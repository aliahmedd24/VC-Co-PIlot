"""Background tasks for vision processing.

This module provides Celery tasks for processing visual content:
- PDF to image conversion
- Vision analysis with Claude
- Chart data extraction
- OCR processing
"""

import asyncio
import io
import logging
from datetime import datetime
from uuid import uuid4

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.document import Document, VisionProcessingStatus
from app.models.venture import Venture
from app.models.visual_content import VisualContent, VisualContentType
from app.models.visual_content import VisionProcessingStatus as VisualStatus
from app.services.embeddings import get_embedding_service
from app.services.storage import get_storage_service
from app.services.vision import PDFConverter, VisionAnalyzer, ImageOptimizer

logger = logging.getLogger(__name__)

# Create async engine for worker (reuse from document_tasks pattern)
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


async def _process_document_vision_async(
    document_id: str,
    analysis_type: str = "general",
    max_pages: int | None = None,
) -> None:
    """Async implementation of vision processing for a document.

    Steps:
    1. Download document from storage
    2. Convert PDF to images (or extract embedded images)
    3. Optimize images for vision API
    4. Analyze each image with Claude
    5. Generate embeddings for vision analysis
    6. Store VisualContent records in database
    7. Update document vision processing status

    Args:
        document_id: ID of document to process
        analysis_type: Type of analysis ('pitch_deck', 'chart', 'ocr', 'general')
        max_pages: Maximum number of pages to process (None = all pages)
    """
    async with WorkerSessionLocal() as session:
        try:
            # Get document
            result = await session.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Update vision processing status
            document.vision_processing_status = VisionProcessingStatus.PROCESSING
            document.updated_at = datetime.utcnow()
            await session.commit()

            # Get venture
            venture_result = await session.execute(
                select(Venture).where(Venture.workspace_id == document.workspace_id)
            )
            venture = venture_result.scalar_one_or_none()

            if not venture:
                raise ValueError(f"No venture found for workspace: {document.workspace_id}")

            # Only process PDFs for now
            if "pdf" not in document.mime_type.lower():
                logger.info(f"Skipping vision for non-PDF document: {document.mime_type}")
                document.vision_processing_status = VisionProcessingStatus.SKIPPED
                await session.commit()
                return

            # Download from storage
            storage = get_storage_service()
            pdf_content = await storage.download_file(document.storage_key)

            # Initialize services
            pdf_converter = PDFConverter(dpi=150, image_format="PNG")
            vision_analyzer = VisionAnalyzer()
            image_optimizer = ImageOptimizer(max_dimension=1568, target_file_size_kb=500)

            # Get page count and update document
            page_count = await pdf_converter.get_page_count(io.BytesIO(pdf_content))
            document.page_count = page_count
            document.has_visual_content = True
            await session.commit()

            # Limit pages if specified
            pages_to_process = min(page_count, max_pages) if max_pages else page_count

            # Convert PDF to images
            logger.info(f"Converting {pages_to_process} pages to images for document {document_id}")
            images = await pdf_converter.convert_pdf_to_images(io.BytesIO(pdf_content))

            # Limit to specified pages
            images = images[:pages_to_process]

            # Process each page
            successful_pages = 0
            failed_pages = 0

            for page_num, image_bytes in enumerate(images, start=1):
                try:
                    # Optimize image
                    optimized_image, opt_metadata = await image_optimizer.optimize_image(
                        image_bytes, output_format="PNG"
                    )

                    # Upload to storage
                    image_storage_key = f"vision/{document.workspace_id}/{document_id}/page_{page_num}.png"
                    await storage.upload_file(image_storage_key, optimized_image, "image/png")

                    # Create thumbnail
                    thumbnail_bytes = await image_optimizer.create_thumbnail(
                        optimized_image, size=(300, 300)
                    )
                    thumbnail_key = f"vision/{document.workspace_id}/{document_id}/thumb_page_{page_num}.jpg"
                    await storage.upload_file(thumbnail_key, thumbnail_bytes, "image/jpeg")

                    # Analyze with vision
                    if analysis_type == "pitch_deck":
                        analysis_result = await vision_analyzer.analyze_pitch_deck_slide(
                            optimized_image, slide_number=page_num, media_type="image/png"
                        )
                        content_type = VisualContentType.SLIDE
                    elif analysis_type == "chart":
                        analysis_result = await vision_analyzer.analyze_financial_chart(
                            optimized_image, media_type="image/png"
                        )
                        content_type = VisualContentType.CHART
                    elif analysis_type == "ocr":
                        analysis_result = await vision_analyzer.perform_ocr(
                            optimized_image, structured=True, media_type="image/png"
                        )
                        content_type = VisualContentType.IMAGE
                    else:
                        analysis_result = await vision_analyzer.analyze_general(
                            optimized_image, media_type="image/png"
                        )
                        content_type = VisualContentType.IMAGE

                    # Generate embedding from analysis text
                    try:
                        embedding_service = get_embedding_service()
                        embedding = await embedding_service.embed(analysis_result["content"])
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for page {page_num}: {str(e)}")
                        embedding = None

                    # Create VisualContent record
                    visual_content = VisualContent(
                        id=str(uuid4()),
                        document_id=document_id,
                        venture_id=venture.id,
                        page_number=page_num,
                        content_type=content_type,
                        storage_key=image_storage_key,
                        thumbnail_key=thumbnail_key,
                        processing_status=VisualStatus.COMPLETED,
                        vision_analysis={
                            "content": analysis_result["content"],
                            "usage": analysis_result.get("usage", {}),
                            "analysis_type": analysis_type,
                        },
                        extracted_data={},
                        extracted_text=analysis_result.get("extracted_text"),
                        embedding=embedding,
                        metadata_={
                            "optimization": opt_metadata,
                            "page_number": page_num,
                            "total_pages": page_count,
                        },
                    )
                    session.add(visual_content)

                    successful_pages += 1
                    logger.info(f"Successfully processed page {page_num}/{pages_to_process}")

                except Exception as e:
                    logger.error(f"Failed to process page {page_num}: {str(e)}")
                    failed_pages += 1

                    # Create failed VisualContent record
                    visual_content = VisualContent(
                        id=str(uuid4()),
                        document_id=document_id,
                        venture_id=venture.id,
                        page_number=page_num,
                        content_type=VisualContentType.IMAGE,
                        storage_key="",
                        processing_status=VisualStatus.FAILED,
                        error_message=str(e)[:500],
                        metadata_={"page_number": page_num},
                    )
                    session.add(visual_content)

            # Update document status
            if failed_pages == 0:
                document.vision_processing_status = VisionProcessingStatus.COMPLETED
            elif successful_pages > 0:
                document.vision_processing_status = VisionProcessingStatus.PARTIAL
            else:
                document.vision_processing_status = VisionProcessingStatus.FAILED

            document.vision_metadata = {
                "total_pages": page_count,
                "processed_pages": pages_to_process,
                "successful_pages": successful_pages,
                "failed_pages": failed_pages,
                "analysis_type": analysis_type,
            }
            document.updated_at = datetime.utcnow()
            await session.commit()

            logger.info(
                f"Vision processing complete for document {document_id}: "
                f"{successful_pages} successful, {failed_pages} failed"
            )

        except Exception as e:
            # Update document with error
            await session.rollback()

            result = await session.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if document:
                document.vision_processing_status = VisionProcessingStatus.FAILED
                document.vision_metadata = {"error": str(e)[:500]}
                document.updated_at = datetime.utcnow()
                await session.commit()

            logger.error(f"Vision processing failed for document {document_id}: {str(e)}")
            raise


