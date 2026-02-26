"""Tool registry and definitions for the agent tool calling system."""

from __future__ import annotations

import json
from collections.abc import Callable, Coroutine
from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

# Handler type: async function(tool_input, ToolExecutor) -> dict
ToolHandler = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


class ToolDefinition(BaseModel):
    """Definition of a tool that agents can call via Claude's tool_use API."""

    name: str
    description: str
    input_schema: dict[str, Any]
    timeout_seconds: float = 30.0
    max_result_chars: int = 8000

    model_config = {"arbitrary_types_allowed": True}


class ToolEntry:
    """Internal registry entry pairing a definition with its handler."""

    __slots__ = ("definition", "handler")

    def __init__(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        self.definition = definition
        self.handler = handler


# Which tools each agent has access to
AGENT_TOOL_MAP: dict[str, list[str]] = {
    "valuation-strategist": [
        "run_valuation",
        "model_scenario",
        "rank_benchmarks",
        "match_success_stories",
        "query_entities",
        "detect_data_gaps",
        "search_brain",
        "create_artifact",
        "update_artifact",
        "generate_document",
        "load_skill_reference",
    ],
    "lean-modeler": [
        "run_valuation",
        "model_scenario",
        "rank_benchmarks",
        "query_entities",
        "create_artifact",
        "update_artifact",
        "generate_document",
        "load_skill_reference",
    ],
    "kpi-dashboard": [
        "rank_benchmarks",
        "score_readiness",
        "query_entities",
        "detect_data_gaps",
        "create_artifact",
        "update_artifact",
        "generate_document",
        "load_skill_reference",
    ],
    "market-oracle": [
        "query_entities",
        "traverse_relations",
        "match_success_stories",
        "rank_benchmarks",
        "search_brain",
        "web_search",
        "fetch_url",
        "delegate_to_agent",
        "create_artifact",
        "update_artifact",
        "generate_document",
        "load_skill_reference",
    ],
    "venture-architect": [
        "run_valuation",
        "score_readiness",
        "query_entities",
        "detect_data_gaps",
        "search_brain",
        "delegate_to_agent",
        "create_artifact",
        "update_artifact",
        "generate_document",
        "load_skill_reference",
    ],
    "pre-mortem-critic": [
        "query_entities",
        "traverse_relations",
        "score_readiness",
        "detect_data_gaps",
        "web_search",
        "delegate_to_agent",
        "create_artifact",
        "update_artifact",
        "load_skill_reference",
    ],
    "dataroom-concierge": [
        "score_readiness",
        "query_entities",
        "detect_data_gaps",
        "create_artifact",
        "update_artifact",
        "generate_document",
        "load_skill_reference",
    ],
    "icp-profiler": [
        "query_entities",
        "traverse_relations",
        "rank_benchmarks",
        "search_brain",
        "web_search",
        "fetch_url",
        "create_artifact",
        "update_artifact",
        "load_skill_reference",
    ],
    "storyteller": [
        "query_entities",
        "match_success_stories",
        "delegate_to_agent",
        "create_artifact",
        "update_artifact",
        "generate_document",
        "load_skill_reference",
    ],
    "deck-architect": [
        "run_valuation",
        "rank_benchmarks",
        "query_entities",
        "match_success_stories",
        "delegate_to_agent",
        "create_artifact",
        "update_artifact",
        "generate_presentation",
        "load_skill_reference",
    ],
    "qa-simulator": [
        "query_entities",
        "detect_data_gaps",
        "score_readiness",
        "load_skill_reference",
    ],
}


class ToolRegistry:
    """Singleton registry of all available agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        """Register a tool with its handler."""
        self._tools[definition.name] = ToolEntry(definition, handler)
        logger.debug("tool_registered", tool=definition.name)

    def get_entry(self, tool_name: str) -> ToolEntry | None:
        """Get a tool entry by name."""
        return self._tools.get(tool_name)

    def get_tools_for_agent(self, agent_id: str) -> list[dict[str, Any]]:
        """Return Claude-format tool definitions for a given agent."""
        tool_names = AGENT_TOOL_MAP.get(agent_id, [])
        claude_tools: list[dict[str, Any]] = []
        for name in tool_names:
            entry = self._tools.get(name)
            if entry is not None:
                claude_tools.append({
                    "name": entry.definition.name,
                    "description": entry.definition.description,
                    "input_schema": entry.definition.input_schema,
                })
        return claude_tools

    def get_tool_names_for_agent(self, agent_id: str) -> list[str]:
        """Return tool names available for a given agent."""
        all_names = AGENT_TOOL_MAP.get(agent_id, [])
        return [n for n in all_names if n in self._tools]

    def list_tools(self) -> list[str]:
        """Return all registered tool names."""
        return list(self._tools.keys())

    def _truncate_result(self, tool_name: str, result: dict[str, Any]) -> str:
        """Serialize and truncate a tool result to fit token budget."""
        entry = self._tools.get(tool_name)
        max_chars = entry.definition.max_result_chars if entry else 8000
        raw = json.dumps(result, default=str)
        if len(raw) > max_chars:
            return raw[:max_chars] + '... [truncated]'
        return raw


# Global singleton
tool_registry = ToolRegistry()
