import enum
import uuid
from typing import Any

from sqlalchemy import Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class KGEntityType(str, enum.Enum):
    VENTURE = "venture"
    MARKET = "market"
    ICP = "icp"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    TEAM_MEMBER = "team_member"
    METRIC = "metric"
    FUNDING_ASSUMPTION = "funding_assumption"
    RISK = "risk"


class KGEntityStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    SUGGESTED = "suggested"
    PINNED = "pinned"


class KGEntity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_entities"
    __table_args__ = (
        Index("ix_kg_entities_venture_type", "venture_id", "type"),
    )

    venture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ventures.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[KGEntityType] = mapped_column(
        Enum(KGEntityType),
        index=True,
        nullable=False,
    )
    status: Mapped[KGEntityStatus] = mapped_column(
        Enum(KGEntityStatus),
        default=KGEntityStatus.NEEDS_REVIEW,
        nullable=False,
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    evidence: Mapped[list["KGEvidence"]] = relationship(
        back_populates="entity",
        cascade="all, delete-orphan",
    )


class KGEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_evidence"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kg_entities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    entity: Mapped["KGEntity"] = relationship(back_populates="evidence")


class KGRelationType(str, enum.Enum):
    COMPETES_WITH = "competes_with"
    TARGETS = "targets"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    BELONGS_TO = "belongs_to"


class KGRelation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_relations"

    from_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kg_entities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    to_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kg_entities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[KGRelationType] = mapped_column(
        Enum(KGRelationType),
        nullable=False,
    )
    relation_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
