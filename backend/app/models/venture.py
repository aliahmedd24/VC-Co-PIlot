from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.kg_entity import KGEntity
    from app.models.workspace import Workspace


class VentureStage(str, PyEnum):
    IDEATION = "ideation"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    GROWTH = "growth"
    EXIT = "exit"


class Venture(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ventures"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(255))
    stage: Mapped[VentureStage] = mapped_column(Enum(VentureStage), default=VentureStage.IDEATION)
    one_liner: Mapped[str | None] = mapped_column(String(500), nullable=True)
    problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="venture")
    entities: Mapped[list["KGEntity"]] = relationship(
        back_populates="venture", cascade="all, delete-orphan"
    )