async def _process_pitch_deck_async(document_id: str, max_slides: int | None = None) -> None:
    """Process a pitch deck with specialized slide analysis.

    Args:
        document_id: ID of the pitch deck document
        max_slides: Maximum number of slides to process
    """
    await _process_document_vision_async(
        document_id=document_id, analysis_type="pitch_deck", max_pages=max_slides
    )


async def _extract_charts_and_analyze_async(document_id: str) -> None:
    """Extract and analyze charts from a document.

    This is a more targeted approach that:
    1. Extracts embedded images from PDF
    2. Filters for chart-like images
    3. Performs detailed chart analysis and data extraction

    Args:
        document_id: ID of the document
    """
    async with WorkerSessionLocal() as session:
        try:
            # Get document
            result = await session.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Get venture
            venture_result = await session.execute(
                select(Venture).where(Venture.workspace_id == document.workspace_id)
            )
            venture = venture_result.scalar_one_or_none()

            if not venture:
                raise ValueError(f"No venture found")

            # Download document
            storage = get_storage_service()
            pdf_content = await storage.download_file(document.storage_key)

            # Extract images
            pdf_converter = PDFConverter()
            embedded_images = await pdf_converter.extract_images_from_pdf(io.BytesIO(pdf_content))

            logger.info(f"Found {len(embedded_images)} embedded images in document {document_id}")

            # Process each image
            vision_analyzer = VisionAnalyzer()
            image_optimizer = ImageOptimizer()

            for idx, (page_num, image_bytes) in enumerate(embedded_images):
                try:
                    # Optimize
                    optimized_image, _ = await image_optimizer.optimize_image(image_bytes)

                    # Analyze as chart
                    analysis = await vision_analyzer.analyze_financial_chart(
                        optimized_image, data_only=False
                    )

                    # Upload
                    storage_key = f"vision/{document.workspace_id}/{document_id}/chart_{idx}.png"
                    await storage.upload_file(storage_key, optimized_image, "image/png")

                    # Generate embedding
                    try:
                        embedding_service = get_embedding_service()
                        embedding = await embedding_service.embed(analysis["content"])
                    except Exception:
                        embedding = None

                    # Store
                    visual_content = VisualContent(
                        id=str(uuid4()),
                        document_id=document_id,
                        venture_id=venture.id,
                        page_number=page_num,
                        content_type=VisualContentType.CHART,
                        storage_key=storage_key,
                        processing_status=VisualStatus.COMPLETED,
                        vision_analysis=analysis,
                        embedding=embedding,
                        metadata_={"extracted_from_pdf": True, "image_index": idx},
                    )
                    session.add(visual_content)

                except Exception as e:
                    logger.error(f"Failed to process chart {idx}: {str(e)}")

            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.error(f"Chart extraction failed for document {document_id}: {str(e)}")
            raise


