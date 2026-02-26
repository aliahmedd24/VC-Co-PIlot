"""Tool handler for the load_skill_reference agent tool."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.skills.skill_loader import skill_loader
from app.core.tools.registry import ToolDefinition, tool_registry

if TYPE_CHECKING:
    from app.core.tools.executor import ToolExecutor


# --------------------------------------------------------------------------- #
# Tool: load_skill_reference
# --------------------------------------------------------------------------- #

LOAD_SKILL_REFERENCE_DEF = ToolDefinition(
    name="load_skill_reference",
    description=(
        "Load detailed domain reference material for deeper analysis. "
        "Use this when you need step-by-step guides, detailed frameworks, "
        "templates, or extended reference data beyond your core expertise. "
        "Call list mode first to see available references, then load by path."
    ),
    input_schema={
        "type": "object",
        "required": ["action"],
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "load"],
                "description": (
                    "'list' to see available references for your agent, "
                    "'load' to retrieve a specific reference file."
                ),
            },
            "reference_name": {
                "type": "string",
                "description": (
                    "Filename of the reference to load (e.g. 'lean_canvas_guide.md'). "
                    "Required when action is 'load'."
                ),
            },
        },
    },
    max_result_chars=12000,
)


async def handle_load_skill_reference(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Handle the load_skill_reference tool call."""
    action = tool_input.get("action", "list")
    agent_id = ctx.agent_id

    if action == "list":
        refs = skill_loader.list_references(agent_id)
        return {
            "agent_id": agent_id,
            "available_references": refs,
            "count": len(refs),
        }

    # action == "load"
    ref_name = tool_input.get("reference_name", "")
    if not ref_name:
        return {"error": "reference_name is required when action is 'load'"}

    # Build the full relative path for the loader
    ref_path = f"{agent_id}/references/{ref_name}"
    content = skill_loader.load_reference(ref_path)
    if content is None:
        return {
            "error": f"Reference '{ref_name}' not found for agent '{agent_id}'.",
            "available": skill_loader.list_references(agent_id),
        }
    return {
        "reference_name": ref_name,
        "content": content,
    }


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

def register_skill_tools() -> None:
    """Register the skill reference tool with the global tool registry."""
    tool_registry.register(LOAD_SKILL_REFERENCE_DEF, handle_load_skill_reference)
