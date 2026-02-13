from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.router.types import RoutingPlan
from app.models.chat import MessageRole


class SendMessageRequest(BaseModel):
    workspace_id: str
    content: str = Field(min_length=1, max_length=10000)
    session_id: str | None = None
    override_agent: str | None = None


class ChatMessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    agent_id: str | None = None
    citations: list[dict[str, Any]] | None = None
    artifact_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageResponse(BaseModel):
    session_id: str
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    routing_plan: RoutingPlan
    proposed_updates: list[dict[str, Any]]
    artifact_id: str | None = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionResponse]
