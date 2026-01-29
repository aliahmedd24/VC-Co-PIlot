"""Research Agent for deep, multi-source research workflows.

This specialized agent combines web search, knowledge graph queries,
entity extraction, and calculations to perform comprehensive research.
"""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse
from app.core.brain.startup_brain import StartupBrain


RESEARCH_AGENT_SYSTEM_PROMPT = """You are a deep research specialist for venture analysis.

## Your Mission
Conduct comprehensive, multi-source research combining internal knowledge with external data to provide thorough, well-cited insights on startups, markets, competitors, and industries.

## Tools at Your Disposal
1. **query_knowledge_graph**: Search internal venture knowledge (ALWAYS check this FIRST)
2. **web_search**: Find current external information, news, competitor data, market trends
3. **extract_entities**: Structure unstructured data into competitors, metrics, ICPs, etc.
4. **calculator**: Perform financial calculations, valuations, market sizing math

## Research Methodology
1. **Check Internal Knowledge First**: Use query_knowledge_graph to see what's already known
2. **Identify Information Gaps**: Determine what's missing or needs updating
3. **External Research**: Use web_search for current data, trends, competitor info
4. **Structure Findings**: Use extract_entities to organize new information
5. **Perform Calculations**: Use calculator for market sizing, valuations, unit economics
6. **Synthesize**: Combine all sources into cohesive, well-cited insights

## Output Requirements
- Cite all sources (internal and external)
- Flag confidence levels for findings
- Identify data gaps or uncertainties
- Suggest knowledge graph updates for new entities
- Provide actionable recommendations

## Quality Standards
- Thorough: Don't stop at first search; dig deeper
- Current: Prioritize recent information
- Balanced: Present multiple perspectives
- Specific: Use numbers, dates, and concrete examples
- Cited: Always attribute sources

Research with rigor. Think like a VC analyst conducting due diligence."""


class ResearchAgent(BaseAgent):
    """Specialized agent for deep, multi-step research workflows.

    This agent excels at:
    - Comprehensive market research
    - Multi-source competitive intelligence
    - Deep-dive company research
    - Industry trend analysis
    - Data-driven opportunity assessment

    It autonomously combines multiple tools to gather, structure,
    and synthesize information from both internal and external sources.
    """

    name = "research_agent"
    description = "Deep multi-source research combining web search, knowledge graph, and entity extraction"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        """Initialize the research agent.

        Args:
            brain: StartupBrain instance for context retrieval
            llm: Optional LLM client (defaults to Claude)
        """
        super().__init__(brain)
        self.llm = llm or get_llm_client("claude")

    def get_default_tools(self) -> list[str]:
        """Get all available research tools.

        Returns:
            List of all tool names
        """
        return ["web_search", "query_knowledge_graph", "extract_entities", "calculator"]

    def _get_system_prompt(self) -> str:
        """Get the research agent system prompt.

        Returns:
            System prompt for deep research
        """
        return RESEARCH_AGENT_SYSTEM_PROMPT

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Execute deep research with all available tools.

        Args:
            message: Research request or question
            context: Optional additional context

        Returns:
            AgentResponse with comprehensive research, citations, and metadata
        """
        # Use tool-enabled execution with higher iteration limit for deep research
        return await self.execute_with_tools(
            message=message,
            context=context,
            max_iterations=10  # Allow more iterations for complex research
        )
