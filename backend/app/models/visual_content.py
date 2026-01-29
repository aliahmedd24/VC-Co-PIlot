"""Visual content model for storing and analyzing images extracted from documents.

This model supports Claude's vision capabilities for pitch deck analysis,
chart interpretation, OCR, and visual content understanding.
"""

from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.venture import Venture


# Use JSONB on PostgreSQL, generic JSON on others (SQLite)
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class VisualContentType(str, PyEnum):
    """Type of visual content extracted from documents."""
    IMAGE = "image"
    CHART = "chart"
    DIAGRAM = "diagram"
    SCREENSHOT = "screenshot"
    SLIDE = "slide"
    TABLE = "table"
    INFOGRAPHIC = "infographic"
    LOGO = "logo"
    OTHER = "other"


class VisionProcessingStatus(str, PyEnum):
    """Status of vision processing for visual content."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class VisualContent(Base, UUIDMixin, TimestampMixin):
    """Visual content extracted from documents with vision analysis.

    This model stores images extracted from PDFs, screenshots, and other
    visual content along with Claude's vision analysis results.

    Key capabilities:
    - Pitch deck slide analysis (design quality, content gaps, metrics)
    - Chart interpretation (extract structured data from graphs)
    - OCR for scanned documents
    - Competitive analysis (product screenshots, UI analysis)
    - Multi-modal RAG (searchable via embeddings)
    """
    __tablename__ = "visual_content"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    venture_id: Mapped[str] = mapped_column(
        ForeignKey("ventures.id", ondelete="CASCADE"), index=True
    )

    # Content identification
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[VisualContentType] = mapped_column(
        Enum(VisualContentType, native_enum=False), default=VisualContentType.IMAGE
    )

    # Storage
    storage_key: Mapped[str] = mapped_column(String(500))
    thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Vision processing
    processing_status: Mapped[VisionProcessingStatus] = mapped_column(
        Enum(VisionProcessingStatus, native_enum=False),
        default=VisionProcessingStatus.PENDING
    )
    vision_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        JSON_TYPE, nullable=True
    )
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON_TYPE, nullable=True
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Multi-modal RAG support
    embedding: Mapped[list[float] | None] = mapped_column(
        JSON().with_variant(Vector(1536), "postgresql"), nullable=True
    )

    # Image metadata
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON_TYPE, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="visual_content")

    __table_args__ = (
        Index(
            "ix_visual_content_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_visual_content_document_page", document_id, page_number),
        Index("ix_visual_content_venture_type", venture_id, content_type),
    )
