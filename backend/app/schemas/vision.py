"""Pydantic schemas for Vision API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VisualContentTypeEnum(str, Enum):
    """Type of visual content extracted from documents."""
    IMAGE = "image"
    CHART = "chart"
    DIAGRAM = "diagram"
    SCREENSHOT = "screenshot"
    SLIDE = "slide"
    TABLE = "table"
    INFOGRAPHIC = "infographic"
    LOGO = "logo"
    OTHER = "other"


class VisionProcessingStatusEnum(str, Enum):
    """Status of vision processing for documents."""
    NOT_STARTED = "not_started"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class VisualProcessingStatusEnum(str, Enum):
    """Status of vision processing for individual visual content."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class VisionAnalysisTypeEnum(str, Enum):
    """Type of vision analysis to perform."""
    GENERAL = "general"
    PITCH_DECK = "pitch_deck"
    CHART = "chart"
    OCR = "ocr"


# --- Visual Content Response Schemas ---


class VisualContentResponse(BaseModel):
    """Schema for visual content API responses."""
    id: str
    document_id: str
    venture_id: str
    page_number: int | None = None
    content_type: VisualContentTypeEnum
    storage_key: str
    thumbnail_key: str | None = None
    processing_status: VisualProcessingStatusEnum
    vision_analysis: dict[str, Any] | None = None
    extracted_data: dict[str, Any] | None = None
    extracted_text: str | None = None
    metadata: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VisualContentListResponse(BaseModel):
    """Schema for listing visual content."""
    visual_content: list[VisualContentResponse]
    total: int
    document_id: str


class VisualContentDownloadResponse(BaseModel):
    """Response with presigned URLs for visual content."""
    image_url: str
    thumbnail_url: str | None = None
    expires_in: int = 3600


# --- Vision Analysis Request/Response Schemas ---


class VisionAnalysisRequest(BaseModel):
    """Request schema for on-demand vision analysis."""
    analysis_type: VisionAnalysisTypeEnum = VisionAnalysisTypeEnum.GENERAL
    custom_prompt: str | None = Field(
        None,
        max_length=2000,
        description="Optional custom prompt for analysis"
    )
    quick_mode: bool = Field(
        False,
        description="Use quick summary mode (faster, less detailed)"
    )


class VisionAnalysisResponse(BaseModel):
    """Response schema for vision analysis result."""
    visual_content_id: str
    page_number: int
    analysis_type: str
    content: str
    extracted_data: dict[str, Any] | None = None
    usage: dict[str, int] | None = None


# --- Vision Status Response Schema ---


class VisionStatusResponse(BaseModel):
    """Response schema for document vision processing status."""
    document_id: str
    vision_processing_status: VisionProcessingStatusEnum
    has_visual_content: bool
    page_count: int | None = None
    vision_metadata: dict[str, Any] | None = None
    visual_content_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    pending_count: int = 0
