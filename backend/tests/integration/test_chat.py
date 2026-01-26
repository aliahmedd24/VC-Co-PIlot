"""Integration tests for Chat API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestChatSessionEndpoints:
    """Tests for chat session CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_chat_session(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session,
    ):
        """Test creating a chat session."""
        # First create a workspace
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Test Workspace"},
            headers=auth_headers,
        )
        workspace_id = workspace_response.json()["id"]

        # Create chat session
        response = await client.post(
            f"/api/v1/chat/sessions?workspace_id={workspace_id}",
            json={"title": "Test Chat"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Chat"
        assert data["workspace_id"] == workspace_id
        assert data["message_count"] == 0

    @pytest.mark.asyncio
    async def test_create_chat_session_without_title(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session,
    ):
        """Test creating a chat session without title."""
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Test Workspace"},
            headers=auth_headers,
        )
        workspace_id = workspace_response.json()["id"]

        response = await client.post(
            f"/api/v1/chat/sessions?workspace_id={workspace_id}",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] is None

    @pytest.mark.asyncio
    async def test_list_chat_sessions(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session,
    ):
        """Test listing chat sessions."""
        # Create workspace and sessions
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Test Workspace"},
            headers=auth_headers,
        )
        workspace_id = workspace_response.json()["id"]

        # Create multiple sessions
        for i in range(3):
            await client.post(
                f"/api/v1/chat/sessions?workspace_id={workspace_id}",
                json={"title": f"Chat {i}"},
                headers=auth_headers,
            )

        response = await client.get(
            f"/api/v1/chat/sessions?workspace_id={workspace_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["sessions"]) == 3

    @pytest.mark.asyncio
    async def test_get_chat_session(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session,
    ):
        """Test getting a single chat session."""
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Test Workspace"},
            headers=auth_headers,
        )
        workspace_id = workspace_response.json()["id"]

        create_response = await client.post(
            f"/api/v1/chat/sessions?workspace_id={workspace_id}",
            json={"title": "My Chat"},
            headers=auth_headers,
        )
        session_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["id"] == session_id
        assert response.json()["title"] == "My Chat"

    @pytest.mark.asyncio
    async def test_delete_chat_session(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session,
    ):
        """Test deleting a chat session."""
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Test Workspace"},
            headers=auth_headers,
        )
        workspace_id = workspace_response.json()["id"]

        create_response = await client.post(
            f"/api/v1/chat/sessions?workspace_id={workspace_id}",
            json={"title": "Delete Me"},
            headers=auth_headers,
        )
        session_id = create_response.json()["id"]

        delete_response = await client.delete(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_session_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test 404 for nonexistent session."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/v1/chat/sessions/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestChatMessageEndpoints:
    """Tests for chat message endpoints."""

    @pytest.fixture
    async def chat_session(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session,
    ):
        """Create a workspace and chat session for message tests."""
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Message Test Workspace"},
            headers=auth_headers,
        )
        workspace_id = workspace_response.json()["id"]

        session_response = await client.post(
            f"/api/v1/chat/sessions?workspace_id={workspace_id}",
            json={"title": "Message Test Session"},
            headers=auth_headers,
        )
        return session_response.json()

    @pytest.mark.asyncio
    async def test_list_messages_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        chat_session: dict,
    ):
        """Test listing messages in empty session."""
        response = await client.get(
            f"/api/v1/chat/sessions/{chat_session['id']}/messages",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["messages"] == []

    @pytest.mark.asyncio
    @patch("app.api.routes.chat.get_agent_router")
    async def test_send_message(
        self,
        mock_get_router,
        client: AsyncClient,
        auth_headers: dict[str, str],
        chat_session: dict,
    ):
        """Test sending a message and getting a response."""
        # Mock the agent router
        mock_router = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is an AI response."
        mock_response.agent_id = "general_agent"
        mock_response.citations = []
        mock_response.routing_plan = {"agent_used": "general_agent"}

        mock_router.route = AsyncMock(return_value=mock_response)
        mock_get_router.return_value = mock_router

        response = await client.post(
            f"/api/v1/chat/sessions/{chat_session['id']}/messages",
            json={"content": "Hello, what is product-market fit?"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check user message
        assert data["user_message"]["role"] == "user"
        assert "product-market fit" in data["user_message"]["content"]

        # Check assistant message
        assert data["assistant_message"]["role"] == "assistant"
        assert data["assistant_message"]["content"] == "This is an AI response."
        assert data["assistant_message"]["agent_id"] == "general_agent"

    @pytest.mark.asyncio
    @patch("app.api.routes.chat.get_agent_router")
    async def test_send_message_with_agent_override(
        self,
        mock_get_router,
        client: AsyncClient,
        auth_headers: dict[str, str],
        chat_session: dict,
    ):
        """Test sending a message with agent override."""
        mock_router = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Market research response."
        mock_response.agent_id = "market_research"
        mock_response.citations = []
        mock_response.routing_plan = {"agent_used": "market_research"}

        mock_router.route = AsyncMock(return_value=mock_response)
        mock_get_router.return_value = mock_router

        response = await client.post(
            f"/api/v1/chat/sessions/{chat_session['id']}/messages",
            json={
                "content": "Who are our competitors?",
                "agent_override": "market_research",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assistant_message"]["agent_id"] == "market_research"

        # Verify agent override was passed
        mock_router.route.assert_called_once()
        call_kwargs = mock_router.route.call_args.kwargs
        assert call_kwargs["agent_override"] == "market_research"

    @pytest.mark.asyncio
    @patch("app.api.routes.chat.get_agent_router")
    async def test_list_messages_after_send(
        self,
        mock_get_router,
        client: AsyncClient,
        auth_headers: dict[str, str],
        chat_session: dict,
    ):
        """Test listing messages after sending."""
        mock_router = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response 1"
        mock_response.agent_id = "general_agent"
        mock_response.citations = []
        mock_response.routing_plan = {}

        mock_router.route = AsyncMock(return_value=mock_response)
        mock_get_router.return_value = mock_router

        # Send a message
        await client.post(
            f"/api/v1/chat/sessions/{chat_session['id']}/messages",
            json={"content": "Hello"},
            headers=auth_headers,
        )

        # List messages
        response = await client.get(
            f"/api/v1/chat/sessions/{chat_session['id']}/messages",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # User + assistant
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
