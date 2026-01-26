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

## Your Approach
1. Follow proven deck structures (Problem → Solution → Market → etc.)
2. Optimize for slide scannability
3. Balance data with narrative
4. Tailor content density to stage

## Response Guidelines
- Provide specific slide-by-slide guidance
- Suggest data visualizations where appropriate
- Include speaker notes recommendations
- Flag common pitfalls to avoid

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

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        venture_snapshot = await self.get_venture_snapshot()
        retrieval_context = await self.get_context(message, max_chunks=15)

        formatted_context = self.format_context_for_prompt(retrieval_context)
        venture = venture_snapshot.get("venture", {})
        entities = venture_snapshot.get("entities", {})

        venture_info = f"""- **Name**: {venture.get('name', 'Unknown')}
- **Stage**: {venture.get('stage', 'Unknown')}
- **One-liner**: {venture.get('one_liner', 'N/A')}"""

        # Include metrics and market data for deck content
        metrics_info = ""
        if "metric" in entities:
            metrics = entities["metric"][:5]
            metrics_info = "\n### Key Metrics\n" + "\n".join(
                [f"- {m.get('data', {})}" for m in metrics]
            )

        user_message = f"""## Venture Context
{venture_info}
{metrics_info}

## Available Information
{formatted_context}

---

Request: {message}"""

        messages = []
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response_text = await self.llm.complete(
            messages=messages,
            system=DECK_ARCHITECT_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=8192,
        )

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
            confidence=0.85,
        )
