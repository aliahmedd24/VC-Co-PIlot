from datetime import datetime

from pydantic import BaseModel, Field

from app.models.venture import VentureStage
from app.models.workspace import WorkspaceRole


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class VentureResponse(BaseModel):
    id: str
    name: str
    stage: VentureStage
    one_liner: str | None
    problem: str | None
    solution: str | None

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    role: WorkspaceRole
    venture: VentureResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VentureUpdate(BaseModel):
    name: str | None = None
    stage: VentureStage | None = None
    one_liner: str | None = Field(None, max_length=500)
    problem: str | None = None
    solution: str | None = None
