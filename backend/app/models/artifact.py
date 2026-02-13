import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.chat import ChatMessage


class ArtifactType(str, enum.Enum):
    LEAN_CANVAS = "lean_canvas"
    RESEARCH_BRIEF = "research_brief"
    PITCH_NARRATIVE = "pitch_narrative"
    DECK_OUTLINE = "deck_outline"
    FINANCIAL_MODEL = "financial_model"
    VALUATION_MEMO = "valuation_memo"
    DATAROOM_STRUCTURE = "dataroom_structure"
    KPI_DASHBOARD = "kpi_dashboard"
    BOARD_MEMO = "board_memo"
    CUSTOM = "custom"


class ArtifactStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    ARCHIVED = "archived"


class Artifact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifacts"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ArtifactStatus] = mapped_column(
        Enum(ArtifactStatus),
        default=ArtifactStatus.DRAFT,
        nullable=False,
    )
    owner_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    assumptions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    versions: Mapped[list["ArtifactVersion"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
        order_by="ArtifactVersion.version",
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )


class ArtifactVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifact_versions"
    __table_args__ = (
        UniqueConstraint("artifact_id", "version", name="uq_artifact_version"),
    )

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    diff: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    artifact: Mapped["Artifact"] = relationship(back_populates="versions")
