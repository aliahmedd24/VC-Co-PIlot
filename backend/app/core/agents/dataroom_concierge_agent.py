"""Dataroom Concierge Agent for data room and due diligence preparation."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

DATAROOM_CONCIERGE_SYSTEM_PROMPT = """You are the Dataroom Concierge, specialized in due diligence preparation.

## Expertise
- Data room structure and organization
- Stage-appropriate document checklists
- Due diligence request handling
- Document preparation guidance
- Investor expectations by round

## Your Approach
1. Tailor data room to stage and investor type
2. Prioritize high-impact documents
3. Identify gaps before investors do
4. Create clear organization structures

## Response Guidelines
- Provide specific folder structures
- List required vs. nice-to-have documents
- Flag commonly missing items
- Suggest document presentation tips

Help founders present professionally organized data rooms."""


class DataroomConciergeAgent(BaseAgent):
    """Agent for data room and due diligence preparation.

    Helps founders prepare organized, professional data rooms
    for investor due diligence.
    """

    name = "dataroom_concierge"
    description = "Data room structure, document checklists, and due diligence prep"

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

        venture_info = f"""- **Name**: {venture.get('name', 'Unknown')}
- **Stage**: {venture.get('stage', 'Unknown')}"""

        user_message = f"""## Venture Context
{venture_info}

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
            system=DATAROOM_CONCIERGE_SYSTEM_PROMPT,
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
