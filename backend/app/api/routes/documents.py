"""Document API routes for upload and management."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.dependencies import get_db
from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentType
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.documents import (
    ChunkResponse,
    DocumentChunksResponse,
    DocumentDownloadResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentTypeEnum,
    DocumentUploadResponse,
)
from app.services.extraction import SUPPORTED_MIME_TYPES, is_supported_mime_type
from app.services.storage import get_storage_service

router = APIRouter(prefix="/documents", tags=["documents"])

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


# --- Helper Functions ---


async def get_workspace_or_404(
    workspace_id: str,
    user: User,
    db: AsyncSession,
) -> Workspace:
    """Get workspace and verify access."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_id == user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


async def get_document_or_404(
    document_id: str,
    user: User,
    db: AsyncSession,
) -> Document:
    """Get document and verify access."""
    result = await db.execute(
        select(Document)
        .join(Workspace)
        .where(
            Document.id == document_id,
            Workspace.owner_id == user.id,
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


def format_document_response(document: Document, chunk_count: int = 0) -> DocumentResponse:
    """Format document model to response schema."""
    return DocumentResponse(
        id=document.id,
        workspace_id=document.workspace_id,
        name=document.name,
        type=DocumentTypeEnum(document.type.value),
        mime_type=document.mime_type,
        size=document.size,
        status=document.status.value,
        error_message=document.error_message,
        created_at=document.created_at,
        updated_at=document.updated_at,
        chunk_count=chunk_count,
    )


# --- Upload Endpoint ---


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    document_type: DocumentTypeEnum = Form(DocumentTypeEnum.OTHER),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload a document for processing.

    The document will be stored in S3/MinIO and queued for background
    processing (text extraction, chunking, and embedding).
    """
    # Verify workspace access
    await get_workspace_or_404(workspace_id, user, db)

    # Validate file type
    content_type = file.content_type or "application/octet-stream"
    if not is_supported_mime_type(content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}. Supported: {SUPPORTED_MIME_TYPES}",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded",
        )

    # Generate storage key
    doc_id = str(uuid4())
    file_ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
    storage_key = f"workspaces/{workspace_id}/documents/{doc_id}.{file_ext}"

    # Upload to storage
    storage = get_storage_service()
    await storage.upload_bytes(content, storage_key, content_type)

    # Create document record
    document = Document(
        id=doc_id,
        workspace_id=workspace_id,
        name=file.filename or "untitled",
        type=DocumentType(document_type.value),
        mime_type=content_type,
        size=file_size,
        storage_key=storage_key,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Queue background processing task
    try:
        from app.workers.document_tasks import process_document

        process_document.delay(document.id)
    except Exception:
        # If Celery not available, update status
        pass

    return DocumentUploadResponse(
        document=format_document_response(document),
        message="Document uploaded successfully. Processing started.",
    )


# --- CRUD Endpoints ---


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    workspace_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: DocumentStatus | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List documents in a workspace."""
    await get_workspace_or_404(workspace_id, user, db)

    # Build query
    query = select(Document).where(Document.workspace_id == workspace_id)

    if status_filter:
        query = query.where(Document.status == status_filter)

    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    documents = result.scalars().all()

    # Get total count
    count_query = select(func.count(Document.id)).where(Document.workspace_id == workspace_id)
    if status_filter:
        count_query = count_query.where(Document.status == status_filter)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get chunk counts
    doc_responses = []
    for doc in documents:
        chunk_count_result = await db.execute(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == doc.id)
        )
        chunk_count = chunk_count_result.scalar() or 0
        doc_responses.append(format_document_response(doc, chunk_count))

    return DocumentListResponse(documents=doc_responses, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a document by ID."""
    document = await get_document_or_404(document_id, user, db)

    chunk_count_result = await db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document.id)
    )
    chunk_count = chunk_count_result.scalar() or 0

    return format_document_response(document, chunk_count)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document and its chunks."""
    document = await get_document_or_404(document_id, user, db)

    # Delete from storage
    try:
        storage = get_storage_service()
        await storage.delete_file(document.storage_key)
    except Exception:
        pass  # Ignore storage errors

    # Delete from database (cascades to chunks)
    await db.delete(document)
    await db.commit()


@router.get("/{document_id}/download", response_model=DocumentDownloadResponse)
async def get_download_url(
    document_id: str,
    expires_in: int = Query(3600, ge=60, le=86400),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDownloadResponse:
    """Get a presigned download URL for a document."""
    document = await get_document_or_404(document_id, user, db)

    storage = get_storage_service()
    url = storage.generate_presigned_url(document.storage_key, expires_in)

    return DocumentDownloadResponse(url=url, expires_in=expires_in)


@router.get("/{document_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(
    document_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentChunksResponse:
    """Get chunks for a document."""
    document = await get_document_or_404(document_id, user, db)

    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index)
        .offset(skip)
        .limit(limit)
    )
    chunks = result.scalars().all()

    count_result = await db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document.id)
    )
    total = count_result.scalar() or 0

    chunk_responses = [
        ChunkResponse(
            id=chunk.id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            metadata=chunk.metadata_,
        )
        for chunk in chunks
    ]

    return DocumentChunksResponse(
        document_id=document.id,
        chunks=chunk_responses,
        total=total,
    )


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Reprocess a failed document."""
    document = await get_document_or_404(document_id, user, db)

    if document.status not in (DocumentStatus.FAILED, DocumentStatus.INDEXED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only reprocess failed or indexed documents",
        )

    # Delete existing chunks
    await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))

    # Reset status
    document.status = DocumentStatus.PENDING
    document.error_message = None
    document.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(document)

    # Queue processing
    try:
        from app.workers.document_tasks import process_document

        process_document.delay(document.id)
    except Exception:
        pass

    return format_document_response(document)
