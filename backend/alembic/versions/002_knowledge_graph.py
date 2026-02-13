"""Knowledge graph tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-12

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # KG Entities
    op.create_table(
        "kg_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "venture_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ventures.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum(
                "venture", "market", "icp", "competitor", "product",
                "team_member", "metric", "funding_assumption", "risk",
                name="kgentitytype",
            ),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "confirmed", "needs_review", "suggested", "pinned",
                name="kgentitystatus",
            ),
            default="needs_review",
            nullable=False,
        ),
        sa.Column("data", postgresql.JSONB(), default={}, nullable=False),
        sa.Column("confidence", sa.Float(), default=0.5, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_kg_entities_venture_type", "kg_entities", ["venture_id", "type"])

    # KG Evidence
    op.create_table(
        "kg_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kg_entities.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("agent_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # KG Relations
    op.create_table(
        "kg_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "from_entity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kg_entities.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "to_entity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kg_entities.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum(
                "competes_with", "targets", "depends_on", "conflicts_with", "belongs_to",
                name="kgrelationtype",
            ),
            nullable=False,
        ),
        sa.Column("relation_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # KG Events (append-only)
    op.create_table(
        "kg_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "venture_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ventures.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.Enum(
                "entity_created", "entity_updated", "entity_deleted",
                "entity_confirmed", "relation_created", "conflict_detected",
                name="kgeventtype",
            ),
            nullable=False,
        ),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_kg_events_venture_created", "kg_events", ["venture_id", "created_at"])


def downgrade() -> None:
    op.drop_table("kg_events")
    op.drop_table("kg_relations")
    op.drop_table("kg_evidence")
    op.drop_table("kg_entities")

    op.execute("DROP TYPE IF EXISTS kgeventtype")
    op.execute("DROP TYPE IF EXISTS kgrelationtype")
    op.execute("DROP TYPE IF EXISTS kgentitystatus")
    op.execute("DROP TYPE IF EXISTS kgentitytype")
