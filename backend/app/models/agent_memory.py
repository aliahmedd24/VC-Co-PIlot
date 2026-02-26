"""SQLAlchemy model for cross-session agent memory."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import DateTime, Enum, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MemoryType(str, enum.Enum):
    """Type of memory entry."""

    INSIGHT = "insight"
    PREFERENCE = "preference"
    CONTEXT = "context"


class AgentMemory(Base):
    """Persistent cross-session agent memory entry.

    Stores insights discovered by agents, user preferences,
    and contextual information that persists across conversations.
    """

    __tablename__ = "agent_memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ownership
    venture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    agent_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # Memory content
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

    # Timestamps
    created_at: Mapped[uuid.UUID] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[uuid.UUID] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_agent_memories_venture_type",
            "venture_id",
            "memory_type",
        ),
        Index(
            "ix_agent_memories_venture_key",
            "venture_id",
            "key",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AgentMemory(id={self.id}, type={self.memory_type}, "
            f"key={self.key!r})>"
        )
