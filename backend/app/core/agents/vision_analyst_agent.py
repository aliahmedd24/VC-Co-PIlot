"""Vision Analyst Agent for analyzing visual content in documents.

This specialized agent focuses on extracting insights from visual content:
- Pitch deck slides
- Charts and graphs
- Diagrams and infographics
- Screenshots and UI mockups
"""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse
from app.core.brain.startup_brain import StartupBrain


VISION_ANALYST_SYSTEM_PROMPT = """You are a Vision Analyst specializing in extracting insights from visual content in venture capital documents.

## Your Expertise
- Analyzing pitch deck slides for content quality, design, and messaging
- Extracting precise data from financial charts and graphs
- Interpreting diagrams, workflows, and infographics
- Evaluating product screenshots and UI/UX
- Performing OCR on scanned documents
- Identifying visual inconsistencies and missing information

## Available Tools
1. **analyze_image**: Analyze any visual content (slides, charts, screenshots, diagrams)
   - Use for: slide analysis, design critique, general image understanding
   - Returns: detailed analysis with extracted text and metrics

2. **extract_chart_data**: Extract structured numerical data from charts
   - Use for: financial projections, traction charts, market sizing graphs
   - Returns: chart type, data series, axes info, trends

3. **query_knowledge_graph**: Check existing knowledge before new analysis
   - Use FIRST to see what's already known about this venture

## Analysis Methodology
1. **Check Context**: Use query_knowledge_graph to understand the venture
2. **Visual Analysis**: Use analyze_image or extract_chart_data for visual content
3. **Extract Insights**: Identify key metrics, trends, and gaps
4. **Provide Recommendations**: Suggest improvements or flag concerns

## Output Requirements
- Be precise with extracted numbers and data
- Note design quality and professionalism
- Flag missing information or inconsistencies
- Provide actionable recommendations
- Cite page numbers and sources

## Quality Standards
- Accuracy: Double-check extracted numbers
- Completeness: Don't miss important details
- Context: Consider the venture stage and industry
- Clarity: Present findings in structured format

Focus on extracting maximum value from visual content to support investment decisions."""


class VisionAnalystAgent(BaseAgent):
    """Specialized agent for analyzing visual content in documents.

    This agent excels at:
    - Pitch deck slide analysis and critique
    - Chart interpretation and data extraction
    - Visual quality assessment
    - OCR and document digitization
    - Competitor visual analysis

    It autonomously uses vision tools to analyze images and extract
    structured insights for venture analysis.
    """

    name = "vision_analyst"
    description = "Analyzes visual content including slides, charts, diagrams, and screenshots"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        """Initialize the vision analyst agent.

        Args:
            brain: StartupBrain instance for context retrieval
            llm: Optional LLM client (defaults to Claude)
        """
        super().__init__(brain)
        self.llm = llm or get_llm_client("claude")

    def get_default_tools(self) -> list[str]:
        """Get vision analysis tools.

        Returns:
            List of tool names for vision analysis
        """
        return ["analyze_image", "extract_chart_data", "query_knowledge_graph"]

    def _get_system_prompt(self) -> str:
        """Get the vision analyst system prompt.

        Returns:
            System prompt for vision analysis
        """
        return VISION_ANALYST_SYSTEM_PROMPT

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Execute vision analysis with tool support.

        Args:
            message: Analysis request or question
            context: Optional additional context

        Returns:
            AgentResponse with vision analysis, citations, and recommendations
        """
        # Use tool-enabled execution for enhanced vision capabilities
        return await self.execute_with_tools(
            message=message,
            context=context,
            max_iterations=8  # Vision analysis may need multiple tool calls
        )
