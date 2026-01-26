"""Artifact schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ArtifactTypeEnum(str, Enum):
    """Artifact types matching the database model."""

    LEAN_CANVAS = "lean_canvas"
    RESEARCH_BRIEF = "research_brief"
    PITCH_NARRATIVE = "pitch_narrative"
    DECK_OUTLINE = "deck_outline"
    FINANCIAL_MODEL = "financial_model"
    VALUATION_MEMO = "valuation_memo"
    DATAROOM_STRUCTURE = "dataroom_structure"
    KPI_DASHBOARD = "kpi_dashboard"
    BOARD_MEMO = "board_memo"
    CUSTOM = "custom"


class ArtifactStatusEnum(str, Enum):
    """Artifact status matching the database model."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    ARCHIVED = "archived"


class ExportFormat(str, Enum):
    """Supported export formats."""

    MARKDOWN = "markdown"
    PDF = "pdf"


# Request schemas


class ArtifactCreate(BaseModel):
    """Request schema for creating an artifact."""

    workspace_id: str
    type: ArtifactTypeEnum
    title: str = Field(..., min_length=1, max_length=255)
    owner_agent: str = Field(..., min_length=1, max_length=100)
    content: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[dict[str, Any]] | None = None


class ArtifactUpdate(BaseModel):
    """Request schema for updating an artifact."""

    title: str | None = Field(None, min_length=1, max_length=255)
    status: ArtifactStatusEnum | None = None
    content: dict[str, Any] | None = None
    assumptions: list[dict[str, Any]] | None = None


class ArtifactChatRequest(BaseModel):
    """Request schema for chatting within artifact context."""

    content: str = Field(..., min_length=1)
    session_id: str | None = None


class ArtifactExportRequest(BaseModel):
    """Request schema for exporting an artifact."""

    format: ExportFormat = ExportFormat.MARKDOWN
    include_versions: bool = False


# Response schemas


class ArtifactVersionResponse(BaseModel):
    """Response schema for artifact version."""

    id: str
    version: int
    content: dict[str, Any]
    diff: dict[str, Any] | None = None
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArtifactResponse(BaseModel):
    """Response schema for artifact."""

    id: str
    workspace_id: str
    type: ArtifactTypeEnum
    title: str
    status: ArtifactStatusEnum
    owner_agent: str
    content: dict[str, Any]
    assumptions: list[dict[str, Any]] | None = None
    created_by_id: str | None = None
    created_at: datetime
    updated_at: datetime
    current_version: int = 1
    versions: list[ArtifactVersionResponse] = []

    class Config:
        from_attributes = True


class ArtifactListResponse(BaseModel):
    """Response schema for paginated artifact list."""

    items: list[ArtifactResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ArtifactExportResponse(BaseModel):
    """Response schema for artifact export."""

    artifact_id: str
    format: ExportFormat
    download_url: str | None = None
    task_id: str | None = None
    status: str = "pending"
