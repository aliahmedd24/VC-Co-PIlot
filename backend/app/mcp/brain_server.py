"""MCP server exposing Startup Brain tools and resources.

Provides 4 tools (query_entities, search_brain, detect_data_gaps,
traverse_relations) and 2 resource templates for external MCP clients
such as Claude Desktop, Cursor, or MCP Inspector.

Mount via FastAPI:
    mcp_app = brain_mcp.http_app(path="/mcp")
    app.mount("/mcp/brain", mcp_app)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.core.brain.startup_brain import StartupBrain
from app.models.kg_entity import (
    KGEntityStatus,
    KGEntityType,
    KGRelationType,
)
from app.services.embedding_service import embedding_service

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

brain_mcp = FastMCP(
    "Startup Brain",
    instructions=(
        "Access a startup's knowledge graph and document corpus. "
        "Query entities, search documents, detect data gaps, "
        "and traverse relationships between entities."
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
    """Create a fresh async database session for MCP tool calls."""
    return _session_factory()


def _brain() -> StartupBrain:
    """Return a StartupBrain instance."""
    return StartupBrain()


# ---------------------------------------------------------------------------
# Tool: query_entities
# ---------------------------------------------------------------------------


@brain_mcp.tool
async def query_entities(
    venture_id: str,
    entity_types: list[str] | None = None,
    keyword: str | None = None,
    min_confidence: float = 0.0,
    status_filter: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Query the venture's knowledge graph for specific entities.

    Filter by type (venture, market, icp, competitor, product,
    team_member, metric, funding_assumption, risk), minimum
    confidence, keyword, or status.
    """
    db = await _get_db()
    brain = _brain()
    try:
        et = (
            [KGEntityType(t) for t in entity_types]
            if entity_types
            else None
        )
        sf = KGEntityStatus(status_filter) if status_filter else None
        limit = min(limit, 50)

        entities = await brain.kg.search_entities_advanced(
            db=db,
            venture_id=UUID(venture_id),
            keyword=keyword,
            entity_types=et,
            min_confidence=min_confidence,
            status_filter=sf,
            limit=limit,
        )

        return {
            "count": len(entities),
            "entities": [
                {
                    "id": str(e.id),
                    "type": e.type.value,
                    "status": e.status.value,
                    "confidence": e.confidence,
                    "data": e.data,
                }
                for e in entities
            ],
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Tool: search_brain
# ---------------------------------------------------------------------------


@brain_mcp.tool
async def search_brain(
    venture_id: str,
    query: str,
    entity_types: list[str] | None = None,
    max_chunks: int = 5,
) -> dict[str, Any]:
    """Search the venture's document corpus and knowledge graph.

    Returns relevant document chunks and matching entities.
    Use this for research queries when you need additional context.
    """
    import asyncio

    db = await _get_db()
    brain = _brain()
    try:
        et = (
            [KGEntityType(t) for t in entity_types]
            if entity_types
            else None
        )
        max_chunks = min(max_chunks, 15)

        query_embedding = await asyncio.to_thread(
            embedding_service.embed_text, query,
        )

        result = await brain.retrieve(
            db=db,
            venture_id=UUID(venture_id),
            query=query,
            query_embedding=query_embedding,
            entity_types=et,
            max_chunks=max_chunks,
        )

        return {
            "chunks": [
                {
                    "document_id": c.document_id,
                    "content": c.content[:500],
                    "score": round(c.final_score, 3),
                }
                for c in result.chunks
            ],
            "entities": [
                {
                    "type": e.type.value,
                    "data": e.data,
                    "confidence": e.confidence,
                }
                for e in result.entities
            ],
            "chunk_count": len(result.chunks),
            "entity_count": len(result.entities),
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Tool: detect_data_gaps
# ---------------------------------------------------------------------------

_COMPLETENESS_FIELDS: dict[str, list[str]] = {
    "venture": ["name", "one_liner", "problem", "solution"],
    "market": ["name", "tam", "sam", "som"],
    "icp": ["name", "description", "pain_points"],
    "competitor": ["name", "description", "strengths"],
    "product": ["name", "description", "features"],
    "team_member": ["name", "role", "bio"],
    "metric": ["name", "value", "unit"],
    "funding_assumption": ["name", "amount", "valuation"],
    "risk": ["name", "severity", "mitigation"],
}


@brain_mcp.tool
async def detect_data_gaps(
    venture_id: str,
    focus_areas: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze the venture's knowledge graph for missing or weak data.

    Returns which entity types are missing, which have low confidence,
    staleness analysis, evidence coverage, completeness scores,
    and recommendations.
    """
    db = await _get_db()
    brain = _brain()
    try:
        entities = await brain.kg.get_entities_by_venture(
            db, UUID(venture_id),
        )

        focus_set = set(focus_areas) if focus_areas else None

        type_counts: dict[str, int] = {}
        low_confidence: list[dict[str, Any]] = []
        stale_entities: list[dict[str, Any]] = []
        no_evidence: list[dict[str, Any]] = []
        completeness_scores: dict[str, float] = {}
        type_field_scores: dict[str, list[float]] = {}
        now = datetime.now(UTC)

        for entity in entities:
            t = entity.type.value
            if focus_set and t not in focus_set:
                continue
            type_counts[t] = type_counts.get(t, 0) + 1

            if entity.confidence < 0.5:
                low_confidence.append({
                    "type": t,
                    "name": entity.data.get("name", ""),
                    "confidence": entity.confidence,
                })

            if (
                hasattr(entity, "updated_at")
                and entity.updated_at is not None
            ):
                days_since = (now - entity.updated_at).days
                if days_since >= 30:
                    stale_entities.append({
                        "type": t,
                        "name": entity.data.get("name", ""),
                        "days_since_update": days_since,
                    })

            evidence_count = (
                len(entity.evidence) if entity.evidence else 0
            )
            if evidence_count == 0:
                no_evidence.append({
                    "type": t,
                    "name": entity.data.get("name", ""),
                })

            expected = _COMPLETENESS_FIELDS.get(t, [])
            if expected:
                present = sum(
                    1 for f in expected if entity.data.get(f)
                )
                score = present / len(expected)
                type_field_scores.setdefault(t, []).append(score)

        for et, scores in type_field_scores.items():
            completeness_scores[et] = round(
                sum(scores) / len(scores), 2,
            )

        check_types = (
            set(focus_areas)
            if focus_set
            else {t.value for t in KGEntityType}
        )
        missing_types = sorted(check_types - set(type_counts.keys()))

        recommendations: list[str] = []
        if missing_types:
            recommendations.append(
                f"Missing entity types: {', '.join(missing_types)}"
            )
        if low_confidence:
            recommendations.append(
                f"{len(low_confidence)} entities have low confidence "
                "(<0.5). Upload supporting documents."
            )
        if stale_entities:
            recommendations.append(
                f"{len(stale_entities)} entities are stale (30+ days)."
            )

        return {
            "entity_counts_by_type": type_counts,
            "total_entities": sum(type_counts.values()),
            "missing_entity_types": missing_types,
            "low_confidence_entities": low_confidence[:10],
            "stale_entities": stale_entities[:10],
            "no_evidence_entities": no_evidence[:10],
            "completeness_scores": completeness_scores,
            "recommendations": recommendations,
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Tool: traverse_relations
# ---------------------------------------------------------------------------


@brain_mcp.tool
async def traverse_relations(
    venture_id: str,
    entity_type: str,
    entity_name: str | None = None,
    relation_type: str | None = None,
    direction: str = "both",
) -> dict[str, Any]:
    """Traverse knowledge graph relationships.

    Follow edges like COMPETES_WITH, TARGETS, DEPENDS_ON, BELONGS_TO
    starting from entities of a given type.
    """
    db = await _get_db()
    brain = _brain()
    try:
        et = KGEntityType(entity_type)
        rt = (
            KGRelationType(relation_type)
            if relation_type
            else None
        )

        return await brain.kg.traverse(
            db=db,
            venture_id=UUID(venture_id),
            entity_type=et,
            entity_name=entity_name,
            relation_type=rt,
            direction=direction,
        )
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Resource: venture snapshot
# ---------------------------------------------------------------------------


@brain_mcp.resource("brain://venture/{venture_id}/snapshot")
async def get_venture_snapshot(venture_id: str) -> str:
    """Full knowledge graph snapshot for a venture.

    Returns all entities with types, counts, and summary statistics.
    """
    db = await _get_db()
    brain = _brain()
    try:
        entities = await brain.kg.get_entities_by_venture(
            db, UUID(venture_id),
        )

        type_counts: dict[str, int] = {}
        entity_list: list[dict[str, Any]] = []
        for e in entities:
            t = e.type.value
            type_counts[t] = type_counts.get(t, 0) + 1
            entity_list.append({
                "id": str(e.id),
                "type": t,
                "status": e.status.value,
                "confidence": e.confidence,
                "data": e.data,
            })

        return json.dumps({
            "venture_id": venture_id,
            "total_entities": len(entities),
            "entity_counts_by_type": type_counts,
            "entities": entity_list,
        })
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Resource: entities by type
# ---------------------------------------------------------------------------


@brain_mcp.resource(
    "brain://venture/{venture_id}/entities/{entity_type}",
)
async def get_entities_by_type(
    venture_id: str,
    entity_type: str,
) -> str:
    """Get all entities of a specific type for a venture.

    Valid types: venture, market, icp, competitor, product,
    team_member, metric, funding_assumption, risk.
    """
    db = await _get_db()
    brain = _brain()
    try:
        et = KGEntityType(entity_type)
        entities = await brain.kg.search_entities_advanced(
            db=db,
            venture_id=UUID(venture_id),
            entity_types=[et],
            limit=50,
        )

        return json.dumps({
            "venture_id": venture_id,
            "entity_type": entity_type,
            "count": len(entities),
            "entities": [
                {
                    "id": str(e.id),
                    "status": e.status.value,
                    "confidence": e.confidence,
                    "data": e.data,
                }
                for e in entities
            ],
        })
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# ASGI app for mounting into FastAPI
# ---------------------------------------------------------------------------

mcp_app = brain_mcp.http_app(path="/mcp")