async def _ocr_document_async(document_id: str) -> None:
    """Perform OCR on a scanned document.

    Args:
        document_id: ID of the document to OCR
    """
    await _process_document_vision_async(document_id=document_id, analysis_type="ocr")


# Celery Tasks


@shared_task(bind=True, max_retries=3)
def process_document_vision(
    self, document_id: str, analysis_type: str = "general", max_pages: int | None = None
) -> dict:
    """Celery task to process a document with vision.

    Args:
        document_id: ID of document to process
        analysis_type: Type of analysis ('pitch_deck', 'chart', 'ocr', 'general')
        max_pages: Maximum pages to process

    Returns:
        Result dict with status
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                _process_document_vision_async(document_id, analysis_type, max_pages)
            )
        finally:
            loop.close()

        return {
            "status": "success",
            "document_id": document_id,
            "analysis_type": analysis_type,
        }

    except Exception as e:
        logger.error(f"Vision task failed: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2**self.request.retries) from e


@shared_task(bind=True, max_retries=2)
def process_pitch_deck(self, document_id: str, max_slides: int | None = None) -> dict:
    """Celery task to process a pitch deck.

    Args:
        document_id: ID of pitch deck document
        max_slides: Maximum slides to process

    Returns:
        Result dict
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_process_pitch_deck_async(document_id, max_slides))
        finally:
            loop.close()

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error(f"Pitch deck processing failed: {str(e)}")
        raise self.retry(exc=e, countdown=2**self.request.retries) from e


@shared_task(bind=True, max_retries=2)
def extract_charts_and_analyze(self, document_id: str) -> dict:
    """Celery task to extract and analyze charts.

    Args:
        document_id: ID of document

    Returns:
        Result dict
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_extract_charts_and_analyze_async(document_id))
        finally:
            loop.close()

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error(f"Chart extraction failed: {str(e)}")
        raise self.retry(exc=e, countdown=2**self.request.retries) from e


@shared_task(bind=True, max_retries=2)
def ocr_document(self, document_id: str) -> dict:
    """Celery task to OCR a document.

    Args:
        document_id: ID of document

    Returns:
        Result dict
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_ocr_document_async(document_id))
        finally:
            loop.close()

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        raise self.retry(exc=e, countdown=2**self.request.retries) from e
