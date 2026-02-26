"""Tool handlers for creating and updating structured artifacts."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import structlog

from app.core.artifacts.content_schemas import CONTENT_SCHEMA_MAP
from app.core.artifacts.manager import artifact_manager
from app.core.tools.registry import ToolDefinition, tool_registry
from app.models.artifact import ArtifactType

if TYPE_CHECKING:
    from app.core.tools.executor import ToolExecutor

logger = structlog.get_logger()

# Which artifact types each agent is allowed to create (mirrors AgentConfig)
_AGENT_ARTIFACT_TYPES: dict[str, list[str]] = {
    "venture-architect": ["lean_canvas", "research_brief"],
    "market-oracle": ["research_brief"],
    "storyteller": ["pitch_narrative"],
    "deck-architect": ["deck_outline"],
    "valuation-strategist": ["valuation_memo"],
    "lean-modeler": ["financial_model"],
    "kpi-dashboard": ["kpi_dashboard"],
    "pre-mortem-critic": ["research_brief"],
    "dataroom-concierge": ["dataroom_structure"],
    "icp-profiler": ["research_brief"],
}


# --------------------------------------------------------------------------- #
# Tool: create_artifact
# --------------------------------------------------------------------------- #

CREATE_ARTIFACT_DEF = ToolDefinition(
    name="create_artifact",
    description=(
        "Create a structured artifact (lean canvas, research brief, pitch "
        "narrative, deck outline, financial model, valuation memo, KPI "
        "dashboard, dataroom structure, board memo, or custom). The content "
        "must match the schema for the given artifact type. Returns the "
        "artifact ID and version."
    ),
    input_schema={
        "type": "object",
        "required": ["artifact_type", "title", "content"],
        "properties": {
            "artifact_type": {
                "type": "string",
                "enum": [t.value for t in ArtifactType],
                "description": "Type of artifact to create",
            },
            "title": {
                "type": "string",
                "description": "Human-readable title for the artifact",
            },
            "content": {
                "type": "object",
                "description": (
                    "Structured content matching the artifact type schema. "
                    "For lean_canvas: problem, solution, key_metrics, etc. "
                    "For research_brief: title, summary, sections. "
                    "For custom: title and body."
                ),
            },
        },
    },
)


async def handle_create_artifact(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Create a new artifact via the ArtifactManager."""
    artifact_type_raw = tool_input["artifact_type"]
    title = tool_input["title"]
    content = tool_input["content"]

    # Validate agent is allowed to create this artifact type
    allowed = _AGENT_ARTIFACT_TYPES.get(ctx.agent_id, [])
    if artifact_type_raw not in allowed and artifact_type_raw != "custom":
        return {
            "error": True,
            "message": (
                f"Agent '{ctx.agent_id}' is not allowed to create "
                f"'{artifact_type_raw}' artifacts. Allowed types: {allowed}"
            ),
        }

    artifact_type = ArtifactType(artifact_type_raw)

    # Validate content against schema if available
    schema_cls = CONTENT_SCHEMA_MAP.get(artifact_type)
    if schema_cls:
        try:
            schema_cls.model_validate(content)
        except Exception as exc:
            return {
                "error": True,
                "message": f"Content validation failed: {exc}",
            }

    artifact = await artifact_manager.create(
        db=ctx.db,
        workspace_id=ctx.venture.workspace_id,
        artifact_type=artifact_type,
        title=title,
        content=content,
        owner_agent=ctx.agent_id,
        created_by_id=uuid.UUID(ctx.user_id) if ctx.user_id else None,
    )

    return {
        "artifact_id": str(artifact.id),
        "title": artifact.title,
        "type": artifact.type.value,
        "version": artifact.current_version,
        "status": artifact.status.value,
    }


# --------------------------------------------------------------------------- #
# Tool: update_artifact
# --------------------------------------------------------------------------- #

UPDATE_ARTIFACT_DEF = ToolDefinition(
    name="update_artifact",
    description=(
        "Update the content of an existing artifact. Provide the artifact ID, "
        "the expected version (for optimistic locking), and new content. "
        "Returns the updated artifact metadata including new version number."
    ),
    input_schema={
        "type": "object",
        "required": ["artifact_id", "expected_version", "content"],
        "properties": {
            "artifact_id": {
                "type": "string",
                "description": "UUID of the artifact to update",
            },
            "expected_version": {
                "type": "integer",
                "description": (
                    "Current version number (for optimistic locking). "
                    "If the artifact has been modified since you last saw it, "
                    "this will fail with a conflict error."
                ),
            },
            "content": {
                "type": "object",
                "description": "New structured content for the artifact",
            },
        },
    },
)


async def handle_update_artifact(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Update an existing artifact via the ArtifactManager."""
    artifact_id_raw = tool_input["artifact_id"]
    expected_version = tool_input["expected_version"]
    content = tool_input["content"]

    try:
        artifact_id = uuid.UUID(artifact_id_raw)
    except ValueError:
        return {"error": True, "message": f"Invalid artifact ID: {artifact_id_raw}"}

    # Fetch current artifact to validate type and workspace
    current = await artifact_manager.get(ctx.db, artifact_id)
    if current is None:
        return {"error": True, "message": "Artifact not found"}

    # Ensure artifact belongs to the same workspace as the venture
    if current.workspace_id != ctx.venture.workspace_id:
        return {"error": True, "message": "Artifact not in current workspace"}

    # Validate content against schema if available
    schema_cls = CONTENT_SCHEMA_MAP.get(current.type)
    if schema_cls:
        try:
            schema_cls.model_validate(content)
        except Exception as exc:
            return {
                "error": True,
                "message": f"Content validation failed: {exc}",
            }

    try:
        artifact = await artifact_manager.update(
            db=ctx.db,
            artifact_id=artifact_id,
            content=content,
            expected_version=expected_version,
            created_by=f"agent:{ctx.agent_id}",
        )
    except Exception as exc:
        return {"error": True, "message": str(exc)}

    return {
        "artifact_id": str(artifact.id),
        "title": artifact.title,
        "type": artifact.type.value,
        "version": artifact.current_version,
        "status": artifact.status.value,
    }


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

def register_artifact_tools() -> None:
    """Register artifact tools with the global tool registry."""
    tool_registry.register(CREATE_ARTIFACT_DEF, handle_create_artifact)
    tool_registry.register(UPDATE_ARTIFACT_DEF, handle_update_artifact)
