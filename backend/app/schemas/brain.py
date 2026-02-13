from typing import Any

from pydantic import BaseModel, Field

from app.models.kg_entity import KGEntityStatus, KGEntityType
from app.schemas.workspace import VentureResponse


class BrainSearchRequest(BaseModel):
    workspace_id: str
    query: str
    entity_types: list[KGEntityType] | None = None
    max_chunks: int = Field(default=10, ge=1, le=50)


class ChunkResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    similarity: float
    freshness_weight: float
    final_score: float


class EntityResult(BaseModel):
    id: str
    type: KGEntityType
    status: KGEntityStatus
    data: dict[str, Any]
    confidence: float
    evidence_count: int

    model_config = {"from_attributes": True}


class BrainSearchResponse(BaseModel):
    chunks: list[ChunkResult]
    entities: list[EntityResult]
    citations: list[dict[str, Any]]


class EntityCreate(BaseModel):
    venture_id: str
    type: KGEntityType
    data: dict[str, Any]
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class EntityUpdate(BaseModel):
    data: dict[str, Any] | None = None
    status: KGEntityStatus | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class VentureProfileResponse(BaseModel):
    venture: VentureResponse
    entities_by_type: dict[str, list[EntityResult]]
    total_documents: int
    total_entities: int
