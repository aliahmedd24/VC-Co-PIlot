"""Tests for the research tool handlers (web_search, fetch_url)."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.tools.research_tools import (
    _strip_html,
    handle_fetch_url,
    handle_web_search,
)


def _make_ctx() -> Any:
    """Create a mock ToolExecutor context."""
    ctx = MagicMock()
    ctx.venture.id = uuid.uuid4()
    ctx.venture.workspace_id = uuid.uuid4()
    ctx.user_id = str(uuid.uuid4())
    ctx.agent_id = "market-oracle"
    ctx.db = AsyncMock()
    ctx.brain = MagicMock()
    return ctx


# --------------------------------------------------------------------------- #
# _strip_html helper
# --------------------------------------------------------------------------- #


def test_strip_html_removes_tags() -> None:
    """_strip_html extracts text from HTML."""
    html = "<html><body><h1>Title</h1><p>Hello <b>world</b></p></body></html>"
    result = _strip_html(html)
    assert "Title" in result
    assert "Hello" in result
    assert "world" in result
    assert "<" not in result


def test_strip_html_removes_scripts_and_styles() -> None:
    """_strip_html strips script and style blocks."""
    html = (
        "<div>Keep this</div>"
        "<script>var x = 1;</script>"
        "<style>.foo { color: red; }</style>"
        "<p>And this</p>"
    )
    result = _strip_html(html)
    assert "Keep this" in result
    assert "And this" in result
    assert "var x" not in result
    assert ".foo" not in result


def test_strip_html_decodes_entities() -> None:
    """_strip_html converts HTML entities to text."""
    html = "<p>A &amp; B &lt; C &gt; D</p>"
    result = _strip_html(html)
    assert "A & B < C > D" in result


# --------------------------------------------------------------------------- #
# web_search
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.settings")
async def test_web_search_no_api_key(mock_settings: Any) -> None:
    """web_search returns error when TAVILY_API_KEY is not set."""
    mock_settings.tavily_api_key = ""
    ctx = _make_ctx()

    result = await handle_web_search({"query": "test"}, ctx)

    assert result["error"] is True
    assert "not configured" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.settings")
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_web_search_success(
    mock_client_cls: Any, mock_settings: Any,
) -> None:
    """web_search returns structured results from Tavily API."""
    mock_settings.tavily_api_key = "test-key"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "answer": "The market size is $10B",
        "results": [
            {
                "title": "Market Report 2026",
                "url": "https://example.com/report",
                "content": "The global market for AI is growing rapidly.",
                "score": 0.95,
            },
            {
                "title": "Industry Analysis",
                "url": "https://example.com/analysis",
                "content": "Startups in this sector raised $5B in 2025.",
                "score": 0.88,
            },
        ],
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_web_search(
        {"query": "AI market size 2026", "max_results": 3}, ctx,
    )

    assert "error" not in result
    assert result["query"] == "AI market size 2026"
    assert result["answer"] == "The market size is $10B"
    assert result["result_count"] == 2
    assert result["results"][0]["title"] == "Market Report 2026"
    assert result["results"][0]["score"] == 0.95


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.settings")
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_web_search_http_error(
    mock_client_cls: Any, mock_settings: Any,
) -> None:
    """web_search returns error on HTTP failure."""
    mock_settings.tavily_api_key = "test-key"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "rate limited", request=MagicMock(), response=mock_response,
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_web_search({"query": "test"}, ctx)

    assert result["error"] is True
    assert "429" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.settings")
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_web_search_request_error(
    mock_client_cls: Any, mock_settings: Any,
) -> None:
    """web_search returns error on network failure."""
    mock_settings.tavily_api_key = "test-key"

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused"),
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_web_search({"query": "test"}, ctx)

    assert result["error"] is True
    assert "ConnectError" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.settings")
async def test_web_search_clamps_max_results(mock_settings: Any) -> None:
    """web_search clamps max_results between 1 and 10."""
    mock_settings.tavily_api_key = "test-key"

    # We patch at a lower level to verify the payload
    with patch("app.core.tools.research_tools.httpx.AsyncClient") as mock_cls:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [], "answer": ""}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        ctx = _make_ctx()
        await handle_web_search({"query": "test", "max_results": 99}, ctx)

        # Verify the clamped value was sent
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["max_results"] == 10


# --------------------------------------------------------------------------- #
# fetch_url
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_fetch_url_invalid_protocol() -> None:
    """fetch_url rejects non-HTTP URLs."""
    ctx = _make_ctx()
    result = await handle_fetch_url({"url": "ftp://example.com"}, ctx)

    assert result["error"] is True
    assert "http://" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_fetch_url_success_html(mock_client_cls: Any) -> None:
    """fetch_url extracts text from HTML response."""
    html_content = (
        "<html><body><h1>Report</h1><p>Market is growing.</p></body></html>"
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://example.com/report"
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_fetch_url({"url": "https://example.com/report"}, ctx)

    assert "error" not in result
    assert result["status_code"] == 200
    assert result["content_type"] == "text/html"
    assert "Report" in result["content"]
    assert "Market is growing" in result["content"]
    assert "<" not in result["content"]


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_fetch_url_success_plain_text(mock_client_cls: Any) -> None:
    """fetch_url returns plain text as-is."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://example.com/data.txt"
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.text = "Some plain text data"
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_fetch_url({"url": "https://example.com/data.txt"}, ctx)

    assert result["content"] == "Some plain text data"
    assert result["content_type"] == "text/plain"


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_fetch_url_truncates_long_content(mock_client_cls: Any) -> None:
    """fetch_url truncates content beyond max_chars."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://example.com/long"
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.text = "x" * 10000
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_fetch_url(
        {"url": "https://example.com/long", "max_chars": 100}, ctx,
    )

    assert len(result["content"]) <= 120  # 100 + "... [truncated]"
    assert result["content"].endswith("... [truncated]")


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_fetch_url_http_error(mock_client_cls: Any) -> None:
    """fetch_url returns error on HTTP failure."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "not found", request=MagicMock(), response=mock_response,
    )

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_fetch_url({"url": "https://example.com/404"}, ctx)

    assert result["error"] is True
    assert "404" in result["message"]


@pytest.mark.asyncio
@patch("app.core.tools.research_tools.httpx.AsyncClient")
async def test_fetch_url_network_error(mock_client_cls: Any) -> None:
    """fetch_url returns error on network failure."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        side_effect=httpx.ConnectTimeout("timeout"),
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    ctx = _make_ctx()
    result = await handle_fetch_url({"url": "https://example.com"}, ctx)

    assert result["error"] is True
    assert "ConnectTimeout" in result["message"]
