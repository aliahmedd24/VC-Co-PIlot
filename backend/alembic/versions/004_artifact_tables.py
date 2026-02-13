"""Artifact and artifact version tables

Revision ID: 004
Revises: 003
Create Date: 2026-02-12

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enum types
    artifacttype_enum = sa.Enum(
        "lean_canvas",
        "research_brief",
        "pitch_narrative",
        "deck_outline",
        "financial_model",
        "valuation_memo",
        "dataroom_structure",
        "kpi_dashboard",
        "board_memo",
        "custom",
        name="artifacttype",
    )
    artifacttype_enum.create(op.get_bind(), checkfirst=True)

    artifactstatus_enum = sa.Enum(
        "draft",
        "in_progress",
        "ready",
        "archived",
        name="artifactstatus",
    )
    artifactstatus_enum.create(op.get_bind(), checkfirst=True)

    # Artifacts table
    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("type", artifacttype_enum, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", artifactstatus_enum, server_default="draft", nullable=False),
        sa.Column("owner_agent", sa.String(100), nullable=False),
        sa.Column("content", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("assumptions", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("current_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Artifact Versions table
    op.create_table(
        "artifact_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("diff", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("artifact_id", "version", name="uq_artifact_version"),
    )

    # Add artifact_id to chat_messages
    op.add_column(
        "chat_messages",
        sa.Column(
            "artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "artifact_id")
    op.drop_table("artifact_versions")
    op.drop_table("artifacts")

    op.execute("DROP TYPE IF EXISTS artifactstatus")
    op.execute("DROP TYPE IF EXISTS artifacttype")
