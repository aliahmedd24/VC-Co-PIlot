from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.visual_content import VisualContent


# Use JSONB on PostgreSQL, generic JSON on others (SQLite)
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class DocumentType(str, PyEnum):
    PITCH_DECK = "pitch_deck"
    FINANCIAL_MODEL = "financial_model"
    BUSINESS_PLAN = "business_plan"
    PRODUCT_DOC = "product_doc"
    OTHER = "other"


class DocumentStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class VisionProcessingStatus(str, PyEnum):
    """Status of vision processing for documents with visual content."""
    NOT_STARTED = "not_started"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some pages succeeded, some failed
    FAILED = "failed"
    SKIPPED = "skipped"  # Vision disabled or not applicable


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False), default=DocumentType.OTHER
    )
    mime_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500))
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.PENDING
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON_TYPE, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vision processing fields
    has_visual_content: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vision_processing_status: Mapped[VisionProcessingStatus] = mapped_column(
        Enum(VisionProcessingStatus, native_enum=False),
        default=VisionProcessingStatus.NOT_STARTED
    )
    vision_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON_TYPE, nullable=True
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    visual_content: Mapped[list["VisualContent"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    venture_id: Mapped[str] = mapped_column(
        ForeignKey("ventures.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    # Use generic JSON for vector embedding on SQLite, Vector on Postgres
    embedding: Mapped[list[float] | None] = mapped_column(
        JSON().with_variant(Vector(1536), "postgresql"), nullable=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON_TYPE, nullable=True
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index(
            "ix_chunks_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
