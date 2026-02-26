from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.artifact import ArtifactStatus, ArtifactType


class ArtifactCreate(BaseModel):
    workspace_id: str
    type: ArtifactType
    title: str = Field(min_length=1, max_length=255)
    content: dict[str, Any] | None = None


class ArtifactUpdate(BaseModel):
    title: str | None = None
    status: ArtifactStatus | None = None
    content: dict[str, Any] | None = None
    expected_version: int


class ArtifactChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class ArtifactExportRequest(BaseModel):
    format: Literal["markdown", "pdf", "pptx", "docx", "xlsx"]


class ArtifactResponse(BaseModel):
    id: str
    type: ArtifactType
    title: str
    status: ArtifactStatus
    owner_agent: str
    content: dict[str, Any]
    current_version: int
    assumptions: list[dict[str, Any]] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactVersionResponse(BaseModel):
    id: str
    version: int
    content: dict[str, Any]
    diff: dict[str, Any] | None = None
    created_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactResponse]


class ArtifactVersionListResponse(BaseModel):
    versions: list[ArtifactVersionResponse]


class ExportTaskResponse(BaseModel):
    task_id: str
    status: str
    download_url: str | None = None
