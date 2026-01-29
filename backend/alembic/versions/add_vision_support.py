"""add vision support

Revision ID: add_vision_support
Revises: 685016100768
Create Date: 2026-01-29 00:00:00.000000

"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_vision_support"
down_revision: str | None = "685016100768"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add vision-related columns to documents table
    op.add_column(
        "documents",
        sa.Column("has_visual_content", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "vision_processing_status",
            sa.Enum(
                "NOT_STARTED",
                "PENDING",
                "PROCESSING",
                "COMPLETED",
                "PARTIAL",
                "FAILED",
                "SKIPPED",
                name="visionprocessingstatus",
            ),
            nullable=False,
            server_default="NOT_STARTED",
        ),
    )
    op.add_column(
        "documents",
        sa.Column("vision_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Create visual_content table
    op.create_table(
        "visual_content",
        sa.Column("document_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("venture_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column(
            "content_type",
            sa.Enum(
                "IMAGE",
                "CHART",
                "DIAGRAM",
                "SCREENSHOT",
                "SLIDE",
                "TABLE",
                "INFOGRAPHIC",
                "LOGO",
                "OTHER",
                name="visualcontenttype",
            ),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_key", sa.String(length=500), nullable=True),
        sa.Column(
            "processing_status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "SKIPPED",
                name="visualprocessingstatus",
            ),
            nullable=False,
        ),
        sa.Column("vision_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(dim=1536), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venture_id"], ["ventures.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for visual_content
    op.create_index(
        op.f("ix_visual_content_document_id"), "visual_content", ["document_id"], unique=False
    )
    op.create_index(
        op.f("ix_visual_content_venture_id"), "visual_content", ["venture_id"], unique=False
    )
    op.create_index(
        "ix_visual_content_document_page",
        "visual_content",
        ["document_id", "page_number"],
        unique=False,
    )
    op.create_index(
        "ix_visual_content_venture_type",
        "visual_content",
        ["venture_id", "content_type"],
        unique=False,
    )
    op.create_index(
        "ix_visual_content_embedding_hnsw",
        "visual_content",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    # Drop visual_content table and indexes
    op.drop_index(
        "ix_visual_content_embedding_hnsw",
        table_name="visual_content",
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.drop_index("ix_visual_content_venture_type", table_name="visual_content")
    op.drop_index("ix_visual_content_document_page", table_name="visual_content")
    op.drop_index(op.f("ix_visual_content_venture_id"), table_name="visual_content")
    op.drop_index(op.f("ix_visual_content_document_id"), table_name="visual_content")
    op.drop_table("visual_content")

    # Remove vision columns from documents table
    op.drop_column("documents", "vision_metadata")
    op.drop_column("documents", "vision_processing_status")
    op.drop_column("documents", "page_count")
    op.drop_column("documents", "has_visual_content")

    # Drop enums
    sa.Enum(name="visualprocessingstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="visualcontenttype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="visionprocessingstatus").drop(op.get_bind(), checkfirst=True)
