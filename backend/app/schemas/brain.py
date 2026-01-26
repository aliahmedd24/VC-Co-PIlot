"""Pydantic schemas for Brain API endpoints."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class KGEntityTypeEnum(str, Enum):
    """Entity types for the Knowledge Graph."""

    VENTURE = "venture"
    MARKET = "market"
    ICP = "icp"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    TEAM_MEMBER = "team_member"
    METRIC = "metric"
    FUNDING_ASSUMPTION = "funding_assumption"
    RISK = "risk"


class KGEntityStatusEnum(str, Enum):
    """Entity statuses."""

    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    SUGGESTED = "suggested"
    PINNED = "pinned"


# --- Entity Schemas ---


class EntityCreate(BaseModel):
    """Schema for creating a KG entity."""

    type: KGEntityTypeEnum
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    status: KGEntityStatusEnum | None = None


class EntityUpdate(BaseModel):
    """Schema for updating a KG entity."""

    data: dict[str, Any] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: KGEntityStatusEnum | None = None


class EvidenceResponse(BaseModel):
    """Schema for evidence attached to an entity."""

    id: str
    snippet: str
    source_type: str
    document_id: str | None = None
    agent_id: str | None = None


class EntityResponse(BaseModel):
    """Schema for entity API responses."""

    id: str
    type: KGEntityTypeEnum
    status: KGEntityStatusEnum
    data: dict[str, Any]
    confidence: float
    evidence: list[EvidenceResponse] = Field(default_factory=list)
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# --- Venture Profile Schemas ---


class VentureInfo(BaseModel):
    """Basic venture information."""

    id: str
    name: str
    stage: str
    one_liner: str | None = None
    problem: str | None = None
    solution: str | None = None


class VentureProfileResponse(BaseModel):
    """Full venture profile including entities."""

    venture: VentureInfo | None = None
    entities: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    metrics: dict[str, Any] | None = None


# --- Search Schemas ---


class BrainSearchRequest(BaseModel):
    """Schema for brain search requests."""

    query: str = Field(..., min_length=1, max_length=1000)
    max_chunks: int = Field(default=10, ge=1, le=50)
    entity_types: list[KGEntityTypeEnum] | None = None
    include_relations: bool = True


class ChunkResult(BaseModel):
    """A document chunk from RAG search."""

    chunk_id: str
    document_id: str
    snippet: str
    score: float


class BrainSearchResponse(BaseModel):
    """Schema for brain search responses."""

    entities: list[EntityResponse] = Field(default_factory=list)
    citations: list[ChunkResult] = Field(default_factory=list)


# --- Proposal Schemas ---


class EntityProposal(BaseModel):
    """A proposed entity update from an agent."""

    type: KGEntityTypeEnum
    data: dict[str, Any]
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ProposeUpdatesRequest(BaseModel):
    """Request to propose KG updates."""

    entities: list[EntityProposal]
    agent_id: str | None = None


class ProposeUpdatesResponse(BaseModel):
    """Response with created entities."""

    created: list[EntityResponse]
    conflicts_detected: int = 0
