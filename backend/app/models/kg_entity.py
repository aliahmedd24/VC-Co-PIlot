from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.venture import Venture


class KGEntityType(str, PyEnum):
    VENTURE = "venture"
    MARKET = "market"
    ICP = "icp"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    TEAM_MEMBER = "team_member"
    METRIC = "metric"
    FUNDING_ASSUMPTION = "funding_assumption"
    RISK = "risk"


class KGEntityStatus(str, PyEnum):
    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    SUGGESTED = "suggested"
    PINNED = "pinned"


class KGEntity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_entities"

    venture_id: Mapped[str] = mapped_column(
        ForeignKey("ventures.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[KGEntityType] = mapped_column(Enum(KGEntityType), index=True)
    status: Mapped[KGEntityStatus] = mapped_column(
        Enum(KGEntityStatus), default=KGEntityStatus.NEEDS_REVIEW
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    venture: Mapped["Venture"] = relationship(back_populates="entities")
    evidence: Mapped[list["KGEvidence"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )


class KGEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_evidence"

    entity_id: Mapped[str] = mapped_column(
        ForeignKey("kg_entities.id", ondelete="CASCADE"), index=True
    )
    snippet: Mapped[str] = mapped_column(Text)
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(50))
    agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    entity: Mapped["KGEntity"] = relationship(back_populates="evidence")


class KGRelation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_relations"

    from_entity_id: Mapped[str] = mapped_column(
        ForeignKey("kg_entities.id", ondelete="CASCADE"), index=True
    )
    to_entity_id: Mapped[str] = mapped_column(
        ForeignKey("kg_entities.id", ondelete="CASCADE"), index=True
    )
    relation_type: Mapped[str] = mapped_column(String(100))
    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class KGEventType(str, PyEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ADD_EVIDENCE = "add_evidence"
    ADD_RELATION = "add_relation"


class KGEvent(Base, UUIDMixin, TimestampMixin):
    """Event sourcing model for KG mutations."""

    __tablename__ = "kg_events"

    venture_id: Mapped[str] = mapped_column(
        ForeignKey("ventures.id", ondelete="CASCADE"), index=True
    )
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    event_type: Mapped[KGEventType] = mapped_column(Enum(KGEventType))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
