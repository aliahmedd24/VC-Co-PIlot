"""Tool handlers for external web research (web_search, fetch_url)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import httpx
import structlog

from app.config import settings
from app.core.tools.registry import ToolDefinition, tool_registry

if TYPE_CHECKING:
    from app.core.tools.executor import ToolExecutor

logger = structlog.get_logger()

_TAVILY_URL = "https://api.tavily.com/search"
_HTTP_TIMEOUT = 20.0
_DEFAULT_MAX_RESULTS = 5
_DEFAULT_FETCH_MAX_CHARS = 5000


def _strip_html(html: str) -> str:
    """Remove HTML tags and normalize whitespace to extract readable text."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# Tool: web_search
# --------------------------------------------------------------------------- #

WEB_SEARCH_DEF = ToolDefinition(
    name="web_search",
    description=(
        "Search the web for current market data, competitor info, industry "
        "trends, funding announcements, and other real-time information. "
        "Returns titles, URLs, and content snippets. Requires a Tavily API key."
    ),
    input_schema={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (be specific for best results)",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return (1-10, default 5)",
            },
            "search_depth": {
                "type": "string",
                "enum": ["basic", "advanced"],
                "description": (
                    "Search depth: 'basic' for quick results, "
                    "'advanced' for deeper analysis (slower)"
                ),
            },
        },
    },
    timeout_seconds=30.0,
)


async def handle_web_search(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Execute a web search via the Tavily API."""
    api_key = settings.tavily_api_key
    if not api_key:
        return {
            "error": True,
            "message": (
                "Web search is not configured. Set TAVILY_API_KEY in environment."
            ),
        }

    query = tool_input["query"]
    max_results = min(max(tool_input.get("max_results", _DEFAULT_MAX_RESULTS), 1), 10)
    search_depth = tool_input.get("search_depth", "basic")

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
        logger.warning("tavily_http_error", status=exc.response.status_code)
        return {
            "error": True,
            "message": f"Search API returned HTTP {exc.response.status_code}",
        }
    except httpx.RequestError as exc:
        logger.warning("tavily_request_error", error=str(exc))
        return {
            "error": True,
            "message": f"Search API request failed: {type(exc).__name__}",
        }

    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", "")[:1000],
            "score": item.get("score"),
        })

    return {
        "query": query,
        "answer": data.get("answer", ""),
        "results": results,
        "result_count": len(results),
    }


# --------------------------------------------------------------------------- #
# Tool: fetch_url
# --------------------------------------------------------------------------- #

FETCH_URL_DEF = ToolDefinition(
    name="fetch_url",
    description=(
        "Fetch and extract text content from a specific URL. Use this to read "
        "articles, reports, or web pages found via web_search. Returns the "
        "extracted text content (HTML tags stripped)."
    ),
    input_schema={
        "type": "object",
        "required": ["url"],
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch (must start with http:// or https://)",
            },
            "max_chars": {
                "type": "integer",
                "description": (
                    "Maximum characters of content to return (default 5000, max 8000)"
                ),
            },
        },
    },
    timeout_seconds=30.0,
)


async def handle_fetch_url(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Fetch a URL and extract text content."""
    url = tool_input["url"]

    if not url.startswith(("http://", "https://")):
        return {"error": True, "message": "URL must start with http:// or https://"}

    max_chars = min(tool_input.get("max_chars", _DEFAULT_FETCH_MAX_CHARS), 8000)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; AIVCCoPilot/1.0; +https://vccopilot.ai)"
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
            "message": f"Failed to fetch URL: {type(exc).__name__}",
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


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

def register_research_tools() -> None:
    """Register web research tools with the global tool registry."""
    tool_registry.register(WEB_SEARCH_DEF, handle_web_search)
    tool_registry.register(FETCH_URL_DEF, handle_fetch_url)
