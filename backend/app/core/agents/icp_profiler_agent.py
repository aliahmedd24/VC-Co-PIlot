"""ICP Profiler Agent for customer profiling and segmentation."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

ICP_PROFILER_SYSTEM_PROMPT = """You are the ICP Profiler, specialized in customer profiling and segmentation.

## Expertise
- Ideal Customer Profile (ICP) definition
- Buyer persona creation
- Market segmentation
- Customer journey mapping
- Target audience prioritization

## Your Approach
1. Start with observable characteristics
2. Identify pain points and motivations
3. Map decision-making processes
4. Prioritize segments by opportunity

## Response Guidelines
- Create specific, actionable profiles
- Distinguish between user and buyer
- Include firmographics and psychographics
- Suggest validation methods

Help founders deeply understand and target their ideal customers."""


class ICPProfilerAgent(BaseAgent):
    """Agent for customer profiling and segmentation.

    Helps founders define and understand their ideal
    customer profiles and market segments.
    """

    name = "icp_profiler"
    description = "Customer profiling, persona creation, and market segmentation"

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
- **Problem**: {venture.get('problem', 'N/A')}
- **Solution**: {venture.get('solution', 'N/A')}"""

        icp_info = ""
        if "icp" in entities:
            icps = entities["icp"][:5]
            icp_info = "\n### Existing ICP Data\n" + "\n".join(
                [f"- {i.get('data', {})}" for i in icps]
            )

        market_info = ""
        if "market" in entities:
            markets = entities["market"][:3]
            market_info = "\n### Market Data\n" + "\n".join(
                [f"- {m.get('data', {})}" for m in markets]
            )

        user_message = f"""## Venture Context
{venture_info}
{icp_info}
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
            system=ICP_PROFILER_SYSTEM_PROMPT,
            temperature=0.6,
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
