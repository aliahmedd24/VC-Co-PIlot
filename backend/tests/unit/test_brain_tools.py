"""Tests for the 4 brain/knowledge tool handlers."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tools.brain_tools import (
    handle_detect_data_gaps,
    handle_query_entities,
    handle_search_brain,
    handle_traverse_relations,
)
from app.models.kg_entity import KGEntity, KGEntityStatus, KGEntityType


def _make_entity(
    entity_type: KGEntityType = KGEntityType.COMPETITOR,
    name: str = "TestEntity",
    confidence: float = 0.8,
    status: KGEntityStatus = KGEntityStatus.CONFIRMED,
    venture_id: str = "v1",
    updated_at: datetime | None = None,
    evidence: list[Any] | None = None,
    extra_data: dict[str, Any] | None = None,
) -> KGEntity:
    """Create a mock KGEntity."""
    entity = MagicMock(spec=KGEntity)
    entity.id = uuid.uuid4()
    entity.venture_id = venture_id
    entity.type = entity_type
    entity.status = status
    entity.confidence = confidence
    data = {"name": name}
    if extra_data:
        data.update(extra_data)
    entity.data = data
    entity.evidence = evidence if evidence is not None else []
    entity.updated_at = updated_at or datetime.now(UTC)
    return entity


def _make_ctx(db_session: AsyncSession | None = None) -> Any:
    """Create a mock ToolExecutor context."""
    ctx = MagicMock()
    ctx.venture.id = uuid.uuid4()
    ctx.venture.stage.value = "seed"
    ctx.db = db_session or AsyncMock()
    ctx.brain = MagicMock()
    ctx.brain.kg = MagicMock()
    return ctx


# --------------------------------------------------------------------------- #
# query_entities (now delegates to search_entities_advanced)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_query_entities_calls_search_entities_advanced() -> None:
    """query_entities delegates to KG.search_entities_advanced."""
    ctx = _make_ctx()
    mock_entity = _make_entity()
    ctx.brain.kg.search_entities_advanced = AsyncMock(return_value=[mock_entity])

    result = await handle_query_entities(
        {"entity_types": ["competitor"], "min_confidence": 0.5, "limit": 10},
        ctx,
    )

    ctx.brain.kg.search_entities_advanced.assert_called_once()
    assert result["count"] == 1
    assert result["entities"][0]["type"] == "competitor"


@pytest.mark.asyncio
async def test_query_entities_empty() -> None:
    """query_entities with no results returns empty list."""
    ctx = _make_ctx()
    ctx.brain.kg.search_entities_advanced = AsyncMock(return_value=[])

    result = await handle_query_entities({}, ctx)
    assert result["count"] == 0
    assert result["entities"] == []


# --------------------------------------------------------------------------- #
# search_brain
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_search_brain_calls_retrieve() -> None:
    """search_brain calls brain.retrieve with the query."""
    ctx = _make_ctx()
    mock_response = MagicMock()
    mock_response.chunks = []
    mock_response.entities = []
    ctx.brain.retrieve = AsyncMock(return_value=mock_response)

    with patch(
        "app.core.tools.brain_tools.embedding_service"
    ) as mock_embed:
        mock_embed.embed_text = MagicMock(return_value=[0.1] * 1536)
        result = await handle_search_brain(
            {"query": "market size analysis"},
            ctx,
        )

    assert result["chunk_count"] == 0
    assert result["entity_count"] == 0
    ctx.brain.retrieve.assert_called_once()


@pytest.mark.asyncio
async def test_search_brain_respects_max_chunks() -> None:
    """search_brain caps max_chunks to 15."""
    ctx = _make_ctx()
    mock_response = MagicMock()
    mock_response.chunks = []
    mock_response.entities = []
    ctx.brain.retrieve = AsyncMock(return_value=mock_response)

    with patch(
        "app.core.tools.brain_tools.embedding_service"
    ) as mock_embed:
        mock_embed.embed_text = MagicMock(return_value=[0.1] * 1536)
        await handle_search_brain(
            {"query": "test", "max_chunks": 100},
            ctx,
        )

    # Verify max_chunks was capped to 15
    call_kwargs = ctx.brain.retrieve.call_args
    assert call_kwargs.kwargs["max_chunks"] == 15


# --------------------------------------------------------------------------- #
# detect_data_gaps
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_detect_data_gaps_empty_kg() -> None:
    """detect_data_gaps with empty KG reports all types as missing."""
    ctx = _make_ctx()
    ctx.brain.kg.get_entities_by_venture = AsyncMock(return_value=[])

    result = await handle_detect_data_gaps({}, ctx)

    assert result["total_entities"] == 0
    assert len(result["missing_entity_types"]) == len(KGEntityType)
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_detect_data_gaps_partial_data() -> None:
    """detect_data_gaps identifies missing types when some data exists."""
    ctx = _make_ctx()
    entities = [
        _make_entity(KGEntityType.COMPETITOR, "Rival Inc", 0.9),
        _make_entity(KGEntityType.MARKET, "AI Market", 0.7),
        _make_entity(KGEntityType.METRIC, "MRR", 0.3, KGEntityStatus.NEEDS_REVIEW),
    ]
    ctx.brain.kg.get_entities_by_venture = AsyncMock(return_value=entities)

    result = await handle_detect_data_gaps({}, ctx)

    assert result["total_entities"] == 3
    assert "competitor" not in result["missing_entity_types"]
    assert "market" not in result["missing_entity_types"]
    assert "icp" in result["missing_entity_types"]
    # MRR has low confidence
    assert len(result["low_confidence_entities"]) == 1
    assert result["low_confidence_entities"][0]["name"] == "MRR"


@pytest.mark.asyncio
async def test_detect_data_gaps_focus_areas() -> None:
    """detect_data_gaps respects focus_areas filter."""
    ctx = _make_ctx()
    ctx.brain.kg.get_entities_by_venture = AsyncMock(return_value=[])

    result = await handle_detect_data_gaps(
        {"focus_areas": ["competitor", "market"]},
        ctx,
    )

    # Only competitor and market should be reported as missing
    assert set(result["missing_entity_types"]) == {"competitor", "market"}


@pytest.mark.asyncio
async def test_detect_data_gaps_staleness() -> None:
    """detect_data_gaps flags entities not updated in 30+ days."""
    ctx = _make_ctx()
    old_date = datetime.now(UTC) - timedelta(days=45)
    entities = [
        _make_entity(
            KGEntityType.COMPETITOR,
            "Stale Corp",
            0.8,
            updated_at=old_date,
        ),
        _make_entity(
            KGEntityType.COMPETITOR,
            "Fresh Corp",
            0.8,
            updated_at=datetime.now(UTC),
        ),
    ]
    ctx.brain.kg.get_entities_by_venture = AsyncMock(return_value=entities)

    result = await handle_detect_data_gaps({}, ctx)

    assert len(result["stale_entities"]) == 1
    assert result["stale_entities"][0]["name"] == "Stale Corp"
    assert result["stale_entities"][0]["days_since_update"] >= 45
    stale_rec = [r for r in result["recommendations"] if "30+ days" in r]
    assert len(stale_rec) == 1


@pytest.mark.asyncio
async def test_detect_data_gaps_evidence_coverage() -> None:
    """detect_data_gaps flags entities with no evidence."""
    ctx = _make_ctx()
    entities = [
        _make_entity(
            KGEntityType.ICP,
            "No Evidence ICP",
            0.7,
            evidence=[],
        ),
        _make_entity(
            KGEntityType.ICP,
            "Has Evidence ICP",
            0.7,
            evidence=[MagicMock()],
        ),
    ]
    ctx.brain.kg.get_entities_by_venture = AsyncMock(return_value=entities)

    result = await handle_detect_data_gaps({}, ctx)

    assert len(result["no_evidence_entities"]) == 1
    assert result["no_evidence_entities"][0]["name"] == "No Evidence ICP"
    evidence_rec = [r for r in result["recommendations"] if "no supporting evidence" in r]
    assert len(evidence_rec) == 1


@pytest.mark.asyncio
async def test_detect_data_gaps_completeness_scoring() -> None:
    """detect_data_gaps calculates data completeness per entity type."""
    ctx = _make_ctx()
    # Market entity with only name (missing tam, sam, som) → 25% complete
    entities = [
        _make_entity(
            KGEntityType.MARKET,
            "Incomplete Market",
            0.8,
        ),
    ]
    ctx.brain.kg.get_entities_by_venture = AsyncMock(return_value=entities)

    result = await handle_detect_data_gaps({}, ctx)

    assert "completeness_scores" in result
    assert "market" in result["completeness_scores"]
    # Only "name" is present out of [name, tam, sam, som] → 0.25
    assert result["completeness_scores"]["market"] == 0.25
    completeness_rec = [r for r in result["recommendations"] if "complete" in r.lower()]
    assert len(completeness_rec) >= 1


# --------------------------------------------------------------------------- #
# traverse_relations (now delegates to KG.traverse)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_traverse_relations_delegates_to_kg() -> None:
    """traverse_relations delegates to KnowledgeGraph.traverse."""
    ctx = _make_ctx()
    mock_result = {
        "start_entities": 1,
        "relation_count": 2,
        "relations": [{"type": "targets"}],
    }
    ctx.brain.kg.traverse = AsyncMock(return_value=mock_result)

    result = await handle_traverse_relations(
        {"entity_type": "competitor", "direction": "outgoing"},
        ctx,
    )

    ctx.brain.kg.traverse.assert_called_once()
    assert result["start_entities"] == 1
    assert result["relation_count"] == 2


@pytest.mark.asyncio
async def test_traverse_relations_no_entities() -> None:
    """traverse_relations with no matching entities returns empty."""
    ctx = _make_ctx()
    ctx.brain.kg.traverse = AsyncMock(return_value={
        "start_entities": 0,
        "relation_count": 0,
        "relations": [],
        "message": "No competitor entities found matching criteria.",
    })

    result = await handle_traverse_relations(
        {"entity_type": "competitor"},
        ctx,
    )
    assert result["start_entities"] == 0
    assert result["relations"] == []


# --------------------------------------------------------------------------- #
# Tool loop integration
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_tool_loop_with_mock_claude() -> None:
    """Integration test: BaseAgent tool loop handles tool_use + tool_result."""

    from app.core.agents.base import AgentConfig, BaseAgent
    from app.core.tools.executor import ToolExecutor
    from app.core.tools.registry import ToolDefinition, ToolRegistry
    from app.models.kg_entity import KGEntityType
    from app.models.venture import VentureStage

    # Create a simple agent
    class TestAgent(BaseAgent):
        def get_agent_specific_instructions(self) -> str:
            return "You are a test agent."

    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        description="Test",
        supported_stages=[VentureStage.SEED],
        required_context=[KGEntityType.VENTURE],
        can_create_artifacts=[],
        max_tool_rounds=3,
    )
    agent = TestAgent(config)

    # Create a tool
    registry = ToolRegistry()
    defn = ToolDefinition(
        name="calc_value",
        description="Calculate",
        input_schema={"type": "object", "properties": {"x": {"type": "number"}}},
    )
    handler = AsyncMock(return_value={"result": 100})
    registry.register(defn, handler)

    executor = ToolExecutor(
        registry=registry,
        db=MagicMock(),
        brain=MagicMock(),
        venture=MagicMock(),
        user_id="user-1",
    )

    # Mock Claude response: first returns tool_use, then text
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.name = "calc_value"
    mock_tool_block.input = {"x": 42}
    mock_tool_block.id = "tool-use-id-1"

    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = "The calculated value is 100."

    # First call returns tool_use, second returns text
    response_1 = MagicMock()
    response_1.content = [mock_tool_block]

    response_2 = MagicMock()
    response_2.content = [mock_text_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        side_effect=[response_1, response_2]
    )
    agent._client = mock_client

    # Define tools in Claude format
    tools = [{"name": "calc_value", "description": "Calculate", "input_schema": {"type": "object"}}]

    result = await agent._call_claude_with_tools(
        system="System prompt",
        prompt="What is the value?",
        tools=tools,
        executor=executor,
    )

    assert result == "The calculated value is 100."
    handler.assert_called_once()
    assert mock_client.messages.create.call_count == 2

