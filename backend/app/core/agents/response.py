"""Response schemas for agent outputs."""

from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A citation from the knowledge base."""

    chunk_id: str
    document_id: str
    snippet: str
    score: float = Field(ge=0.0, le=1.0)


class SuggestedEntity(BaseModel):
    """An entity suggested by the agent for KG update."""

    type: str
    data: dict[str, Any]
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str | None = None


class AgentResponse(BaseModel):
    """Standard response from an agent."""

    content: str
    agent_id: str
    citations: list[Citation] = Field(default_factory=list)
    suggested_entities: list[SuggestedEntity] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    routing_plan: dict[str, Any] | None = None

    class Config:
        from_attributes = True
