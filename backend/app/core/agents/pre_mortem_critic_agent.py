"""Pre-Mortem Critic Agent for risk analysis and failure mode identification."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

PRE_MORTEM_CRITIC_SYSTEM_PROMPT = """You are the Pre-Mortem Critic, specialized in startup risk analysis.

## Expertise
- Pre-mortem analysis methodology
- Risk identification and categorization
- Failure mode analysis
- Mitigation strategy development
- Stage-appropriate risk prioritization

## Your Approach
1. Imagine the venture has failed - why?
2. Identify risks across all dimensions
3. Assess probability and impact
4. Develop specific mitigation strategies

## Response Guidelines
- Be constructively critical, not pessimistic
- Prioritize risks by severity
- Suggest concrete mitigation actions
- Balance risk awareness with action bias

Help founders anticipate and prevent potential failures."""


class PreMortemCriticAgent(BaseAgent):
    """Agent for risk analysis and failure mode identification.

    Helps founders identify risks and develop mitigation
    strategies using pre-mortem methodology.
    """

    name = "pre_mortem_critic"
    description = "Risk analysis, failure modes, and mitigation strategies"

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

        risks_info = ""
        if "risk" in entities:
            risks = entities["risk"][:10]
            risks_info = "\n### Known Risks\n" + "\n".join(
                [f"- {r.get('data', {})}" for r in risks]
            )

        competitors_info = ""
        if "competitor" in entities:
            competitors = entities["competitor"][:5]
            competitors_info = "\n### Competitors\n" + "\n".join(
                [f"- {c.get('data', {})}" for c in competitors]
            )

        user_message = f"""## Venture Context
{venture_info}
{risks_info}
{competitors_info}

## Available Information
{formatted_context}

---

Request: {message}

Consider risks across:
1. Market/demand risks
2. Competition risks
3. Execution risks
4. Financial risks
5. Team risks"""

        messages = []
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response_text = await self.llm.complete(
            messages=messages,
            system=PRE_MORTEM_CRITIC_SYSTEM_PROMPT,
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
