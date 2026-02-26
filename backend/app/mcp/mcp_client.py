"""Lightweight MCP client facade for dispatching tool calls to remote servers.

Enables the ToolExecutor to transparently route calls to external MCP servers
(e.g. third-party MCP services running on separate processes/machines).

Usage:
    client = MCPClient(base_url="http://localhost:8001/mcp/brain")
    result = await client.call_tool("query_entities", {"venture_id": "..."})
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

_DEFAULT_TIMEOUT = 30.0


class MCPClient:
    """Client for dispatching tool calls to a remote MCP server.

    Communicates via the MCP HTTP+SSE transport. Provides a simple
    ``call_tool`` interface that abstracts the MCP protocol details.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call a tool on the remote MCP server.

        Args:
            tool_name: Name of the MCP tool to invoke.
            arguments: Tool input arguments.

        Returns:
            Tool result as a dictionary.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

                if "error" in data:
                    return {
                        "error": True,
                        "message": data["error"].get("message", "Unknown"),
                    }

                return data.get("result", {})
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "mcp_client_http_error",
                status=exc.response.status_code,
                url=self.base_url,
            )
            return {
                "error": True,
                "message": (
                    f"MCP server returned HTTP "
                    f"{exc.response.status_code}"
                ),
            }
        except httpx.RequestError as exc:
            logger.warning(
                "mcp_client_request_error",
                error=str(exc),
                url=self.base_url,
            )
            return {
                "error": True,
                "message": (
                    f"MCP server unreachable: {type(exc).__name__}"
                ),
            }

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools on the remote MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("result", {}).get("tools", [])
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning("mcp_client_list_error", error=str(exc))
            return []

    def __repr__(self) -> str:
        return f"MCPClient(base_url={self.base_url!r})"
