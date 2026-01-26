"""KPI Dashboard Agent for metrics tracking and analysis."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

KPI_DASHBOARD_SYSTEM_PROMPT = """You are the KPI Dashboard, specialized in startup metrics and KPI tracking.

## Expertise
- KPI selection and tracking
- MRR, ARR, and revenue metrics
- Churn and retention analysis
- Growth metrics and cohort analysis
- Benchmarking against stage/industry

## Your Approach
1. Focus on metrics that matter for the stage
2. Distinguish between vanity and actionable metrics
3. Provide context through benchmarks
4. Create clear tracking recommendations

## Response Guidelines
- Define metrics precisely
- Suggest measurement methodologies
- Provide industry benchmarks when possible
- Recommend dashboard structure

Help founders track what matters and understand what metrics mean."""


class KPIDashboardAgent(BaseAgent):
    """Agent for KPI tracking and metrics analysis.

    Helps founders identify, track, and understand key
    performance indicators for their stage.
    """

    name = "kpi_dashboard"
    description = "KPI tracking, metrics analysis, and performance benchmarking"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        super().__init__(brain)
        self.llm = llm or get_llm_client("claude")

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        venture_snapshot = await self.get_venture_snapshot()
        retrieval_context = await self.get_context(message, max_chunks=10)

        formatted_context = self.format_context_for_prompt(retrieval_context)
        venture = venture_snapshot.get("venture", {})
        entities = venture_snapshot.get("entities", {})

        venture_info = f"""- **Name**: {venture.get('name', 'Unknown')}
- **Stage**: {venture.get('stage', 'Unknown')}"""

        metrics_info = ""
        if "metric" in entities:
            metrics = entities["metric"][:15]
            metrics_info = "\n### Current Metrics\n" + "\n".join(
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
            system=KPI_DASHBOARD_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=4096,
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
