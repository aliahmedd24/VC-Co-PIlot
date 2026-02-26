"""Tool handler for inter-agent delegation (delegate_to_agent)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.core.agents.registry import agent_registry
from app.core.router.types import ModelProfile, RoutingPlan
from app.core.tools.registry import ToolDefinition, tool_registry

if TYPE_CHECKING:
    from app.core.tools.executor import ToolExecutor

logger = structlog.get_logger()

MAX_DELEGATION_DEPTH = 1


# --------------------------------------------------------------------------- #
# Tool: delegate_to_agent
# --------------------------------------------------------------------------- #

DELEGATE_TO_AGENT_DEF = ToolDefinition(
    name="delegate_to_agent",
    description=(
        "Delegate a focused sub-task to another specialist agent. The target "
        "agent receives the venture context and your prompt, then returns its "
        "analysis. Use this when another agent's expertise would strengthen "
        "your response (e.g., ask Pre-Mortem Critic for risk analysis, or "
        "Market Oracle for competitive intelligence). The delegated agent "
        "cannot use tools or delegate further."
    ),
    input_schema={
        "type": "object",
        "required": ["target_agent", "prompt"],
        "properties": {
            "target_agent": {
                "type": "string",
                "description": (
                    "The agent ID to delegate to. Available agents: "
                    "venture-architect, market-oracle, storyteller, "
                    "deck-architect, valuation-strategist, lean-modeler, "
                    "kpi-dashboard, qa-simulator, dataroom-concierge, "
                    "icp-profiler, pre-mortem-critic"
                ),
            },
            "prompt": {
                "type": "string",
                "description": (
                    "A focused, specific prompt for the target agent. "
                    "Include context about what you need and why."
                ),
            },
        },
    },
    timeout_seconds=60.0,
    max_result_chars=8000,
)


async def handle_delegate_to_agent(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Delegate a sub-task to another agent.

    The target agent runs WITHOUT tools and cannot delegate further,
    preventing infinite delegation chains.
    """
    target_agent_id = tool_input["target_agent"]
    prompt = tool_input["prompt"]

    # Prevent self-delegation
    if target_agent_id == ctx.agent_id:
        return {
            "error": True,
            "message": "An agent cannot delegate to itself.",
        }

    # Enforce recursion guard
    if ctx.delegation_depth >= MAX_DELEGATION_DEPTH:
        return {
            "error": True,
            "message": (
                f"Delegation depth limit reached ({MAX_DELEGATION_DEPTH}). "
                "Delegated agents cannot delegate further."
            ),
        }

    # Look up target agent
    target_agent = agent_registry.get(target_agent_id)
    if target_agent is None:
        available = agent_registry.list_ids()
        return {
            "error": True,
            "message": (
                f"Unknown agent: '{target_agent_id}'. "
                f"Available agents: {', '.join(available)}"
            ),
        }

    # Build a lightweight routing plan for the delegated execution
    delegation_plan = RoutingPlan(
        selected_agent=target_agent_id,
        model_profile=ModelProfile.DEFAULT,
        tools=[],
        artifact_needed=False,
        fallback_agent=ctx.agent_id,
        confidence=1.0,
        reasoning=f"Delegated from {ctx.agent_id}",
        latency_ms=0.0,
    )

    logger.info(
        "agent_delegation",
        from_agent=ctx.agent_id,
        to_agent=target_agent_id,
        depth=ctx.delegation_depth + 1,
        prompt_preview=prompt[:100],
    )

    # Execute target agent WITHOUT tools (use_tools=False)
    response = await target_agent.execute(
        prompt=prompt,
        brain=ctx.brain,
        db=ctx.db,
        venture=ctx.venture,
        routing_plan=delegation_plan,
        session_id="",
        user_id=ctx.user_id,
        use_tools=False,
    )

    return {
        "delegated_to": target_agent_id,
        "agent_name": target_agent.config.name,
        "content": response.content,
        "citations": response.citations,
    }


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

def register_delegation_tools() -> None:
    """Register the delegation tool with the global tool registry."""
    tool_registry.register(DELEGATE_TO_AGENT_DEF, handle_delegate_to_agent)
