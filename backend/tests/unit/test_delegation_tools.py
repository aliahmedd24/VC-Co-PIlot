"""Tests for the delegation tool handler (delegate_to_agent)."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agents.base import AgentConfig, AgentResponse
from app.core.tools.delegation_tools import (
    MAX_DELEGATION_DEPTH,
    handle_delegate_to_agent,
)
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


def _make_ctx(
    agent_id: str = "venture-architect",
    delegation_depth: int = 0,
) -> Any:
    """Create a mock ToolExecutor context."""
    ctx = MagicMock()
    ctx.agent_id = agent_id
    ctx.delegation_depth = delegation_depth
    ctx.venture = MagicMock()
    ctx.venture.id = uuid.uuid4()
    ctx.venture.workspace_id = uuid.uuid4()
    ctx.venture.name = "TestVenture"
    ctx.venture.stage = VentureStage.SEED
    ctx.venture.one_liner = "A test venture"
    ctx.user_id = str(uuid.uuid4())
    ctx.db = AsyncMock()
    ctx.brain = MagicMock()
    return ctx


def _make_mock_agent(agent_id: str = "pre-mortem-critic") -> MagicMock:
    """Create a mock agent with config and execute method."""
    agent = MagicMock()
    agent.config = AgentConfig(
        id=agent_id,
        name="Pre-Mortem Critic",
        description="Risk analysis specialist",
        supported_stages=[VentureStage.SEED],
        required_context=[KGEntityType.VENTURE],
        can_create_artifacts=["research_brief"],
    )
    agent.execute = AsyncMock(return_value=AgentResponse(
        content="Risk analysis: The main risks are market timing and competition.",
        citations=[{"document_id": "doc-123"}],
        proposed_updates=[],
    ))
    return agent


# --------------------------------------------------------------------------- #
# Success case
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@patch("app.core.tools.delegation_tools.agent_registry")
async def test_delegate_success(mock_registry: Any) -> None:
    """delegate_to_agent successfully delegates to target agent."""
    mock_agent = _make_mock_agent()
    mock_registry.get.return_value = mock_agent

    ctx = _make_ctx(agent_id="venture-architect", delegation_depth=0)

    result = await handle_delegate_to_agent(
        {
            "target_agent": "pre-mortem-critic",
            "prompt": "What are the top 3 risks for this venture?",
        },
        ctx,
    )

    assert "error" not in result
    assert result["delegated_to"] == "pre-mortem-critic"
    assert result["agent_name"] == "Pre-Mortem Critic"
    assert "Risk analysis" in result["content"]
    assert len(result["citations"]) == 1

    # Verify execute was called with use_tools=False
    mock_agent.execute.assert_called_once()
    call_kwargs = mock_agent.execute.call_args
    assert call_kwargs.kwargs.get("use_tools") is False


@pytest.mark.asyncio
@patch("app.core.tools.delegation_tools.agent_registry")
async def test_delegate_passes_correct_context(mock_registry: Any) -> None:
    """delegate_to_agent passes db, brain, venture, user_id to target agent."""
    mock_agent = _make_mock_agent()
    mock_registry.get.return_value = mock_agent

    ctx = _make_ctx()

    await handle_delegate_to_agent(
        {"target_agent": "pre-mortem-critic", "prompt": "Analyze risks"},
        ctx,
    )

    call_kwargs = mock_agent.execute.call_args.kwargs
    assert call_kwargs["brain"] is ctx.brain
    assert call_kwargs["db"] is ctx.db
    assert call_kwargs["venture"] is ctx.venture
    assert call_kwargs["user_id"] == ctx.user_id


# --------------------------------------------------------------------------- #
# Error cases
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_delegate_self_delegation_rejected() -> None:
    """delegate_to_agent rejects delegation to self."""
    ctx = _make_ctx(agent_id="venture-architect")

    result = await handle_delegate_to_agent(
        {"target_agent": "venture-architect", "prompt": "test"},
        ctx,
    )

    assert result["error"] is True
    assert "cannot delegate to itself" in result["message"]


@pytest.mark.asyncio
async def test_delegate_depth_limit_enforced() -> None:
    """delegate_to_agent rejects when delegation depth is at max."""
    ctx = _make_ctx(delegation_depth=MAX_DELEGATION_DEPTH)

    result = await handle_delegate_to_agent(
        {"target_agent": "pre-mortem-critic", "prompt": "test"},
        ctx,
    )

    assert result["error"] is True
    assert "depth limit" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.delegation_tools.agent_registry")
async def test_delegate_unknown_agent(mock_registry: Any) -> None:
    """delegate_to_agent returns error for non-existent agent."""
    mock_registry.get.return_value = None
    mock_registry.list_ids.return_value = [
        "venture-architect",
        "market-oracle",
        "pre-mortem-critic",
    ]

    ctx = _make_ctx()

    result = await handle_delegate_to_agent(
        {"target_agent": "nonexistent-agent", "prompt": "test"},
        ctx,
    )

    assert result["error"] is True
    assert "Unknown agent" in result["message"]
    assert "nonexistent-agent" in result["message"]
    assert "venture-architect" in result["message"]  # lists available agents


# --------------------------------------------------------------------------- #
# Routing plan validation
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@patch("app.core.tools.delegation_tools.agent_registry")
async def test_delegate_routing_plan_has_no_tools(mock_registry: Any) -> None:
    """Delegation routing plan has empty tools list."""
    mock_agent = _make_mock_agent()
    mock_registry.get.return_value = mock_agent

    ctx = _make_ctx()

    await handle_delegate_to_agent(
        {"target_agent": "pre-mortem-critic", "prompt": "test"},
        ctx,
    )

    call_kwargs = mock_agent.execute.call_args.kwargs
    routing_plan = call_kwargs["routing_plan"]
    assert routing_plan.tools == []
    assert routing_plan.selected_agent == "pre-mortem-critic"
    assert "Delegated from venture-architect" in routing_plan.reasoning


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@patch("app.core.tools.delegation_tools.agent_registry")
async def test_delegate_agent_execute_error_propagates(
    mock_registry: Any,
) -> None:
    """If target agent's execute raises, error is surfaced."""
    mock_agent = _make_mock_agent()
    mock_agent.execute = AsyncMock(side_effect=RuntimeError("LLM timeout"))
    mock_registry.get.return_value = mock_agent

    ctx = _make_ctx()

    # The ToolExecutor wraps this in try/except, but the handler itself
    # lets the exception propagate (executor handles it)
    with pytest.raises(RuntimeError, match="LLM timeout"):
        await handle_delegate_to_agent(
            {"target_agent": "pre-mortem-critic", "prompt": "test"},
            ctx,
        )


@pytest.mark.asyncio
async def test_delegate_depth_zero_allowed() -> None:
    """delegation_depth=0 (initial) should pass depth check."""
    ctx = _make_ctx(delegation_depth=0)

    # Self-delegation check runs first, so use a different agent
    # This just verifies depth=0 doesn't trigger depth guard
    # (the actual unknown-agent error comes after depth check)
    with patch("app.core.tools.delegation_tools.agent_registry") as mock_reg:
        mock_agent = _make_mock_agent()
        mock_reg.get.return_value = mock_agent

        result = await handle_delegate_to_agent(
            {"target_agent": "pre-mortem-critic", "prompt": "test"},
            ctx,
        )

        assert "error" not in result
        assert result["delegated_to"] == "pre-mortem-critic"
