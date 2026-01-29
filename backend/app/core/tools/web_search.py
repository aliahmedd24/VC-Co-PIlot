"""Web search tool using Brave Search API.

This tool enables agents to search the web for current information,
market data, competitor intelligence, and other real-time data.
"""

import httpx
from app.config import settings
from app.core.tools.base import BaseTool, ToolDefinition, ToolResult


class BraveSearchTool(BaseTool):
    """Web search using Brave Search API.

    The Brave Search API provides access to fresh, independent search results.
    Free tier: 2,500 queries/month
    Sign up: https://brave.com/search/api/

    This tool is essential for:
    - Market research and sizing
    - Competitor intelligence
    - Current events and trends
    - Company and founder research
    - Industry analysis
    """

    def __init__(self):
        """Initialize the Brave Search tool."""
        self.api_key = settings.brave_api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition for Claude."""
        return ToolDefinition(
            name="web_search",
            description=(
                "Search the web for current information, news, company data, market research, "
                "or any information not in the knowledge base. Use this for recent events, "
                "competitor info, industry trends, market sizing, funding news, or fact-checking. "
                "Returns web search results with URLs and descriptions."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The search query. Be specific and use relevant keywords. "
                            "Examples: 'AI infrastructure market size 2024', "
                            "'competitor analysis for Stripe', 'Series A funding trends'"
                        )
                    },
                    "count": {
                        "type": "number",
                        "description": "Number of results to return (1-20). Default is 5.",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )

    async def execute(self, query: str, count: int = 5, **kwargs) -> ToolResult:
        """Execute a web search using Brave Search API.

        Args:
            query: The search query
            count: Number of results to return (1-20)
            **kwargs: Additional context (unused)

        Returns:
            ToolResult with search results and citations
        """
        # Validate API key
        if not self.api_key:
            return ToolResult(
                tool_name="web_search",
                success=False,
                error="Brave API key not configured. Please set BRAVE_API_KEY in .env",
                result=None
            )

        # Validate count
        count = max(1, min(count, 20))

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip",
                        "X-Subscription-Token": self.api_key
                    },
                    params={
                        "q": query,
                        "count": count
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            # Parse results
            results = []
            citations = []
            web_results = data.get("web", {}).get("results", [])

            if not web_results:
                return ToolResult(
                    tool_name="web_search",
                    success=True,
                    result="No results found for this query.",
                    citations=[],
                    metadata={"query": query, "result_count": 0}
                )

            for idx, item in enumerate(web_results, 1):
                title = item.get("title", "No title")
                description = item.get("description", "No description")
                url = item.get("url", "")

                # Format result for LLM
                result_text = f"{idx}. {title}\n{description}\nURL: {url}"
                results.append(result_text)

                # Add citation
                citations.append({
                    "source": "web_search",
                    "title": title,
                    "url": url,
                    "snippet": description,
                    "relevance": item.get("score", 0.0)
                })

            result_text = "\n\n".join(results)

            return ToolResult(
                tool_name="web_search",
                success=True,
                result=result_text,
                citations=citations,
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "api": "brave_search"
                }
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg = "Invalid Brave API key. Please check BRAVE_API_KEY in .env"
            elif e.response.status_code == 429:
                error_msg = "Brave API rate limit exceeded. Free tier: 2,500 queries/month"

            return ToolResult(
                tool_name="web_search",
                success=False,
                error=error_msg,
                result=None
            )

        except httpx.TimeoutException:
            return ToolResult(
                tool_name="web_search",
                success=False,
                error="Web search request timed out. Please try again.",
                result=None
            )

        except Exception as e:
            return ToolResult(
                tool_name="web_search",
                success=False,
                error=f"Web search error: {str(e)}",
                result=None
            )


# Register the tool on import
from app.core.tools.registry import tool_registry
tool_registry.register(BraveSearchTool())
