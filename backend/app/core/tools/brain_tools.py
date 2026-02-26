"""Tool handlers for enhanced knowledge graph and brain access."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from app.core.tools.registry import ToolDefinition, tool_registry
from app.models.kg_entity import (
    KGEntityStatus,
    KGEntityType,
    KGRelationType,
)
from app.services.embedding_service import embedding_service

if TYPE_CHECKING:
    from app.core.tools.executor import ToolExecutor


# --------------------------------------------------------------------------- #
# Tool: query_entities
# --------------------------------------------------------------------------- #

QUERY_ENTITIES_DEF = ToolDefinition(
    name="query_entities",
    description=(
        "Query the venture's knowledge graph for specific entities. Filter by "
        "type (venture, market, icp, competitor, product, team_member, metric, "
        "funding_assumption, risk), minimum confidence, or status."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "entity_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [t.value for t in KGEntityType],
                },
                "description": "Filter by entity types",
            },
            "keyword": {
                "type": "string",
                "description": "Keyword search within entity data",
            },
            "min_confidence": {
                "type": "number",
                "default": 0.0,
                "description": "Minimum confidence threshold (0.0-1.0)",
            },
            "status_filter": {
                "type": "string",
                "enum": [s.value for s in KGEntityStatus],
                "description": "Filter by entity status",
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "description": "Max entities to return (1-50)",
            },
        },
    },
)


async def handle_query_entities(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Advanced entity query using KnowledgeGraph.search_entities_advanced."""
    entity_types_raw = tool_input.get("entity_types", [])
    entity_types = [KGEntityType(t) for t in entity_types_raw] if entity_types_raw else None
    keyword = tool_input.get("keyword")
    min_confidence = tool_input.get("min_confidence", 0.0)
    status_raw = tool_input.get("status_filter")
    status_filter = KGEntityStatus(status_raw) if status_raw else None
    limit = min(tool_input.get("limit", 20), 50)

    entities = await ctx.brain.kg.search_entities_advanced(
        db=ctx.db,
        venture_id=ctx.venture.id,
        keyword=keyword,
        entity_types=entity_types,
        min_confidence=min_confidence,
        status_filter=status_filter,
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
                "evidence_count": len(e.evidence) if e.evidence else 0,
            }
            for e in entities
        ],
    }


# --------------------------------------------------------------------------- #
# Tool: search_brain
# --------------------------------------------------------------------------- #

SEARCH_BRAIN_DEF = ToolDefinition(
    name="search_brain",
    description=(
        "Search the venture's document corpus and knowledge graph for additional "
        "information. Use this for follow-up research queries when initial context "
        "is insufficient. Returns relevant document chunks and matching entities."
    ),
    input_schema={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query text",
            },
            "entity_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter entities by type",
            },
            "max_chunks": {
                "type": "integer",
                "default": 5,
                "description": "Max document chunks to return (1-15)",
            },
        },
    },
)


