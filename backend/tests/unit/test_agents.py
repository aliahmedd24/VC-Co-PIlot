import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agents.base import AgentResponse, BaseAgent
from app.core.agents.dataroom_concierge import dataroom_concierge
from app.core.agents.deck_architect import deck_architect
from app.core.agents.icp_profiler import icp_profiler
from app.core.agents.kpi_dashboard import kpi_dashboard
from app.core.agents.lean_modeler import lean_modeler
from app.core.agents.market_oracle import market_oracle
from app.core.agents.pre_mortem_critic import pre_mortem_critic
from app.core.agents.qa_simulator import qa_simulator
from app.core.agents.storyteller import storyteller
from app.core.agents.valuation_strategist import valuation_strategist
from app.core.agents.venture_architect import venture_architect
from app.core.router.types import ModelProfile, RoutingPlan
from app.models.venture import VentureStage
from app.schemas.brain import BrainSearchResponse


def _make_venture() -> Any:
    v = MagicMock()
    v.id = uuid.uuid4()
    v.name = "TestStartup"
    v.stage = VentureStage.SEED
    v.one_liner = "AI-powered analytics"
    return v


def _make_routing_plan(agent_id: str) -> RoutingPlan:
    return RoutingPlan(
        selected_agent=agent_id,
        model_profile=ModelProfile.DEFAULT,
        tools=[],
        artifact_needed=False,
        fallback_agent="venture-architect",
        confidence=0.8,
        reasoning="test",
        latency_ms=1.0,
    )


def _mock_claude_response(text: str = "This is a helpful response.") -> MagicMock:
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


async def _execute_agent(agent: BaseAgent) -> AgentResponse:
    """Execute an agent with fully mocked dependencies."""
    venture = _make_venture()
    plan = _make_routing_plan(agent.config.id)
    mock_db = AsyncMock(spec=AsyncSession)

    mock_brain = MagicMock()
    mock_brain.retrieve = AsyncMock(
        return_value=BrainSearchResponse(chunks=[], entities=[], citations=[])
    )
    mock_brain.get_snapshot = AsyncMock(return_value=([], 0))
    mock_brain._entity_to_result = MagicMock()

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=_mock_claude_response())

    with (
        patch.object(agent, "_get_client", return_value=mock_client),
        patch(
            "app.core.agents.base.embedding_service"
        ) as mock_embed,
    ):
        mock_embed.embed_text.return_value = [0.1] * 1536
        return await agent.execute(
            prompt="Test question",
            brain=mock_brain,
            db=mock_db,
            venture=venture,
            routing_plan=plan,
            session_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )


@pytest.mark.asyncio
async def test_venture_architect_execute() -> None:
    result = await _execute_agent(venture_architect)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_market_oracle_execute() -> None:
    result = await _execute_agent(market_oracle)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_storyteller_execute() -> None:
    result = await _execute_agent(storyteller)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_deck_architect_execute() -> None:
    result = await _execute_agent(deck_architect)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_valuation_strategist_execute() -> None:
    result = await _execute_agent(valuation_strategist)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_lean_modeler_execute() -> None:
    result = await _execute_agent(lean_modeler)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_kpi_dashboard_execute() -> None:
    result = await _execute_agent(kpi_dashboard)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_qa_simulator_execute() -> None:
    result = await _execute_agent(qa_simulator)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_dataroom_concierge_execute() -> None:
    result = await _execute_agent(dataroom_concierge)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_icp_profiler_execute() -> None:
    result = await _execute_agent(icp_profiler)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_pre_mortem_critic_execute() -> None:
    result = await _execute_agent(pre_mortem_critic)
    assert isinstance(result, AgentResponse)
    assert len(result.content) > 0
