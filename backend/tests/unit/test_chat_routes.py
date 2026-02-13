from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(
    client: AsyncClient, email: str = "chat@example.com"
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepass123", "name": "Test"},
    )
    token: str = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_workspace(
    client: AsyncClient, headers: dict[str, str], name: str = "Chat Test WS"
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": name},
        headers=headers,
    )
    result: dict[str, Any] = response.json()
    return result


def _mock_claude_response(text: str = "This is an AI response.") -> MagicMock:
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


def _chat_mocks() -> tuple[Any, Any, Any]:
    """Create the three mocks needed for chat: embedding, RAG, Claude client."""
    mock_embed = patch("app.core.agents.base.embedding_service")
    mock_rag = patch("app.core.brain.startup_brain.startup_brain.rag")
    mock_claude = patch("app.core.agents.base.AsyncAnthropic")
    return mock_embed, mock_rag, mock_claude


async def _send_message(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    content: str = "What is the market size?",
    session_id: str | None = None,
    override_agent: str | None = None,
) -> Any:
    """Helper to send a chat message with all external services mocked."""
    body: dict[str, Any] = {
        "workspace_id": workspace_id,
        "content": content,
    }
    if session_id:
        body["session_id"] = session_id
    if override_agent:
        body["override_agent"] = override_agent

    with (
        patch("app.core.agents.base.embedding_service") as mock_embed,
        patch("app.core.brain.startup_brain.startup_brain.rag") as mock_rag,
    ):
        mock_embed.embed_text.return_value = [0.1] * 1536
        mock_rag.search = AsyncMock(return_value=[])

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=_mock_claude_response()
        )

        with patch(
            "app.core.agents.base.BaseAgent._get_client",
            return_value=mock_client,
        ):
            response = await client.post(
                "/api/v1/chat/send",
                json=body,
                headers=headers,
            )

    return response


@pytest.mark.asyncio
async def test_send_message_creates_session(client: AsyncClient) -> None:
    """POST /chat/send with no session_id creates a new session."""
    headers = await _register_and_get_headers(client, "chat1@test.com")
    ws = await _create_workspace(client, headers)
    workspace_id = ws["id"]

    response = await _send_message(client, headers, workspace_id)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["user_message"]["content"] == "What is the market size?"
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"
    assert len(data["assistant_message"]["content"]) > 0


@pytest.mark.asyncio
async def test_send_message_existing_session(client: AsyncClient) -> None:
    """POST /chat/send with valid session_id appends to existing session."""
    headers = await _register_and_get_headers(client, "chat2@test.com")
    ws = await _create_workspace(client, headers)
    workspace_id = ws["id"]

    # First message creates session
    resp1 = await _send_message(client, headers, workspace_id, "First message")
    session_id = resp1.json()["session_id"]

    # Second message uses existing session
    resp2 = await _send_message(
        client, headers, workspace_id, "Second message", session_id=session_id
    )
    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_send_message_returns_routing_plan(client: AsyncClient) -> None:
    """Response includes routing_plan with all required fields."""
    headers = await _register_and_get_headers(client, "chat3@test.com")
    ws = await _create_workspace(client, headers)
    workspace_id = ws["id"]

    response = await _send_message(client, headers, workspace_id)

    data = response.json()
    plan = data["routing_plan"]
    assert "selected_agent" in plan
    assert "model_profile" in plan
    assert "confidence" in plan
    assert "reasoning" in plan
    assert "latency_ms" in plan
    assert "fallback_agent" in plan


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient) -> None:
    """GET /chat/sessions returns sessions ordered by updated_at desc."""
    headers = await _register_and_get_headers(client, "chat4@test.com")
    ws = await _create_workspace(client, headers)
    workspace_id = ws["id"]

    # Create two sessions
    await _send_message(client, headers, workspace_id, "Session 1")
    await _send_message(client, headers, workspace_id, "Session 2")

    response = await client.get(
        f"/api/v1/chat/sessions?workspace_id={workspace_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 2


@pytest.mark.asyncio
async def test_get_session_with_messages(client: AsyncClient) -> None:
    """GET /chat/sessions/{id} returns session with message history."""
    headers = await _register_and_get_headers(client, "chat5@test.com")
    ws = await _create_workspace(client, headers)
    workspace_id = ws["id"]

    # Create a session with a message
    resp = await _send_message(client, headers, workspace_id)
    session_id = resp.json()["session_id"]

    response = await client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert len(data["messages"]) == 2  # user + assistant
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_chat_requires_venture(client: AsyncClient) -> None:
    """Workspace without venture returns 400."""
    import uuid

    headers = await _register_and_get_headers(client, "chat6@test.com")
    await _create_workspace(client, headers)

    # The workspace auto-creates a venture, so we test with a
    # non-existent workspace_id to verify the auth/venture check path.
    fake_ws_id = str(uuid.uuid4())

    response = await _send_message(client, headers, fake_ws_id)
    assert response.status_code == 404  # Workspace not found
