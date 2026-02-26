"""MCP server for cross-session agent memory.

Provides store_insight, recall_context, update_preference tools
and memory resources for external MCP clients.

Mount via FastAPI:
    from app.mcp.memory_server import memory_mcp_app
    app.mount("/mcp/memory", memory_mcp_app)
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import structlog
from fastmcp import FastMCP
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.models.agent_memory import AgentMemory, MemoryType

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

memory_mcp = FastMCP(
    "Agent Memory",
    instructions=(
        "Store and recall cross-session agent memory. "
        "Persist insights, user preferences, and contextual "
        "information that survives across conversations."
    ),
)

# ---------------------------------------------------------------------------
# Database session helper
# ---------------------------------------------------------------------------

_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
_session_factory = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False,
)


async def _get_db() -> AsyncSession:
    """Create a fresh async database session."""
    return _session_factory()


# ---------------------------------------------------------------------------
# Tool: store_insight
# ---------------------------------------------------------------------------


@memory_mcp.tool
async def store_insight(
    venture_id: str,
    key: str,
    value: str,
    agent_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Store an insight discovered during agent analysis.

    Args:
        venture_id: UUID of the venture.
        key: Short identifier for the insight (e.g. "market_size_update").
        value: The insight content.
        agent_id: Which agent produced the insight.
        metadata: Optional additional structured data.
    """
    db = await _get_db()
    try:
        memory = AgentMemory(
            venture_id=UUID(venture_id),
            agent_id=agent_id,
            memory_type=MemoryType.INSIGHT,
            key=key,
            value=value,
            metadata_=metadata or {},
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)

        return {
            "status": "stored",
            "memory_id": str(memory.id),
            "key": key,
        }
    except Exception as exc:
        await db.rollback()
        logger.error("store_insight_failed", error=str(exc))
        return {"error": f"Failed to store insight: {exc}"}
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Tool: recall_context
# ---------------------------------------------------------------------------


@memory_mcp.tool
async def recall_context(
    venture_id: str,
    memory_type: str | None = None,
    key_prefix: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Recall stored memories for a venture.

    Args:
        venture_id: UUID of the venture.
        memory_type: Filter by type (insight, preference, context).
        key_prefix: Filter by key prefix.
        limit: Maximum entries to return.
    """
    db = await _get_db()
    try:
        stmt = select(AgentMemory).where(
            AgentMemory.venture_id == UUID(venture_id),
        )

        if memory_type:
            stmt = stmt.where(
                AgentMemory.memory_type == MemoryType(memory_type),
            )
        if key_prefix:
            stmt = stmt.where(AgentMemory.key.startswith(key_prefix))

        stmt = stmt.order_by(AgentMemory.updated_at.desc()).limit(
            min(limit, 50),
        )

        result = await db.execute(stmt)
        memories = result.scalars().all()

        return {
            "count": len(memories),
            "memories": [
                {
                    "id": str(m.id),
                    "type": m.memory_type.value,
                    "key": m.key,
                    "value": m.value,
                    "agent_id": m.agent_id,
                    "metadata": m.metadata_,
                }
                for m in memories
            ],
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Tool: update_preference
# ---------------------------------------------------------------------------


@memory_mcp.tool
async def update_preference(
    venture_id: str,
    key: str,
    value: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Set or update a user/venture preference.

    If a preference with the same key exists, it is updated.
    Otherwise, a new preference is created.

    Args:
        venture_id: UUID of the venture.
        key: Preference key (e.g. "report_format", "risk_tolerance").
        value: Preference value.
        user_id: Optional user UUID for user-specific preferences.
    """
    db = await _get_db()
    try:
        # Check for existing
        stmt = select(AgentMemory).where(
            AgentMemory.venture_id == UUID(venture_id),
            AgentMemory.memory_type == MemoryType.PREFERENCE,
            AgentMemory.key == key,
        )
        if user_id:
            stmt = stmt.where(AgentMemory.user_id == UUID(user_id))

        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            await db.execute(
                update(AgentMemory)
                .where(AgentMemory.id == existing.id)
                .values(value=value),
            )
            await db.commit()
            return {
                "status": "updated",
                "memory_id": str(existing.id),
                "key": key,
            }

        memory = AgentMemory(
            venture_id=UUID(venture_id),
            user_id=UUID(user_id) if user_id else None,
            memory_type=MemoryType.PREFERENCE,
            key=key,
            value=value,
            metadata_={},
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)

        return {
            "status": "created",
            "memory_id": str(memory.id),
            "key": key,
        }
    except Exception as exc:
        await db.rollback()
        logger.error("update_preference_failed", error=str(exc))
        return {"error": f"Failed to update preference: {exc}"}
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Resource: venture insights
# ---------------------------------------------------------------------------


@memory_mcp.resource("memory://venture/{venture_id}/insights")
async def get_venture_insights(venture_id: str) -> str:
    """All insights stored for a venture.

    Returns a JSON list of insights with keys, values, and metadata.
    """
    db = await _get_db()
    try:
        stmt = (
            select(AgentMemory)
            .where(
                AgentMemory.venture_id == UUID(venture_id),
                AgentMemory.memory_type == MemoryType.INSIGHT,
            )
            .order_by(AgentMemory.updated_at.desc())
            .limit(100)
        )
        result = await db.execute(stmt)
        memories = result.scalars().all()

        return json.dumps({
            "venture_id": venture_id,
            "insight_count": len(memories),
            "insights": [
                {
                    "key": m.key,
                    "value": m.value,
                    "agent_id": m.agent_id,
                    "metadata": m.metadata_,
                }
                for m in memories
            ],
        })
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Resource: user preferences
# ---------------------------------------------------------------------------


@memory_mcp.resource("memory://user/{user_id}/preferences")
async def get_user_preferences(user_id: str) -> str:
    """All preferences for a user across ventures.

    Returns a JSON list of preference key-value pairs.
    """
    db = await _get_db()
    try:
        stmt = (
            select(AgentMemory)
            .where(
                AgentMemory.user_id == UUID(user_id),
                AgentMemory.memory_type == MemoryType.PREFERENCE,
            )
            .order_by(AgentMemory.key)
            .limit(100)
        )
        result = await db.execute(stmt)
        memories = result.scalars().all()

        return json.dumps({
            "user_id": user_id,
            "preference_count": len(memories),
            "preferences": [
                {
                    "key": m.key,
                    "value": m.value,
                    "venture_id": str(m.venture_id),
                }
                for m in memories
            ],
        })
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# ASGI app for mounting into FastAPI
# ---------------------------------------------------------------------------

memory_mcp_app = memory_mcp.http_app(path="/mcp")
