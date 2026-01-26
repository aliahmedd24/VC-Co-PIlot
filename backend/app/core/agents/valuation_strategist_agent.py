"""Valuation Strategist Agent for valuation and funding strategy."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

VALUATION_STRATEGIST_SYSTEM_PROMPT = """You are the Valuation Strategist, specialized in startup valuation and funding.

## Expertise
- Pre-money/post-money valuation
- Valuation methodologies (comps, DCF, scorecard)
- Funding round strategy and timing
- Cap table management
- Term sheet negotiation guidance

## Your Approach
1. Always contextualize valuation to stage and market
2. Use multiple methodologies when possible
3. Be honest about valuation uncertainty ranges
4. Consider dilution and future round implications

## Response Guidelines
- Provide valuation ranges, not single numbers
- Explain methodology and assumptions clearly
- Flag risks and sensitivities
- Include comparable company data when available

Help founders think strategically about valuation and funding."""


class ValuationStrategistAgent(BaseAgent):
    """Agent for valuation and funding round strategy.

    Helps founders understand valuation methodologies and
    develop funding round strategies.
    """

    name = "valuation_strategist"
    description = "Valuation analysis, funding strategy, and cap table guidance"

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

        # Include funding and metrics data
        funding_info = ""
        if "funding_assumption" in entities:
            funding = entities["funding_assumption"][:5]
            funding_info = "\n### Funding Data\n" + "\n".join(
                [f"- {f.get('data', {})}" for f in funding]
            )

        metrics_info = ""
        if "metric" in entities:
            metrics = entities["metric"][:5]
            metrics_info = "\n### Key Metrics\n" + "\n".join(
                [f"- {m.get('data', {})}" for m in metrics]
            )

        user_message = f"""## Venture Context
{venture_info}
{funding_info}
{metrics_info}

## Available Information
{formatted_context}

---

Request: {message}

Please consider:
1. Stage-appropriate valuation methodologies
2. Market conditions and comparable companies
3. Dilution and future funding implications"""

        messages = []
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response_text = await self.llm.complete(
            messages=messages,
            system=VALUATION_STRATEGIST_SYSTEM_PROMPT,
            temperature=0.5,  # Lower temp for financial analysis
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
            confidence=0.80,
        )
