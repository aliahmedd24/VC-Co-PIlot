"""Pydantic schemas for Chat API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message roles in a chat."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# --- Session Schemas ---


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""

    title: str | None = Field(None, max_length=255)
    venture_id: str | None = None


class ChatSessionResponse(BaseModel):
    """Schema for chat session responses."""

    id: str
    workspace_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """Schema for listing chat sessions."""

    sessions: list[ChatSessionResponse]
    total: int


# --- Message Schemas ---


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""

    content: str = Field(..., min_length=1, max_length=10000)
    agent_override: str | None = None  # Force specific agent


class CitationResponse(BaseModel):
    """Schema for citation in a message."""

    chunk_id: str
    document_id: str
    snippet: str
    score: float


class ChatMessageResponse(BaseModel):
    """Schema for chat message responses."""

    id: str
    session_id: str
    role: MessageRole
    content: str
    agent_id: str | None = None
    citations: list[CitationResponse] = Field(default_factory=list)
    routing_plan: dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageListResponse(BaseModel):
    """Schema for listing chat messages."""

    messages: list[ChatMessageResponse]
    total: int


# --- Streaming Schemas ---


class StreamChunkType(str, Enum):
    """Types of stream chunks."""

    CONTENT = "content"
    CITATION = "citation"
    ROUTING = "routing"
    DONE = "done"
    ERROR = "error"


class StreamChunk(BaseModel):
    """Schema for SSE stream chunks."""

    type: StreamChunkType
    data: str | dict[str, Any]


# --- Send Message Response ---


class SendMessageResponse(BaseModel):
    """Response after sending a message."""

    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
