"""Lean Modeler Agent for financial projections and unit economics."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

LEAN_MODELER_SYSTEM_PROMPT = """You are the Lean Modeler, specialized in startup financial modeling.

## Expertise
- Financial projections and forecasting
- Runway and burn rate analysis
- Unit economics (CAC, LTV, margins)
- Cash flow modeling
- Break-even analysis

## Your Approach
1. Start with key assumptions and drivers
2. Build bottom-up when possible
3. Stress-test critical variables
4. Show clear paths to profitability

## Response Guidelines
- Clearly state all assumptions
- Provide ranges for uncertain projections
- Flag key sensitivities and risks
- Create actionable financial milestones

Help founders build realistic, defensible financial models."""


class LeanModelerAgent(BaseAgent):
    """Agent for financial projections and unit economics.

    Helps founders build financial models, analyze runway,
    and understand unit economics.
    """

    name = "lean_modeler"
    description = "Financial projections, runway analysis, and unit economics"

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
- **Stage**: {venture.get('stage', 'Unknown')}"""

        # Include financial data
        funding_info = ""
        if "funding_assumption" in entities:
            funding = entities["funding_assumption"][:5]
            funding_info = "\n### Funding Assumptions\n" + "\n".join(
                [f"- {f.get('data', {})}" for f in funding]
            )

        metrics_info = ""
        if "metric" in entities:
            metrics = entities["metric"][:10]
            metrics_info = "\n### Financial Metrics\n" + "\n".join(
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

Please provide:
1. Analysis with clear assumptions
2. Key financial drivers and sensitivities
3. Actionable recommendations"""

        messages = []
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response_text = await self.llm.complete(
            messages=messages,
            system=LEAN_MODELER_SYSTEM_PROMPT,
            temperature=0.4,  # Low temp for financial precision
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
