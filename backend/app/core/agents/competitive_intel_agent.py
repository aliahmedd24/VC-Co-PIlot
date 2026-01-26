"""Competitive Intelligence Agent for competitor analysis."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

COMPETITIVE_INTEL_SYSTEM_PROMPT = """You are the Competitive Intelligence analyst, specialized in competitor analysis.

## Expertise
- Competitive landscape mapping
- Competitor deep-dive analysis
- Positioning and differentiation
- Competitive strategy development
- Market dynamics assessment

## Your Approach
1. Map the full competitive landscape
2. Analyze direct and indirect competitors
3. Identify sustainable differentiators
4. Develop competitive positioning

## Response Guidelines
- Create structured competitor comparisons
- Analyze strengths, weaknesses, strategies
- Identify competitive gaps and opportunities
- Suggest positioning strategies

Help founders understand and outmaneuver competition."""


class CompetitiveIntelAgent(BaseAgent):
    """Agent for competitor analysis and competitive strategy.

    Helps founders understand competitive landscape and
    develop differentiation strategies.
    """

    name = "competitive_intel"
    description = "Competitor analysis, landscape mapping, and positioning strategy"

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
- **One-liner**: {venture.get('one_liner', 'N/A')}
- **Solution**: {venture.get('solution', 'N/A')}"""

        competitors_info = ""
        if "competitor" in entities:
            competitors = entities["competitor"][:10]
            competitors_info = "\n### Known Competitors\n" + "\n".join(
                [f"- {c.get('data', {})}" for c in competitors]
            )

        market_info = ""
        if "market" in entities:
            markets = entities["market"][:3]
            market_info = "\n### Market Context\n" + "\n".join(
                [f"- {m.get('data', {})}" for m in markets]
            )

        user_message = f"""## Venture Context
{venture_info}
{competitors_info}
{market_info}

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
            system=COMPETITIVE_INTEL_SYSTEM_PROMPT,
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
