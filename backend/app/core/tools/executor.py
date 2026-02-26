"""Tool executor — dispatches tool calls with context injection."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

import structlog

from app.core.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.brain.startup_brain import StartupBrain
    from app.models.venture import Venture

logger = structlog.get_logger()


class ToolExecutor:
    """Executes tool calls within an agent's execution context.

    Created per agent.execute() invocation with the current DB session,
    brain, venture, and user context injected.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        db: AsyncSession,
        brain: StartupBrain,
        venture: Venture,
        user_id: str,
        agent_id: str = "",
        delegation_depth: int = 0,
    ) -> None:
        self.registry = registry
        self.db = db
        self.brain = brain
        self.venture = venture
        self.user_id = user_id
        self.agent_id = agent_id
        self.delegation_depth = delegation_depth
        self._cache: dict[str, dict[str, Any]] = {}

    async def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a tool call, returning the result dict.

        Handles errors gracefully — tool failures are returned as error dicts
        so Claude can adjust its approach rather than crashing the agent.
        """
        entry = self.registry.get_entry(tool_name)
        if entry is None:
            return {"error": True, "message": f"Unknown tool: {tool_name}"}

        # Check cache (same tool + same input = same result within one execution)
        cache_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True, default=str)}"
        if cache_key in self._cache:
            logger.debug("tool_cache_hit", tool=tool_name)
            return self._cache[cache_key]

        timeout = entry.definition.timeout_seconds

        try:
            result = await asyncio.wait_for(
                entry.handler(tool_input, self),
                timeout=timeout,
            )
        except TimeoutError:
            logger.warning("tool_timeout", tool=tool_name, timeout=timeout)
            return {
                "error": True,
                "message": f"Tool '{tool_name}' timed out after {timeout}s",
            }
        except Exception as exc:
            logger.error("tool_execution_failed", tool=tool_name, error=str(exc))
            return {
                "error": True,
                "message": f"Tool '{tool_name}' failed: {str(exc)}",
            }

        self._cache[cache_key] = result
        logger.info("tool_executed", tool=tool_name, result_keys=list(result.keys()))
        return result
