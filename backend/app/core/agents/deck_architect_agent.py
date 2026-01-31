"""Deck Architect Agent for pitch deck creation."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

DECK_ARCHITECT_SYSTEM_PROMPT = """You are the Deck Architect, specialized in pitch deck creation.

## Expertise
- Pitch deck structure and flow
- Slide content optimization
- Visual storytelling recommendations
- Investor deck best practices
- Stage-appropriate deck strategy

## Available Tools
1. **analyze_image**: Analyze existing pitch deck slides
   - Use to review slide design, content, and messaging
   - Provides design quality ratings and improvement suggestions

2. **query_knowledge_graph**: Check venture context and existing data
   - Use FIRST to understand what's already known

## Your Approach
1. Follow proven deck structures (Problem → Solution → Market → etc.)
2. Optimize for slide scannability
3. Balance data with narrative
4. Tailor content density to stage
5. When analyzing existing decks, use analyze_image to review slides

## Response Guidelines
- Provide specific slide-by-slide guidance
- Suggest data visualizations where appropriate
- Include speaker notes recommendations
- Flag common pitfalls to avoid
- Use vision analysis to critique existing slides

Help create decks that tell a compelling story and drive action."""


class DeckArchitectAgent(BaseAgent):
    """Agent for pitch deck structure and content.

    Helps founders create compelling pitch decks with proper
    structure, content, and visual recommendations.
    """

    name = "deck_architect"
    description = "Pitch deck structure, slide content, and presentation design"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        super().__init__(brain)
        self.llm = llm or get_llm_client("claude")

    def get_default_tools(self) -> list[str]:
        """Get tools for deck architecture.

        Returns:
            List of tool names including vision analysis
        """
        return ["analyze_image", "query_knowledge_graph"]

    def _get_system_prompt(self) -> str:
        """Get the deck architect system prompt.

        Returns:
            System prompt for deck creation
        """
        return DECK_ARCHITECT_SYSTEM_PROMPT

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Execute deck architecture with vision tool support.

        Args:
            message: Deck creation request or question
            context: Optional additional context

        Returns:
            AgentResponse with deck guidance and vision analysis
        """
        # Use tool-enabled execution for vision capabilities
        return await self.execute_with_tools(
            message=message,
            context=context,
            max_iterations=7  # Deck analysis may need slide reviews
        )
