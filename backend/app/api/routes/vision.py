"""Vision API routes for visual content management and analysis."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.dependencies import get_db
from app.models.document import Document, VisionProcessingStatus
from app.models.user import User
from app.models.visual_content import VisualContent
from app.models.visual_content import VisionProcessingStatus as VisualStatus
from app.models.workspace import Workspace
from app.schemas.vision import (
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisionProcessingStatusEnum,
    VisionStatusResponse,
    VisualContentDownloadResponse,
    VisualContentListResponse,
    VisualContentResponse,
    VisualContentTypeEnum,
    VisualProcessingStatusEnum,
)
from app.services.storage import get_storage_service

router = APIRouter(prefix="/vision", tags=["vision"])


# --- Helper Functions ---


async def get_document_with_access(
    document_id: str,
    user: User,
    db: AsyncSession,
) -> Document:
    """Get document and verify user has access via workspace ownership."""
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
            detail="Document not found or access denied",
        )
    return document


async def get_visual_content_with_access(
    visual_id: str,
    user: User,
    db: AsyncSession,
) -> VisualContent:
    """Get visual content and verify user has access."""
    result = await db.execute(
        select(VisualContent)
        .join(Document)
        .join(Workspace)
        .where(
            VisualContent.id == visual_id,
            Workspace.owner_id == user.id,
        )
    )
    visual_content = result.scalar_one_or_none()
    if not visual_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visual content not found or access denied",
        )
    return visual_content


def check_vision_enabled() -> None:
    """Check if vision feature is enabled."""
    if not settings.vision_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vision processing is not enabled",
        )


def format_visual_content_response(vc: VisualContent) -> VisualContentResponse:
    """Format VisualContent model to response schema."""
    return VisualContentResponse(
        id=vc.id,
        document_id=vc.document_id,
        venture_id=vc.venture_id,
        page_number=vc.page_number,
        content_type=VisualContentTypeEnum(vc.content_type.value),
        storage_key=vc.storage_key,
        thumbnail_key=vc.thumbnail_key,
        processing_status=VisualProcessingStatusEnum(vc.processing_status.value),
        vision_analysis=vc.vision_analysis,
        extracted_data=vc.extracted_data,
        extracted_text=vc.extracted_text,
        metadata=vc.metadata_,
        error_message=vc.error_message,
        created_at=vc.created_at,
        updated_at=vc.updated_at,
    )


# --- Endpoints ---


@router.get("/documents/{document_id}/visual-content", response_model=VisualContentListResponse)
async def list_visual_content(
    document_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    page_number: int | None = Query(None, ge=1, description="Filter by page number"),
    content_type: VisualContentTypeEnum | None = Query(None, description="Filter by content type"),
    processing_status: VisualProcessingStatusEnum | None = Query(None, description="Filter by status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisualContentListResponse:
    """List visual content for a document.

    Returns paginated list of visual content items extracted from the document,
    with optional filtering by page number, content type, or processing status.
    """
    # Verify document access
    document = await get_document_with_access(document_id, user, db)

    # Build query
    query = select(VisualContent).where(VisualContent.document_id == document.id)

    if page_number is not None:
        query = query.where(VisualContent.page_number == page_number)
    if content_type is not None:
        query = query.where(VisualContent.content_type == content_type.value)
    if processing_status is not None:
        query = query.where(VisualContent.processing_status == processing_status.value)

    query = query.order_by(VisualContent.page_number.asc()).offset(skip).limit(limit)

    result = await db.execute(query)
    visual_contents = result.scalars().all()

    # Get total count
    count_query = select(func.count(VisualContent.id)).where(
        VisualContent.document_id == document.id
    )
    if page_number is not None:
        count_query = count_query.where(VisualContent.page_number == page_number)
    if content_type is not None:
        count_query = count_query.where(VisualContent.content_type == content_type.value)
    if processing_status is not None:
        count_query = count_query.where(VisualContent.processing_status == processing_status.value)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return VisualContentListResponse(
        visual_content=[format_visual_content_response(vc) for vc in visual_contents],
        total=total,
        document_id=document_id,
    )


@router.get("/visual-content/{visual_id}", response_model=VisualContentResponse)
async def get_visual_content(
    visual_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisualContentResponse:
    """Get specific visual content by ID.

    Returns detailed information about a single visual content item,
    including analysis results and extracted data.
    """
    visual_content = await get_visual_content_with_access(visual_id, user, db)
    return format_visual_content_response(visual_content)


@router.get("/visual-content/{visual_id}/download", response_model=VisualContentDownloadResponse)
async def get_visual_content_urls(
    visual_id: str,
    expires_in: int = Query(3600, ge=60, le=86400),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisualContentDownloadResponse:
    """Get presigned download URLs for visual content.

    Returns presigned URLs for both the full image and thumbnail (if available).
    """
    visual_content = await get_visual_content_with_access(visual_id, user, db)

    storage = get_storage_service()

    image_url = storage.generate_presigned_url(visual_content.storage_key, expires_in)
    thumbnail_url = None
    if visual_content.thumbnail_key:
        thumbnail_url = storage.generate_presigned_url(visual_content.thumbnail_key, expires_in)

    return VisualContentDownloadResponse(
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        expires_in=expires_in,
    )


@router.post(
    "/documents/{document_id}/analyze-slide/{page_number}",
    response_model=VisionAnalysisResponse,
)
async def analyze_slide_on_demand(
    document_id: str,
    page_number: int,
    request: VisionAnalysisRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisionAnalysisResponse:
    """Perform on-demand vision analysis on a specific slide/page.

    This endpoint allows re-analyzing or analyzing a specific page with
    different analysis types or custom prompts. Useful for:
    - Re-analyzing with different parameters
    - Custom analysis prompts
    - Analyzing pages that were skipped initially
    """
    check_vision_enabled()

    # Verify document access
    document = await get_document_with_access(document_id, user, db)

    # Validate page number
    if document.page_count and page_number > document.page_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page number {page_number} exceeds document page count ({document.page_count})",
        )

    # Check if visual content exists for this page
    result = await db.execute(
        select(VisualContent).where(
            VisualContent.document_id == document_id,
            VisualContent.page_number == page_number,
        )
    )
    visual_content = result.scalar_one_or_none()

    if not visual_content or not visual_content.storage_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No visual content found for page {page_number}. "
            "Ensure vision processing has been run on this document.",
        )

    # Download image from storage
    storage = get_storage_service()
    try:
        image_bytes = await storage.download_file(visual_content.storage_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve image: {str(e)}",
        )

    # Perform analysis
    from app.services.vision import VisionAnalyzer

    analyzer = VisionAnalyzer()

    try:
        if request.analysis_type.value == "pitch_deck":
            analysis_result = await analyzer.analyze_pitch_deck_slide(
                image_bytes,
                slide_number=page_number,
                quick_mode=request.quick_mode,
            )
        elif request.analysis_type.value == "chart":
            analysis_result = await analyzer.analyze_financial_chart(image_bytes)
        elif request.analysis_type.value == "ocr":
            analysis_result = await analyzer.perform_ocr(image_bytes, structured=True)
        else:
            analysis_result = await analyzer.analyze_general(
                image_bytes,
                custom_prompt=request.custom_prompt,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision analysis failed: {str(e)}",
        )

    # Update visual content with new analysis
    visual_content.vision_analysis = {
        "content": analysis_result.get("content", ""),
        "usage": analysis_result.get("usage", {}),
        "analysis_type": request.analysis_type.value,
        "custom_prompt": request.custom_prompt,
    }
    visual_content.processing_status = VisualStatus.COMPLETED
    visual_content.updated_at = datetime.utcnow()
    await db.commit()

    return VisionAnalysisResponse(
        visual_content_id=visual_content.id,
        page_number=page_number,
        analysis_type=request.analysis_type.value,
        content=analysis_result.get("content", ""),
        extracted_data=analysis_result.get("extracted_data"),
        usage=analysis_result.get("usage"),
    )


@router.get("/documents/{document_id}/vision-status", response_model=VisionStatusResponse)
async def get_vision_status(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisionStatusResponse:
    """Get vision processing status for a document.

    Returns comprehensive status information including:
    - Overall processing status
    - Page count
    - Counts by processing status (completed, failed, pending)
    - Vision metadata
    """
    document = await get_document_with_access(document_id, user, db)

    # Get visual content counts by status
    count_result = await db.execute(
        select(
            func.count(VisualContent.id).label("total"),
            func.count(VisualContent.id).filter(
                VisualContent.processing_status == VisualStatus.COMPLETED
            ).label("completed"),
            func.count(VisualContent.id).filter(
                VisualContent.processing_status == VisualStatus.FAILED
            ).label("failed"),
            func.count(VisualContent.id).filter(
                VisualContent.processing_status == VisualStatus.PENDING
            ).label("pending"),
        ).where(VisualContent.document_id == document_id)
    )
    counts = count_result.one()

    return VisionStatusResponse(
        document_id=document_id,
        vision_processing_status=VisionProcessingStatusEnum(
            document.vision_processing_status.value
        ),
        has_visual_content=document.has_visual_content,
        page_count=document.page_count,
        vision_metadata=document.vision_metadata,
        visual_content_count=counts.total or 0,
        completed_count=counts.completed or 0,
        failed_count=counts.failed or 0,
        pending_count=counts.pending or 0,
    )


@router.post("/documents/{document_id}/trigger-vision", response_model=VisionStatusResponse)
async def trigger_vision_processing(
    document_id: str,
    analysis_type: str = Query("general", pattern="^(general|pitch_deck|chart|ocr)$"),
    max_pages: int | None = Query(None, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisionStatusResponse:
    """Trigger vision processing for a document.

    Starts or re-starts vision processing for a document. Useful for:
    - Documents uploaded without vision enabled
    - Re-processing with different analysis type
    - Processing documents where vision initially failed
    """
    check_vision_enabled()

    document = await get_document_with_access(document_id, user, db)

    # Don't allow re-triggering if already processing
    if document.vision_processing_status == VisionProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vision processing is already in progress for this document",
        )

    # Update status to pending
    document.vision_processing_status = VisionProcessingStatus.PENDING
    document.updated_at = datetime.utcnow()
    await db.commit()

    # Queue background task
    try:
        from app.workers.vision_tasks import process_document_vision

        process_document_vision.delay(document_id, analysis_type, max_pages)
    except Exception as e:
        # Revert status if task queueing fails
        document.vision_processing_status = VisionProcessingStatus.FAILED
        document.vision_metadata = {"error": f"Failed to queue task: {str(e)}"}
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue vision processing: {str(e)}",
        )

    # Get counts
    count_result = await db.execute(
        select(func.count(VisualContent.id)).where(
            VisualContent.document_id == document_id
        )
    )
    total_count = count_result.scalar() or 0

    return VisionStatusResponse(
        document_id=document_id,
        vision_processing_status=VisionProcessingStatusEnum.PENDING,
        has_visual_content=document.has_visual_content,
        page_count=document.page_count,
        vision_metadata=document.vision_metadata,
        visual_content_count=total_count,
        completed_count=0,
        failed_count=0,
        pending_count=0,
    )


@router.delete("/documents/{document_id}/visual-content", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_visual_content(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all visual content for a document.

    Removes all visual content records and resets vision processing status.
    Storage files are also deleted.
    """
    document = await get_document_with_access(document_id, user, db)

    # Don't allow deletion if currently processing
    if document.vision_processing_status == VisionProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete while vision processing is in progress",
        )

    # Get all visual content for cleanup
    result = await db.execute(
        select(VisualContent).where(VisualContent.document_id == document_id)
    )
    visual_contents = result.scalars().all()

    # Delete from storage
    storage = get_storage_service()
    for vc in visual_contents:
        try:
            if vc.storage_key:
                await storage.delete_file(vc.storage_key)
            if vc.thumbnail_key:
                await storage.delete_file(vc.thumbnail_key)
        except Exception:
            pass  # Ignore storage errors during cleanup

    # Delete records
    for vc in visual_contents:
        await db.delete(vc)

    # Reset document vision status
    document.vision_processing_status = VisionProcessingStatus.NOT_STARTED
    document.has_visual_content = False
    document.vision_metadata = None
    document.updated_at = datetime.utcnow()

    await db.commit()
