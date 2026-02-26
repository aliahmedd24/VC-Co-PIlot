"""Tests for Sprint E advanced MCP servers and MCP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.mcp.mcp_client import MCPClient

# ------------------------------------------------------------------ #
# Analytics MCP Server
# ------------------------------------------------------------------ #


class TestAnalyticsMCPServer:
    """Test analytics_server.py tool registration and server setup."""

    def test_server_instance_exists(self) -> None:
        from app.mcp.analytics_server import analytics_mcp

        assert analytics_mcp.name == "VC Analytics"

    def test_asgi_app_created(self) -> None:
        from app.mcp.analytics_server import analytics_mcp_app

        assert analytics_mcp_app is not None

    def test_has_five_tools(self) -> None:

        # FastMCP stores tools internally
        tool_names = {
            "run_valuation",
            "score_readiness",
            "model_scenario",
            "rank_benchmarks",
            "match_success_stories",
        }
        # Verify the decorated functions exist as module attrs
        import app.mcp.analytics_server as mod

        for name in tool_names:
            assert hasattr(mod, name), f"Missing tool function: {name}"


# ------------------------------------------------------------------ #
# Research MCP Server
# ------------------------------------------------------------------ #


class TestResearchMCPServer:
    """Test research_server.py tool registration."""

    def test_server_instance_exists(self) -> None:
        from app.mcp.research_server import research_mcp

        assert research_mcp.name == "Market Research"

    def test_asgi_app_created(self) -> None:
        from app.mcp.research_server import research_mcp_app

        assert research_mcp_app is not None

    def test_has_tools(self) -> None:
        import app.mcp.research_server as mod

        assert hasattr(mod, "web_search")
        assert hasattr(mod, "fetch_url")


# ------------------------------------------------------------------ #
# Memory MCP Server
# ------------------------------------------------------------------ #


class TestMemoryMCPServer:
    """Test memory_server.py tool and resource registration."""

    def test_server_instance_exists(self) -> None:
        from app.mcp.memory_server import memory_mcp

        assert memory_mcp.name == "Agent Memory"

    def test_asgi_app_created(self) -> None:
        from app.mcp.memory_server import memory_mcp_app

        assert memory_mcp_app is not None

    def test_has_tools(self) -> None:
        import app.mcp.memory_server as mod

        for tool_name in ("store_insight", "recall_context", "update_preference"):
            assert hasattr(mod, tool_name), f"Missing: {tool_name}"

    def test_has_resources(self) -> None:
        import app.mcp.memory_server as mod

        assert hasattr(mod, "get_venture_insights")
        assert hasattr(mod, "get_user_preferences")


# ------------------------------------------------------------------ #
# AgentMemory model
# ------------------------------------------------------------------ #


class TestAgentMemoryModel:
    """Test the AgentMemory SQLAlchemy model."""

    def test_model_table_name(self) -> None:
        from app.models.agent_memory import AgentMemory

        assert AgentMemory.__tablename__ == "agent_memories"

    def test_memory_type_enum(self) -> None:
        from app.models.agent_memory import MemoryType

        assert MemoryType.INSIGHT.value == "insight"
        assert MemoryType.PREFERENCE.value == "preference"
        assert MemoryType.CONTEXT.value == "context"

    def test_model_repr(self) -> None:
        from app.models.agent_memory import AgentMemory, MemoryType

        m = AgentMemory.__new__(AgentMemory)
        m.id = "test-id"
        m.memory_type = MemoryType.INSIGHT
        m.key = "test_key"
        assert "test_key" in repr(m)


# ------------------------------------------------------------------ #
# MCP Client
# ------------------------------------------------------------------ #


class TestMCPClient:
    """Test the MCPClient facade."""

    def test_init(self) -> None:
        client = MCPClient(base_url="http://localhost:8001/mcp/brain")
        assert client.base_url == "http://localhost:8001/mcp/brain"
        assert client.timeout == 30.0

    def test_repr(self) -> None:
        client = MCPClient(base_url="http://localhost:8001")
        assert "localhost:8001" in repr(client)

    @pytest.mark.asyncio
    async def test_call_tool_success(self) -> None:
        client = MCPClient(base_url="http://localhost:8001")

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"count": 5},
        }

        with patch("app.mcp.mcp_client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await client.call_tool("query_entities", {"venture_id": "abc"})
            assert result == {"count": 5}

    @pytest.mark.asyncio
    async def test_call_tool_error_response(self) -> None:
        client = MCPClient(base_url="http://localhost:8001")

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32600, "message": "Invalid"},
        }

        with patch("app.mcp.mcp_client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await client.call_tool("bad_tool")
            assert result["error"] is True

    @pytest.mark.asyncio
    async def test_list_tools(self) -> None:
        client = MCPClient(base_url="http://localhost:8001")

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "tool_a", "description": "desc"},
                ],
            },
        }

        with patch("app.mcp.mcp_client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = await client.list_tools()
            assert len(tools) == 1
            assert tools[0]["name"] == "tool_a"


# ------------------------------------------------------------------ #
# Main.py mounting
# ------------------------------------------------------------------ #


class TestMainMounting:
    """Verify all MCP apps are mounted in the FastAPI app."""

    def test_mcp_routes_mounted(self) -> None:
        from app.main import app

        route_paths = [r.path for r in app.routes if hasattr(r, "path")]

        assert "/mcp/brain" in route_paths
        assert "/mcp/analytics" in route_paths
        assert "/mcp/research" in route_paths
        assert "/mcp/memory" in route_paths
