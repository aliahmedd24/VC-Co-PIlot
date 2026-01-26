from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.chat import ChatMessage
    from app.models.workspace import Workspace


class ArtifactType(str, PyEnum):
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


class ArtifactStatus(str, PyEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    ARCHIVED = "archived"


class Artifact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifacts"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType))
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[ArtifactStatus] = mapped_column(
        Enum(ArtifactStatus), default=ArtifactStatus.DRAFT
    )
    owner_agent: Mapped[str] = mapped_column(String(100))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    assumptions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="artifacts")
    versions: Mapped[list["ArtifactVersion"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
        order_by="ArtifactVersion.version.desc()",
    )
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="artifact")


class ArtifactVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifact_versions"

    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    diff: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    artifact: Mapped["Artifact"] = relationship(back_populates="versions")
