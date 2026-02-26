"""Tests for the load_skill_reference tool handler."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.tools.registry import AGENT_TOOL_MAP
from app.core.tools.skill_tools import handle_load_skill_reference

_ALL_AGENT_IDS = [
    "venture-architect",
    "valuation-strategist",
    "market-oracle",
    "pre-mortem-critic",
    "deck-architect",
    "storyteller",
    "lean-modeler",
    "kpi-dashboard",
    "qa-simulator",
    "dataroom-concierge",
    "icp-profiler",
]


def _make_ctx(agent_id: str = "venture-architect") -> MagicMock:
    """Create a mock ToolExecutor context with agent_id set."""
    ctx = MagicMock()
    ctx.agent_id = agent_id
    return ctx


# ------------------------------------------------------------------ #
# load_skill_reference handler
# ------------------------------------------------------------------ #


@pytest.mark.asyncio()
async def test_load_skill_reference_list() -> None:
    """List action should return available references."""
    ctx = _make_ctx("venture-architect")
    result = await handle_load_skill_reference({"action": "list"}, ctx)
    assert result["count"] >= 2
    assert "lean_canvas_guide.md" in result["available_references"]


@pytest.mark.asyncio()
async def test_load_skill_reference_load_success() -> None:
    """Load action with valid reference should return content."""
    ctx = _make_ctx("venture-architect")
    result = await handle_load_skill_reference(
        {"action": "load", "reference_name": "lean_canvas_guide.md"}, ctx,
    )
    assert "content" in result
    assert "Lean Canvas" in result["content"]


@pytest.mark.asyncio()
async def test_load_skill_reference_not_found() -> None:
    """Load action with missing reference should return error."""
    ctx = _make_ctx("venture-architect")
    result = await handle_load_skill_reference(
        {"action": "load", "reference_name": "nonexistent.md"}, ctx,
    )
    assert "error" in result


@pytest.mark.asyncio()
async def test_load_skill_reference_path_traversal_blocked() -> None:
    """Path traversal in reference_name should be blocked."""
    ctx = _make_ctx("venture-architect")
    result = await handle_load_skill_reference(
        {"action": "load", "reference_name": "../../../etc/passwd"}, ctx,
    )
    # Should either return error or not found, but NOT file content
    assert "error" in result or result.get("content") is None


# ------------------------------------------------------------------ #
# Registration
# ------------------------------------------------------------------ #


@pytest.mark.parametrize("agent_id", _ALL_AGENT_IDS)
def test_skill_tools_registered_in_agent_map(agent_id: str) -> None:
    """Every agent should have load_skill_reference in AGENT_TOOL_MAP."""
    tools = AGENT_TOOL_MAP.get(agent_id, [])
    assert "load_skill_reference" in tools, (
        f"load_skill_reference missing from AGENT_TOOL_MAP for {agent_id}"
    )
