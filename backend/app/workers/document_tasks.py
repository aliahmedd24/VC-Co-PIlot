"""Background tasks for document processing."""

import asyncio
from datetime import datetime
from uuid import uuid4

from celery import chain, shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.venture import Venture
from app.services.embeddings import get_embedding_service
from app.services.extraction import extract_text
from app.services.storage import get_storage_service

# Create async engine for worker
worker_engine = create_async_engine(
    str(settings.database_url),
    pool_size=2,
    max_overflow=0,
)
WorkerSessionLocal = async_sessionmaker(
    worker_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _process_document_async(document_id: str) -> None:
    """Async implementation of document processing.

    Steps:
    1. Download document from storage
    2. Extract text based on MIME type
    3. Chunk text with overlap
    4. Generate embeddings
    5. Store chunks in database
    6. Update document status
    """
    async with WorkerSessionLocal() as session:
        try:
            # Get document
            result = await session.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            document.updated_at = datetime.utcnow()
            await session.commit()

            # Get venture for this workspace
            venture_result = await session.execute(
                select(Venture).where(Venture.workspace_id == document.workspace_id)
            )
            venture = venture_result.scalar_one_or_none()

            if not venture:
                raise ValueError(f"No venture found for workspace: {document.workspace_id}")

            # Download from storage
            storage = get_storage_service()
            content = await storage.download_file(document.storage_key)

            # Extract text
            text = extract_text(content, document.mime_type)

            if not text.strip():
                raise ValueError("No text could be extracted from document")

            # Chunk text
            chunks = _chunk_text(text)

            if not chunks:
                raise ValueError("No chunks generated from document")

            # Generate embeddings
            try:
                embedding_service = get_embedding_service()
                texts = [c["text"] for c in chunks]
                embeddings = await embedding_service.embed_batch(texts)
            except Exception:
                # If embedding fails, store chunks without embeddings
                embeddings = [None] * len(chunks)

            # Delete existing chunks (for reprocessing)
            existing_chunks = await session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            for chunk in existing_chunks.scalars():
                await session.delete(chunk)

            # Create new chunks
            for idx, (chunk_data, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
                chunk = DocumentChunk(
                    id=str(uuid4()),
                    document_id=document_id,
                    venture_id=venture.id,
                    content=chunk_data["text"],
                    embedding=embedding,
                    chunk_index=idx,
                    metadata_=chunk_data.get("metadata"),
                )
                session.add(chunk)

            # Update document status
            document.status = DocumentStatus.INDEXED
            document.error_message = None
            document.updated_at = datetime.utcnow()
            await session.commit()

        except Exception as e:
            # Update document with error
            await session.rollback()

            result = await session.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)[:500]
                document.updated_at = datetime.utcnow()
                await session.commit()

            raise


def _chunk_text(
    text: str,
    target_size: int = 512,
    overlap: int = 64,
) -> list[dict]:
    """Chunk text with overlap.

    Args:
        text: Text to chunk.
        target_size: Target chunk size in tokens (approx 4 chars per token).
        overlap: Overlap size in tokens.

    Returns:
        List of chunk dicts with 'text' and 'metadata'.
    """
    char_target = target_size * 4
    char_overlap = overlap * 4

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""
    chunk_start = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) > char_target and current_chunk:
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "metadata": {"start_char": chunk_start},
                }
            )
            overlap_start = max(0, len(current_chunk) - char_overlap)
            current_chunk = current_chunk[overlap_start:] + "\n\n" + para
            chunk_start += overlap_start
        else:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para

    if current_chunk.strip():
        chunks.append(
            {
                "text": current_chunk.strip(),
                "metadata": {"start_char": chunk_start},
            }
        )

    return chunks


@shared_task(bind=True, max_retries=3)
def process_document(self, document_id: str) -> dict:
    """Celery task to process a document.

    Args:
        document_id: ID of the document to process.

    Returns:
        Result dict with status.
    """
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_process_document_async(document_id))
        finally:
            loop.close()

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2**self.request.retries) from e


@shared_task(bind=True, max_retries=3)
def process_document_with_vision(
    self,
    document_id: str,
    enable_vision: bool = True,
    vision_analysis_type: str = "general",
) -> dict:
    """Celery task to process a document with optional vision analysis.

    This task chains text processing and vision processing:
    1. Extract text and create embeddings (standard processing)
    2. If enable_vision=True, trigger vision processing in parallel

    Args:
        document_id: ID of the document to process
        enable_vision: Whether to enable vision processing
        vision_analysis_type: Type of vision analysis ('pitch_deck', 'chart', 'ocr', 'general')

    Returns:
        Result dict with status
    """
    try:
        # Run text processing first
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_process_document_async(document_id))
        finally:
            loop.close()

        # If vision enabled and document is PDF, trigger vision processing
        if enable_vision:
            # Import here to avoid circular dependency
            from app.workers.vision_tasks import process_document_vision

            # Trigger vision processing asynchronously (don't wait for it)
            process_document_vision.apply_async(
                args=[document_id],
                kwargs={"analysis_type": vision_analysis_type},
                countdown=5,  # Wait 5 seconds after text processing
            )

        return {
            "status": "success",
            "document_id": document_id,
            "vision_enabled": enable_vision,
        }

    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2**self.request.retries) from e