async def handle_search_brain(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Execute a follow-up brain retrieval query."""
    query = tool_input["query"]
    max_chunks = min(tool_input.get("max_chunks", 5), 15)

    entity_types_raw = tool_input.get("entity_types", [])
    entity_types = [KGEntityType(t) for t in entity_types_raw] if entity_types_raw else None

    query_embedding = await asyncio.to_thread(
        embedding_service.embed_text, query,
    )

    result = await ctx.brain.retrieve(
        db=ctx.db,
        venture_id=ctx.venture.id,
        query=query,
        query_embedding=query_embedding,
        entity_types=entity_types,
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


# --------------------------------------------------------------------------- #
# Tool: detect_data_gaps
# --------------------------------------------------------------------------- #

# Expected data fields for completeness scoring per entity type.
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

DETECT_DATA_GAPS_DEF = ToolDefinition(
    name="detect_data_gaps",
    description=(
        "Analyze the venture's knowledge graph to find missing or weak data "
        "areas. Returns which entity types are missing, which have low confidence, "
        "staleness analysis, evidence coverage, data completeness scores, "
        "and recommendations for improving analysis quality."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "focus_areas": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [t.value for t in KGEntityType],
                },
                "description": "Limit gap analysis to specific entity types",
            },
        },
    },
)


async def handle_detect_data_gaps(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Analyze KG data quality with staleness, evidence, and completeness."""
    from datetime import UTC, datetime

    entities = await ctx.brain.kg.get_entities_by_venture(ctx.db, ctx.venture.id)

    focus_raw = tool_input.get("focus_areas", [])
    focus_set = set(focus_raw) if focus_raw else None

    type_counts: dict[str, int] = {}
    low_confidence: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    stale_entities: list[dict[str, Any]] = []
    no_evidence: list[dict[str, Any]] = []
    completeness_scores: dict[str, float] = {}
    confirmed_count = 0
    now = datetime.now(UTC)

    # Collect type-level completeness data
    type_field_scores: dict[str, list[float]] = {}

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
        if entity.status == KGEntityStatus.NEEDS_REVIEW:
            needs_review.append({
                "type": t,
                "name": entity.data.get("name", ""),
            })
        if entity.status == KGEntityStatus.CONFIRMED:
            confirmed_count += 1

        # Staleness: entities not updated in 30+ days
        if hasattr(entity, "updated_at") and entity.updated_at is not None:
            days_since = (now - entity.updated_at).days
            if days_since >= 30:
                stale_entities.append({
                    "type": t,
                    "name": entity.data.get("name", ""),
                    "days_since_update": days_since,
                })

        # Evidence coverage: entities with no evidence at all
        evidence_count = len(entity.evidence) if entity.evidence else 0
        if evidence_count == 0:
            no_evidence.append({
                "type": t,
                "name": entity.data.get("name", ""),
            })

        # Data completeness scoring
        expected_fields = _COMPLETENESS_FIELDS.get(t, [])
        if expected_fields:
            present = sum(1 for f in expected_fields if entity.data.get(f))
            score = present / len(expected_fields) if expected_fields else 1.0
            if t not in type_field_scores:
                type_field_scores[t] = []
            type_field_scores[t].append(score)

    # Average completeness per type
    for entity_type, scores in type_field_scores.items():
        completeness_scores[entity_type] = round(sum(scores) / len(scores), 2)

    # Identify missing types
    check_types = set(focus_raw) if focus_set else {t.value for t in KGEntityType}
    present_types = set(type_counts.keys())
    missing_types = sorted(check_types - present_types)

    recommendations: list[str] = []
    if "competitor" in missing_types:
        recommendations.append(
            "No competitors identified. Upload competitive analysis or describe your competition."
        )
    if "metric" in missing_types:
        recommendations.append(
            "No metrics tracked. Add KPIs like MRR, churn rate, CAC, LTV."
        )
    if "team_member" in missing_types or type_counts.get("team_member", 0) < 2:
        recommendations.append(
            "Team profile is thin. Add team member information for investor confidence."
        )
    if "market" in missing_types:
        recommendations.append(
            "No market data. Upload or provide TAM/SAM/SOM and industry analysis."
        )
    if "icp" in missing_types:
        recommendations.append(
            "No ideal customer profile defined. Describe your target customers."
        )
    if "funding_assumption" in missing_types:
        recommendations.append(
            "No funding assumptions. Add planned raise amount, valuation expectations."
        )
    if low_confidence:
        recommendations.append(
            f"{len(low_confidence)} entities have low confidence (<0.5). "
            "Upload supporting documents to strengthen these data points."
        )
    if needs_review:
        recommendations.append(
            f"{len(needs_review)} entities need review. Confirm or reject them "
            "to improve data quality."
        )
    if stale_entities:
        recommendations.append(
            f"{len(stale_entities)} entities haven't been updated in 30+ days. "
            "Review and update stale data."
        )
    if no_evidence:
        recommendations.append(
            f"{len(no_evidence)} entities have no supporting evidence. "
            "Upload documents or add evidence to improve reliability."
        )
    # Completeness-based recommendations
    for entity_type, score in completeness_scores.items():
        if score < 0.5:
            fields = ", ".join(_COMPLETENESS_FIELDS.get(entity_type, []))
            recommendations.append(
                f"{entity_type} entities are only {int(score * 100)}% "
                f"complete. Add missing fields: {fields}"
            )

    return {
        "entity_counts_by_type": type_counts,
        "total_entities": sum(type_counts.values()),
        "confirmed_entities": confirmed_count,
        "missing_entity_types": missing_types,
        "low_confidence_entities": low_confidence[:10],
        "needs_review_entities": needs_review[:10],
        "stale_entities": stale_entities[:10],
        "no_evidence_entities": no_evidence[:10],
        "completeness_scores": completeness_scores,
        "recommendations": recommendations,
    }


# --------------------------------------------------------------------------- #
# Tool: traverse_relations
# --------------------------------------------------------------------------- #

TRAVERSE_RELATIONS_DEF = ToolDefinition(
    name="traverse_relations",
    description=(
        "Traverse knowledge graph relationships. Find entities connected via "
        "relations like COMPETES_WITH, TARGETS, DEPENDS_ON, BELONGS_TO. "
        "Start from entities of a given type and follow edges."
    ),
    input_schema={
        "type": "object",
        "required": ["entity_type"],
        "properties": {
            "entity_type": {
                "type": "string",
                "enum": [t.value for t in KGEntityType],
                "description": "Entity type to start traversal from",
            },
            "entity_name": {
                "type": "string",
                "description": "Optional name to narrow starting entity",
            },
            "relation_type": {
                "type": "string",
                "enum": [r.value for r in KGRelationType],
                "description": "Type of relation to follow",
            },
            "direction": {
                "type": "string",
                "enum": ["outgoing", "incoming", "both"],
                "default": "both",
                "description": "Direction of relation traversal",
            },
        },
    },
)


async def handle_traverse_relations(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Traverse KG relations using KnowledgeGraph.traverse."""
    entity_type = KGEntityType(tool_input["entity_type"])
    entity_name = tool_input.get("entity_name")
    relation_type_raw = tool_input.get("relation_type")
    relation_type = KGRelationType(relation_type_raw) if relation_type_raw else None
    direction = tool_input.get("direction", "both")

    return await ctx.brain.kg.traverse(
        db=ctx.db,
        venture_id=ctx.venture.id,
        entity_type=entity_type,
        entity_name=entity_name,
        relation_type=relation_type,
        direction=direction,
    )


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

def register_brain_tools() -> None:
    """Register all 4 brain/knowledge tools with the global tool registry."""
    tool_registry.register(QUERY_ENTITIES_DEF, handle_query_entities)
    tool_registry.register(SEARCH_BRAIN_DEF, handle_search_brain)
    tool_registry.register(DETECT_DATA_GAPS_DEF, handle_detect_data_gaps)
    tool_registry.register(TRAVERSE_RELATIONS_DEF, handle_traverse_relations)
