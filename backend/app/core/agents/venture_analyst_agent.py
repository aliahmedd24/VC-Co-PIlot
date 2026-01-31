"""Venture Analyst Agent for deep startup analysis."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation, SuggestedEntity
from app.core.brain.startup_brain import StartupBrain

VENTURE_ANALYST_SYSTEM_PROMPT = """You are a seasoned VC analyst evaluating startups for investment.

Your expertise includes:
- Business model analysis and unit economics
- Team assessment and founder-market fit
- Market opportunity sizing
- Product-market fit evaluation
- Risk assessment and due diligence

## Available Tools
1. **web_search**: Research current market data, competitors, industry trends
2. **calculator**: Perform financial calculations, unit economics, valuations
3. **query_knowledge_graph**: Check existing venture knowledge
4. **extract_entities**: Structure unstructured data into entities
5. **extract_chart_data**: Extract precise numbers from financial charts and graphs

When analyzing:
1. Be thorough but focus on what matters most for the stage
2. Use data from the knowledge base to support your analysis
3. Use extract_chart_data to get precise metrics from visual charts
4. Identify strengths, weaknesses, and key risks
5. Provide specific, actionable recommendations
6. Flag any missing information critical for assessment

You may suggest updates to the startup's knowledge graph when you identify:
- New insights about the market or competition
- Updated understanding of the ICP
- Refined business model assumptions
- New risks or opportunities

Format your analysis with clear sections and bullet points."""


class VentureAnalystAgent(BaseAgent):
    """Specialized agent for deep-dive startup analysis.

    This agent performs VC-style due diligence including business model
    analysis, unit economics, team assessment, and investment readiness.
    """

    name = "venture_analyst"
    description = "Deep-dive startup analysis including business model, team, and unit economics"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        """Initialize the venture analyst agent.

        Args:
            brain: StartupBrain instance for context retrieval.
            llm: Optional LLM client (defaults to Claude).
        """
        super().__init__(brain)
        self.llm = llm or get_llm_client("claude")

    def get_default_tools(self) -> list[str]:
        """Get tools for venture analysis.

        Returns:
            List of tool names for venture analysis
        """
        return [
            "web_search",
            "calculator",
            "query_knowledge_graph",
            "extract_entities",
            "extract_chart_data"
        ]

    def _get_system_prompt(self) -> str:
        """Get the venture analyst system prompt.

        Returns:
            System prompt for venture analysis
        """
        return VENTURE_ANALYST_SYSTEM_PROMPT

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Execute venture analysis with tool support.

        Args:
            message: Analysis request or question.
            context: Optional additional context.

        Returns:
            AgentResponse with analysis, citations, and suggested KG updates.
        """
        # Use tool-enabled execution with calculator for unit economics
        return await self.execute_with_tools(
            message=message,
            context=context,
            max_iterations=8  # Venture analysis may need more iterations
        )

    async def execute_legacy(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Legacy execution method without tools."""
        # Get comprehensive context
        venture_snapshot = await self.get_venture_snapshot()
        retrieval_context = await self.get_context(message, max_chunks=15)

        # Build detailed prompt
        formatted_context = self.format_context_for_prompt(retrieval_context)

        venture_details = self._format_venture_details(venture_snapshot)
        entities_summary = self._format_entities(venture_snapshot.get("entities", {}))

        user_message = f"""## Venture Profile
{venture_details}

## Existing Knowledge
{entities_summary}

## Relevant Documents
{formatted_context}

---

Analysis Request: {message}

Please provide:
1. Your analysis addressing the request
2. Key insights from the available data
3. Any suggested updates to the knowledge graph (as structured data)
4. Recommendations and next steps"""

        messages = [{"role": "user", "content": user_message}]

        # Add conversation history if provided
        if context and "history" in context:
            messages = [
                {"role": m["role"], "content": m["content"]} for m in context["history"][-5:]
            ] + messages

        # Get LLM response
        response_text = await self.llm.complete(
            messages=messages,
            system=VENTURE_ANALYST_SYSTEM_PROMPT,
            temperature=0.5,  # Lower temp for more analytical responses
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

        # Parse any suggested entities from the response (simplified)
        suggested_entities = self._extract_suggested_entities(response_text)

        return AgentResponse(
            content=response_text,
            agent_id=self.name,
            citations=citations,
            suggested_entities=suggested_entities,
            confidence=0.85,
        )

    def _format_venture_details(self, snapshot: dict[str, Any]) -> str:
        """Format venture details for the prompt."""
        venture = snapshot.get("venture")
        if not venture:
            return "No venture profile loaded."

        return f"""- **Name**: {venture.get('name', 'Unknown')}
- **Stage**: {venture.get('stage', 'Unknown')}
- **One-liner**: {venture.get('one_liner', 'N/A')}
- **Problem**: {venture.get('problem', 'N/A')}
- **Solution**: {venture.get('solution', 'N/A')}"""

    def _format_entities(self, entities: dict[str, list]) -> str:
        """Format KG entities for the prompt."""
        if not entities:
            return "No entities in knowledge graph."

        parts = []
        for entity_type, items in entities.items():
            if items:
                parts.append(f"\n### {entity_type.title()}")
                for item in items[:5]:  # Limit to 5 per type
                    data = item.get("data", {})
                    confidence = item.get("confidence", 0)
                    parts.append(f"- {data} (confidence: {confidence:.0%})")

        return "\n".join(parts) if parts else "No entities found."

    def _extract_suggested_entities(self, response: str) -> list[SuggestedEntity]:
        """Extract suggested entity updates from the response.

        This is a simplified implementation. A more robust version would
        use structured output or tool use from the LLM.
        """
        # For now, return empty list - would need structured LLM output
        return []
