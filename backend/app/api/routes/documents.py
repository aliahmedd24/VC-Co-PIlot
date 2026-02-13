import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.dependencies import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.storage_service import storage_service

logger = structlog.get_logger()
router = APIRouter(prefix="/documents", tags=["documents"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
}


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    # Verify workspace access
    workspace = await _verify_workspace_access(workspace_id, current_user, db)

    # Validate MIME type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' is not supported",
        )

    # Read and validate size
    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    # Upload to S3
    storage_key = storage_service.upload_file(file_data, content_type)

    # Create DB record
    document = Document(
        workspace_id=workspace.id,
        name=file.filename or "untitled",
        type=DocumentType.OTHER,
        mime_type=content_type,
        size=len(file_data),
        storage_key=storage_key,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.flush()

    # Enqueue processing task
    try:
        from app.workers.document_tasks import process_document

        process_document.delay(str(document.id))
        logger.info("document_processing_enqueued", document_id=str(document.id))
    except Exception:
        logger.warning("celery_enqueue_failed", document_id=str(document.id))

    return DocumentResponse(
        id=str(document.id),
        name=document.name,
        type=document.type,
        status=document.status,
        mime_type=document.mime_type,
        size=document.size,
        created_at=document.created_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    # Verify workspace access
    await _verify_workspace_access(workspace_id, current_user, db)

    result = await db.execute(
        select(Document)
        .where(Document.workspace_id == workspace_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.workspace_id == workspace_id)
    )
    total = count_result.scalar_one()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=str(doc.id),
                name=doc.name,
                type=doc.type,
                status=doc.status,
                mime_type=doc.mime_type,
                size=doc.size,
                created_at=doc.created_at,
            )
            for doc in documents
        ],
        total=total,
    )


async def _verify_workspace_access(
    workspace_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Workspace:
    from app.models.workspace import WorkspaceMembership

    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMembership)
        .where(
            Workspace.id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace
