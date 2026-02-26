"""MCP server exposing web research tools.

Provides web_search and fetch_url for external MCP clients.

Mount via FastAPI:
    from app.mcp.research_server import research_mcp_app
    app.mount("/mcp/research", research_mcp_app)
"""

from __future__ import annotations

import re
from typing import Any

import httpx
import structlog
from fastmcp import FastMCP

from app.config import settings

logger = structlog.get_logger()

_TAVILY_URL = "https://api.tavily.com/search"
_HTTP_TIMEOUT = 20.0

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

research_mcp = FastMCP(
    "Market Research",
    instructions=(
        "Search the web for market data, competitor intelligence, "
        "industry trends, and funding announcements. Fetch and "
        "extract content from URLs."
    ),
)


# ---------------------------------------------------------------------------
# Tool: web_search
# ---------------------------------------------------------------------------


@research_mcp.tool
async def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> dict[str, Any]:
    """Search the web using Tavily API.

    Args:
        query: Search query (be specific for best results).
        max_results: Maximum results to return (1-10).
        search_depth: 'basic' for quick results, 'advanced' for deeper analysis.
    """
    api_key = settings.tavily_api_key
    if not api_key:
        return {
            "error": True,
            "message": "Web search not configured. Set TAVILY_API_KEY.",
        }

    max_results = min(max(max_results, 1), 10)

    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
    }

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(_TAVILY_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        return {
            "error": True,
            "message": f"Search API returned HTTP {exc.response.status_code}",
        }
    except httpx.RequestError as exc:
        return {
            "error": True,
            "message": f"Search API request failed: {type(exc).__name__}",
        }

    results = [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", "")[:1000],
            "score": item.get("score"),
        }
        for item in data.get("results", [])
    ]

    return {
        "query": query,
        "answer": data.get("answer", ""),
        "results": results,
        "result_count": len(results),
    }


# ---------------------------------------------------------------------------
# Tool: fetch_url
# ---------------------------------------------------------------------------


def _strip_html(html: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@research_mcp.tool
async def fetch_url(
    url: str,
    max_chars: int = 5000,
) -> dict[str, Any]:
    """Fetch and extract text content from a URL.

    Args:
        url: The URL to fetch (must start with http:// or https://).
        max_chars: Maximum characters to return (default 5000, max 8000).
    """
    if not url.startswith(("http://", "https://")):
        return {"error": True, "message": "URL must start with http(s)://"}

    max_chars = min(max_chars, 8000)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; AIVCCoPilot/1.0; "
            "+https://vccopilot.ai)"
        ),
        "Accept": "text/html,application/xhtml+xml,text/plain",
    }

    try:
        async with httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {
            "error": True,
            "message": f"HTTP {exc.response.status_code} fetching {url}",
        }
    except httpx.RequestError as exc:
        return {
            "error": True,
            "message": f"Failed to fetch: {type(exc).__name__}",
        }

    content_type = resp.headers.get("content-type", "")
    raw = resp.text

    if "text/html" in content_type or "application/xhtml" in content_type:
        text = _strip_html(raw)
    else:
        text = raw

    if len(text) > max_chars:
        text = text[:max_chars] + "... [truncated]"

    return {
        "url": str(resp.url),
        "status_code": resp.status_code,
        "content_type": content_type.split(";")[0].strip(),
        "content": text,
        "content_length": len(text),
    }


# ---------------------------------------------------------------------------
# ASGI app for mounting into FastAPI
# ---------------------------------------------------------------------------

research_mcp_app = research_mcp.http_app(path="/mcp")
