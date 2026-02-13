import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(
    client: AsyncClient,
) -> dict[str, str]:
    """Register a user and return auth headers."""
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"stream-{uuid.uuid4().hex[:8]}@test.com",
            "password": "testpass123",
            "full_name": "Stream Tester",
        },
    )
    token: str = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_workspace(
    client: AsyncClient, headers: dict[str, str]
) -> str:
    """Create workspace and return its id."""
    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Stream WS"},
        headers=headers,
    )
    result: str = ws_resp.json()["id"]
    return result


def _mock_claude_response(text: str = "Test response") -> MagicMock:
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


async def _send_message_json(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    content: str = "What is my valuation?",
) -> Any:
    """Send a chat message with Accept: application/json, all mocks in place."""
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
            resp = await client.post(
                "/api/v1/chat/send",
                json={
                    "workspace_id": workspace_id,
                    "content": content,
                },
                headers={**headers, "Accept": "application/json"},
            )

    return resp


@pytest.mark.asyncio
async def test_non_streaming_fallback_returns_json(client: AsyncClient) -> None:
    """Accept: application/json returns full JSON response (backward compatible)."""
    headers = await _register_and_get_headers(client)
    workspace_id = await _create_workspace(client, headers)

    resp = await _send_message_json(client, headers, workspace_id)

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "assistant_message" in data
    assert data["assistant_message"]["content"] == "Test response"


@pytest.mark.asyncio
async def test_sse_streaming_returns_event_stream(client: AsyncClient) -> None:
    """Accept: text/event-stream returns SSE response."""
    headers = await _register_and_get_headers(client)
    workspace_id = await _create_workspace(client, headers)

    async def mock_text_stream() -> AsyncIterator[str]:
        for token_text in ["Hello", " World", "!"]:
            yield token_text

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__ = AsyncMock()
    mock_stream_ctx.__aenter__.return_value.text_stream = mock_text_stream()
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.agents.base.embedding_service") as mock_embed,
        patch("app.core.brain.startup_brain.startup_brain.rag") as mock_rag,
    ):
        mock_embed.embed_text.return_value = [0.1] * 1536
        mock_rag.search = AsyncMock(return_value=[])

        mock_client = AsyncMock()
        mock_client.messages.stream = MagicMock(
            return_value=mock_stream_ctx,
        )

        with patch(
            "app.core.agents.base.BaseAgent._get_client",
            return_value=mock_client,
        ):
            resp = await client.post(
                "/api/v1/chat/send",
                json={
                    "workspace_id": workspace_id,
                    "content": "Tell me about funding",
                },
                headers={**headers, "Accept": "text/event-stream"},
            )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    body = resp.text
    assert "event: routing" in body
    assert "event: token" in body
    assert "event: done" in body
