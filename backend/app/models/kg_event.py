import enum
import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class KGEventType(str, enum.Enum):
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    ENTITY_CONFIRMED = "entity_confirmed"
    RELATION_CREATED = "relation_created"
    CONFLICT_DETECTED = "conflict_detected"


class KGEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_events"
    __table_args__ = (
        Index("ix_kg_events_venture_created", "venture_id", "created_at"),
    )

    venture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ventures.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[KGEventType] = mapped_column(
        Enum(KGEventType),
        nullable=False,
    )
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
