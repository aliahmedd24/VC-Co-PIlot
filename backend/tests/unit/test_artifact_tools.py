"""Tests for the artifact tool handlers (create_artifact, update_artifact)."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.tools.artifact_tools import (
    handle_create_artifact,
    handle_update_artifact,
)
from app.models.artifact import ArtifactStatus, ArtifactType


def _make_ctx(agent_id: str = "venture-architect") -> Any:
    """Create a mock ToolExecutor context."""
    ctx = MagicMock()
    ctx.venture.id = uuid.uuid4()
    ctx.venture.workspace_id = uuid.uuid4()
    ctx.user_id = str(uuid.uuid4())
    ctx.agent_id = agent_id
    ctx.db = AsyncMock()
    ctx.brain = MagicMock()
    return ctx


def _make_artifact(
    workspace_id: uuid.UUID,
    artifact_type: ArtifactType = ArtifactType.LEAN_CANVAS,
    version: int = 1,
) -> Any:
    """Create a mock Artifact."""
    artifact = MagicMock()
    artifact.id = uuid.uuid4()
    artifact.workspace_id = workspace_id
    artifact.type = artifact_type
    artifact.title = "Test Artifact"
    artifact.status = ArtifactStatus.DRAFT
    artifact.current_version = version
    artifact.content = {"problem": ["test"]}
    return artifact


# Valid lean canvas content matching LeanCanvasContent schema
_VALID_LEAN_CANVAS = {
    "problem": ["No solution exists"],
    "solution": ["Build one"],
    "key_metrics": ["ARR", "Churn"],
    "unique_value_prop": "Best in class",
    "unfair_advantage": "Patents",
    "channels": ["Direct"],
    "customer_segments": ["Enterprise"],
    "cost_structure": ["Engineering"],
    "revenue_streams": ["SaaS"],
}


# --------------------------------------------------------------------------- #
# create_artifact
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@patch("app.core.tools.artifact_tools.artifact_manager")
async def test_create_artifact_success(mock_manager: Any) -> None:
    """create_artifact creates artifact and returns metadata."""
    ctx = _make_ctx("venture-architect")
    artifact = _make_artifact(ctx.venture.workspace_id)
    mock_manager.create = AsyncMock(return_value=artifact)

    result = await handle_create_artifact(
        {
            "artifact_type": "lean_canvas",
            "title": "My Lean Canvas",
            "content": _VALID_LEAN_CANVAS,
        },
        ctx,
    )

    assert result["artifact_id"] == str(artifact.id)
    assert result["version"] == artifact.current_version
    mock_manager.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_artifact_unauthorized_type() -> None:
    """create_artifact rejects artifact types the agent isn't allowed to create."""
    ctx = _make_ctx("storyteller")  # can only create pitch_narrative

    result = await handle_create_artifact(
        {
            "artifact_type": "lean_canvas",
            "title": "Not Allowed",
            "content": {},
        },
        ctx,
    )

    assert result["error"] is True
    assert "not allowed" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.artifact_tools.artifact_manager")
async def test_create_artifact_custom_type_any_agent(mock_manager: Any) -> None:
    """Any agent can create 'custom' artifacts."""
    ctx = _make_ctx("qa-simulator")  # normally can_create_artifacts = []
    artifact = _make_artifact(ctx.venture.workspace_id, ArtifactType.CUSTOM)
    mock_manager.create = AsyncMock(return_value=artifact)

    result = await handle_create_artifact(
        {
            "artifact_type": "custom",
            "title": "Custom Doc",
            "content": {"title": "Custom", "body": "Some content"},
        },
        ctx,
    )

    assert "error" not in result
    assert result["type"] == "custom"


@pytest.mark.asyncio
async def test_create_artifact_invalid_content() -> None:
    """create_artifact rejects content with wrong field types."""
    ctx = _make_ctx("venture-architect")

    # problem must be list[str], not str
    result = await handle_create_artifact(
        {
            "artifact_type": "lean_canvas",
            "title": "Bad Content",
            "content": {"problem": "a string, not a list"},
        },
        ctx,
    )

    assert result["error"] is True
    assert "validation failed" in result["message"].lower()


# --------------------------------------------------------------------------- #
# update_artifact
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@patch("app.core.tools.artifact_tools.artifact_manager")
async def test_update_artifact_success(mock_manager: Any) -> None:
    """update_artifact updates content with proper version."""
    ctx = _make_ctx()
    artifact = _make_artifact(ctx.venture.workspace_id, version=2)
    mock_manager.get = AsyncMock(return_value=artifact)
    updated = _make_artifact(ctx.venture.workspace_id, version=3)
    mock_manager.update = AsyncMock(return_value=updated)

    result = await handle_update_artifact(
        {
            "artifact_id": str(artifact.id),
            "expected_version": 2,
            "content": _VALID_LEAN_CANVAS,
        },
        ctx,
    )

    assert result["version"] == 3
    mock_manager.update.assert_called_once()


@pytest.mark.asyncio
@patch("app.core.tools.artifact_tools.artifact_manager")
async def test_update_artifact_not_found(mock_manager: Any) -> None:
    """update_artifact returns error when artifact doesn't exist."""
    ctx = _make_ctx()
    mock_manager.get = AsyncMock(return_value=None)

    result = await handle_update_artifact(
        {
            "artifact_id": str(uuid.uuid4()),
            "expected_version": 1,
            "content": _VALID_LEAN_CANVAS,
        },
        ctx,
    )

    assert result["error"] is True
    assert "not found" in result["message"].lower()


@pytest.mark.asyncio
@patch("app.core.tools.artifact_tools.artifact_manager")
async def test_update_artifact_wrong_workspace(mock_manager: Any) -> None:
    """update_artifact rejects updates to artifacts in other workspaces."""
    ctx = _make_ctx()
    other_workspace = uuid.uuid4()
    artifact = _make_artifact(other_workspace)
    mock_manager.get = AsyncMock(return_value=artifact)

    result = await handle_update_artifact(
        {
            "artifact_id": str(artifact.id),
            "expected_version": 1,
            "content": _VALID_LEAN_CANVAS,
        },
        ctx,
    )

    assert result["error"] is True
    assert "workspace" in result["message"].lower()


@pytest.mark.asyncio
async def test_update_artifact_invalid_uuid() -> None:
    """update_artifact returns error for invalid artifact IDs."""
    ctx = _make_ctx()

    result = await handle_update_artifact(
        {
            "artifact_id": "not-a-uuid",
            "expected_version": 1,
            "content": {},
        },
        ctx,
    )

    assert result["error"] is True
    assert "Invalid artifact ID" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.artifact_tools.artifact_manager")
async def test_update_artifact_version_conflict(mock_manager: Any) -> None:
    """update_artifact returns error on version conflict."""
    ctx = _make_ctx()
    artifact = _make_artifact(ctx.venture.workspace_id, version=1)
    mock_manager.get = AsyncMock(return_value=artifact)
    mock_manager.update = AsyncMock(
        side_effect=Exception("Version conflict: expected 1, current is 2"),
    )

    result = await handle_update_artifact(
        {
            "artifact_id": str(artifact.id),
            "expected_version": 1,
            "content": _VALID_LEAN_CANVAS,
        },
        ctx,
    )

    assert result["error"] is True
    assert "conflict" in result["message"].lower()
