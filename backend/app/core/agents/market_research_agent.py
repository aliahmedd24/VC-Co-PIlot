"""Market Research Agent for market and competitor analysis."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain
from app.models.kg_entity import KGEntityType

MARKET_RESEARCH_SYSTEM_PROMPT = """You are an expert market researcher and competitive analyst.

Your expertise includes:
- Market sizing (TAM, SAM, SOM)
- Competitive landscape analysis
- Ideal Customer Profile (ICP) definition
- Industry trend analysis
- Go-to-market strategy evaluation

When researching:
1. Use data from the knowledge base to support findings
2. Be specific about market sizes with sources when available
3. Identify direct and indirect competitors
4. Define clear customer segments and personas
5. Highlight market opportunities and threats

You should suggest knowledge graph updates for:
- New competitors discovered
- Refined market segments
- Updated ICP definitions
- New market metrics or data points

Format your research with clear sections, tables where helpful, and bullet points."""


class MarketResearchAgent(BaseAgent):
    """Specialized agent for market and competitor analysis.

    This agent focuses on market sizing, competitive landscape,
    ICP definition, and go-to-market strategy.
    """

    name = "market_research"
    description = "Market sizing, competitive analysis, and ICP definition"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        """Initialize the market research agent.

        Args:
            brain: StartupBrain instance for context retrieval.
            llm: Optional LLM client (defaults to Claude).
        """
        super().__init__(brain)
        self.llm = llm or get_llm_client("claude")

    def get_default_tools(self) -> list[str]:
        """Get tools for market research.

        Returns:
            List of tool names for market research
        """
        return ["web_search", "query_knowledge_graph", "extract_entities"]

    def _get_system_prompt(self) -> str:
        """Get the market research system prompt.

        Returns:
            System prompt for market research
        """
        return MARKET_RESEARCH_SYSTEM_PROMPT

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Execute market research with tool support.

        Args:
            message: Research request or question.
            context: Optional additional context.

        Returns:
            AgentResponse with research, citations, and suggested KG updates.
        """
        # Use tool-enabled execution for enhanced research capabilities
        return await self.execute_with_tools(
            message=message,
            context=context,
            max_iterations=7  # Market research may need more iterations
        )

    async def execute_legacy(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Legacy execution method without tools (kept for backward compatibility).

        Args:
            message: Research request or question.
            context: Optional additional context.

        Returns:
            AgentResponse with research, citations, and suggested KG updates.
        """
        # Get context with focus on market-related entities
        venture_snapshot = await self.get_venture_snapshot()
        retrieval_context = await self.get_context(message, max_chunks=15)

        # Get market-specific entities from the brain
        market_entities = await self.brain.kg.get_entities_by_type(
            [
                KGEntityType.MARKET,
                KGEntityType.ICP,
                KGEntityType.COMPETITOR,
            ]
        )

        # Build detailed prompt
        formatted_context = self.format_context_for_prompt(retrieval_context)
        venture_info = self._format_venture_brief(venture_snapshot)
        existing_market_data = self._format_market_entities(market_entities)

        user_message = f"""## Venture Brief
{venture_info}

## Existing Market Data
{existing_market_data}

## Relevant Documents
{formatted_context}

---

Research Request: {message}

Please provide:
1. Your research findings addressing the request
2. Data and metrics with sources where available
3. Suggested updates to the knowledge graph (competitors, ICPs, market data)
4. Strategic recommendations based on the analysis"""

        messages = [{"role": "user", "content": user_message}]

        # Add conversation history if provided
        if context and "history" in context:
            messages = [
                {"role": m["role"], "content": m["content"]} for m in context["history"][-5:]
            ] + messages

        # Get LLM response
        response_text = await self.llm.complete(
            messages=messages,
            system=MARKET_RESEARCH_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=8192,
        )

        # Build citations
        citations = [
            Citation(
                chunk_id=c.get("chunk_id", ""),
                document_id=c.get("document_id", ""),
                snippet=c.get("snippet", ""),
                score=c.get("score", 0.0),
            )
            for c in retrieval_context.get("citations", [])
        ]

        return AgentResponse(
            content=response_text,
            agent_id=self.name,
            citations=citations,
            suggested_entities=[],  # Would extract from structured LLM output
            confidence=0.8,
        )

    def _format_venture_brief(self, snapshot: dict[str, Any]) -> str:
        """Format brief venture info for context."""
        venture = snapshot.get("venture")
        if not venture:
            return "No venture profile loaded."

        return f"""- **Name**: {venture.get('name', 'Unknown')}
- **One-liner**: {venture.get('one_liner', 'N/A')}
- **Solution**: {venture.get('solution', 'N/A')}"""

    def _format_market_entities(self, entities: list) -> str:
        """Format market-related entities for the prompt."""
        if not entities:
            return "No market data in knowledge graph yet."

        parts = {"market": [], "icp": [], "competitor": []}

        for entity in entities:
            entity_type = entity.type.value
            if entity_type in parts:
                data = entity.data
                confidence = entity.confidence
                parts[entity_type].append(f"- {data} (confidence: {confidence:.0%})")

        output = []
        if parts["market"]:
            output.append("### Market Segments")
            output.extend(parts["market"])
        if parts["icp"]:
            output.append("\n### ICPs (Ideal Customer Profiles)")
            output.extend(parts["icp"])
        if parts["competitor"]:
            output.append("\n### Known Competitors")
            output.extend(parts["competitor"])

        return "\n".join(output) if output else "No market data available."
