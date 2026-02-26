"""Tests for ToolRegistry, ToolExecutor, and tool registration."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.tools.executor import ToolExecutor
from app.core.tools.registry import (
    AGENT_TOOL_MAP,
    ToolDefinition,
    ToolRegistry,
)

# --------------------------------------------------------------------------- #
# ToolRegistry tests
# --------------------------------------------------------------------------- #


def test_registry_register_and_list() -> None:
    """Registered tools appear in list_tools."""
    registry = ToolRegistry()
    defn = ToolDefinition(
        name="test_tool",
        description="A test tool",
        input_schema={"type": "object", "properties": {}},
    )
    handler: Any = AsyncMock(return_value={"ok": True})
    registry.register(defn, handler)
    assert "test_tool" in registry.list_tools()


def test_registry_get_entry() -> None:
    """get_entry returns the correct ToolEntry."""
    registry = ToolRegistry()
    defn = ToolDefinition(
        name="my_tool",
        description="desc",
        input_schema={"type": "object"},
    )
    handler: Any = AsyncMock(return_value={})
    registry.register(defn, handler)
    entry = registry.get_entry("my_tool")
    assert entry is not None
    assert entry.definition.name == "my_tool"
    assert entry.handler is handler


def test_registry_get_entry_missing() -> None:
    """get_entry returns None for unregistered tools."""
    registry = ToolRegistry()
    assert registry.get_entry("nonexistent") is None


def test_registry_get_tools_for_agent() -> None:
    """get_tools_for_agent returns Claude-format dicts for mapped tools."""
    registry = ToolRegistry()
    defn = ToolDefinition(
        name="run_valuation",
        description="Run valuation",
        input_schema={"type": "object", "properties": {"revenue": {"type": "number"}}},
    )
    registry.register(defn, AsyncMock(return_value={}))

    tools = registry.get_tools_for_agent("valuation-strategist")
    # valuation-strategist has run_valuation in AGENT_TOOL_MAP
    assert any(t["name"] == "run_valuation" for t in tools)


def test_registry_get_tools_for_agent_no_mapping() -> None:
    """Agent with no mapping returns empty list."""
    registry = ToolRegistry()
    assert registry.get_tools_for_agent("unknown-agent") == []


def test_registry_get_tool_names_for_agent() -> None:
    """get_tool_names_for_agent returns only registered tool names."""
    registry = ToolRegistry()
    defn = ToolDefinition(
        name="query_entities",
        description="Query KG",
        input_schema={"type": "object"},
    )
    registry.register(defn, AsyncMock(return_value={}))

    # venture-architect has query_entities in AGENT_TOOL_MAP
    names = registry.get_tool_names_for_agent("venture-architect")
    assert "query_entities" in names


def test_registry_truncate_result() -> None:
    """_truncate_result limits output to max_result_chars."""
    registry = ToolRegistry()
    defn = ToolDefinition(
        name="big_tool",
        description="desc",
        input_schema={"type": "object"},
        max_result_chars=50,
    )
    registry.register(defn, AsyncMock(return_value={}))

    large_result = {"data": "x" * 100}
    truncated = registry._truncate_result("big_tool", large_result)
    assert len(truncated) <= 50 + len("... [truncated]")
    assert truncated.endswith("... [truncated]")


def test_agent_tool_map_all_agents_present() -> None:
    """AGENT_TOOL_MAP has entries for all 11 agents."""
    expected = {
        "valuation-strategist",
        "lean-modeler",
        "kpi-dashboard",
        "market-oracle",
        "venture-architect",
        "pre-mortem-critic",
        "dataroom-concierge",
        "icp-profiler",
        "storyteller",
        "deck-architect",
        "qa-simulator",
    }
    assert set(AGENT_TOOL_MAP.keys()) == expected


# --------------------------------------------------------------------------- #
# ToolExecutor tests
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_executor_execute_success() -> None:
    """Executor calls handler and returns result."""
    registry = ToolRegistry()
    handler = AsyncMock(return_value={"value": 42})
    defn = ToolDefinition(
        name="simple_tool",
        description="Simple",
        input_schema={"type": "object"},
    )
    registry.register(defn, handler)

    executor = ToolExecutor(
        registry=registry,
        db=MagicMock(),
        brain=MagicMock(),
        venture=MagicMock(),
        user_id="user-1",
    )
    result = await executor.execute("simple_tool", {"x": 1})
    assert result == {"value": 42}
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_executor_unknown_tool() -> None:
    """Executor returns error dict for unknown tools."""
    registry = ToolRegistry()
    executor = ToolExecutor(
        registry=registry,
        db=MagicMock(),
        brain=MagicMock(),
        venture=MagicMock(),
        user_id="user-1",
    )
    result = await executor.execute("missing_tool", {})
    assert result["error"] is True
    assert "Unknown tool" in result["message"]


@pytest.mark.asyncio
async def test_executor_handler_error() -> None:
    """Executor returns error dict when handler raises."""
    registry = ToolRegistry()
    handler = AsyncMock(side_effect=ValueError("bad input"))
    defn = ToolDefinition(
        name="failing_tool",
        description="Fails",
        input_schema={"type": "object"},
    )
    registry.register(defn, handler)

    executor = ToolExecutor(
        registry=registry,
        db=MagicMock(),
        brain=MagicMock(),
        venture=MagicMock(),
        user_id="user-1",
    )
    result = await executor.execute("failing_tool", {})
    assert result["error"] is True
    assert "bad input" in result["message"]


@pytest.mark.asyncio
async def test_executor_caching() -> None:
    """Executor caches results for identical tool+input."""
    registry = ToolRegistry()
    handler = AsyncMock(return_value={"cached": True})
    defn = ToolDefinition(
        name="cached_tool",
        description="Cached",
        input_schema={"type": "object"},
    )
    registry.register(defn, handler)

    executor = ToolExecutor(
        registry=registry,
        db=MagicMock(),
        brain=MagicMock(),
        venture=MagicMock(),
        user_id="user-1",
    )

    result1 = await executor.execute("cached_tool", {"a": 1})
    result2 = await executor.execute("cached_tool", {"a": 1})
    assert result1 == result2
    # Handler called only once due to cache
    assert handler.call_count == 1


@pytest.mark.asyncio
async def test_executor_timeout() -> None:
    """Executor returns error for slow tools."""
    import asyncio

    registry = ToolRegistry()

    async def slow_handler(tool_input: dict[str, Any], ctx: Any) -> dict[str, Any]:
        await asyncio.sleep(5)
        return {}

    defn = ToolDefinition(
        name="slow_tool",
        description="Slow",
        input_schema={"type": "object"},
        timeout_seconds=0.1,
    )
    registry.register(defn, slow_handler)

    executor = ToolExecutor(
        registry=registry,
        db=MagicMock(),
        brain=MagicMock(),
        venture=MagicMock(),
        user_id="user-1",
    )
    result = await executor.execute("slow_tool", {})
    assert result["error"] is True
    assert "timed out" in result["message"]
