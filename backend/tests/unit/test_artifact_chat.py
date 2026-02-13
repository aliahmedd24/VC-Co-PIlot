from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(
    client: AsyncClient, email: str = "artchat@example.com"
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepass123", "name": "Test"},
    )
    token: str = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_workspace(
    client: AsyncClient, headers: dict[str, str]
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Artifact Chat WS"},
        headers=headers,
    )
    result: dict[str, Any] = response.json()
    return result


async def _create_artifact(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/artifacts",
        json={
            "workspace_id": workspace_id,
            "type": "lean_canvas",
            "title": "Test Canvas",
            "content": {"problem": ["High CAC"]},
        },
        headers=headers,
    )
    result: dict[str, Any] = response.json()
    return result


async def _send_artifact_chat(
    client: AsyncClient,
    headers: dict[str, str],
    artifact_id: str,
    content: str = "Please refine the problem section.",
    agent_response_text: str = "Here's my refinement.",
) -> Any:
    """Send an artifact chat message with all external services mocked."""
    with (
        patch("app.core.agents.base.embedding_service") as mock_embed,
        patch("app.core.brain.startup_brain.startup_brain.rag") as mock_rag,
    ):
        mock_embed.embed_text.return_value = [0.1] * 1536
        mock_rag.search = AsyncMock(return_value=[])

        mock_client = AsyncMock()
        content_block = MagicMock()
        content_block.text = agent_response_text
        mock_response = MagicMock()
        mock_response.content = [content_block]
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch(
            "app.core.agents.base.BaseAgent._get_client",
            return_value=mock_client,
        ):
            response = await client.post(
                f"/api/v1/artifacts/{artifact_id}/chat",
                json={"content": content},
                headers=headers,
            )

    return response


@pytest.mark.asyncio
async def test_artifact_chat_creates_message(client: AsyncClient) -> None:
    """POST /artifacts/{id}/chat creates user and assistant messages."""
    headers = await _register_and_get_headers(client, "achat1@test.com")
    ws = await _create_workspace(client, headers)
    artifact = await _create_artifact(client, headers, ws["id"])

    response = await _send_artifact_chat(
        client, headers, artifact["id"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_message"]["content"] == "Please refine the problem section."
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"
    assert len(data["assistant_message"]["content"]) > 0


@pytest.mark.asyncio
async def test_artifact_chat_updates_artifact(client: AsyncClient) -> None:
    """When agent returns ARTIFACT_CONTENT marker, artifact gets updated."""
    headers = await _register_and_get_headers(client, "achat2@test.com")
    ws = await _create_workspace(client, headers)
    artifact = await _create_artifact(client, headers, ws["id"])

    # Agent response with artifact content marker
    agent_text = (
        'I have refined the problem section. '
        '<!-- ARTIFACT_CONTENT: {"problem": ["High CAC", "Low retention"]} -->'
    )
    response = await _send_artifact_chat(
        client, headers, artifact["id"], agent_response_text=agent_text
    )

    assert response.status_code == 200

    # Verify artifact was updated
    get_resp = await client.get(
        f"/api/v1/artifacts/{artifact['id']}",
        headers=headers,
    )
    updated = get_resp.json()
    assert updated["content"] == {"problem": ["High CAC", "Low retention"]}
    assert updated["current_version"] == 2


@pytest.mark.asyncio
async def test_artifact_chat_routes_to_owner_agent(client: AsyncClient) -> None:
    """Artifact chat routes to the artifact's owner_agent."""
    headers = await _register_and_get_headers(client, "achat3@test.com")
    ws = await _create_workspace(client, headers)
    artifact = await _create_artifact(client, headers, ws["id"])

    response = await _send_artifact_chat(
        client, headers, artifact["id"]
    )

    assert response.status_code == 200
    data = response.json()
    # Owner agent is venture-architect (set by create_artifact route)
    assert data["routing_plan"]["selected_agent"] is not None
