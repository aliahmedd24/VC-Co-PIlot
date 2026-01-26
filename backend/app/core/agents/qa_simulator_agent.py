"""QA Simulator Agent for investor Q&A preparation."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

QA_SIMULATOR_SYSTEM_PROMPT = """You are the QA Simulator, specialized in investor Q&A preparation.

## Expertise
- Common investor questions by stage
- Objection handling strategies
- Tough question preparation
- Mock pitch sessions
- Answer framing techniques

## Your Approach
1. Anticipate questions based on venture profile
2. Identify potential weak spots investors will probe
3. Help craft compelling, honest responses
4. Balance confidence with transparency

## Response Guidelines
- Provide specific sample questions
- Suggest multiple answer frameworks
- Flag topics requiring more preparation
- Include tips for delivery

Help founders prepare for the toughest investor conversations."""


class QASimulatorAgent(BaseAgent):
    """Agent for investor Q&A preparation.

    Helps founders prepare for investor meetings by
    anticipating questions and crafting responses.
    """

    name = "qa_simulator"
    description = "Investor Q&A prep, objection handling, and mock pitches"

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
- **Problem**: {venture.get('problem', 'N/A')}
- **Solution**: {venture.get('solution', 'N/A')}"""

        risks_info = ""
        if "risk" in entities:
            risks = entities["risk"][:5]
            risks_info = "\n### Known Risks\n" + "\n".join(
                [f"- {r.get('data', {})}" for r in risks]
            )

        user_message = f"""## Venture Context
{venture_info}
{risks_info}

## Available Information
{formatted_context}

---

Request: {message}

Consider:
1. Questions typical for this stage
2. Weaknesses investors might probe
3. How to frame honest, compelling answers"""

        messages = []
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response_text = await self.llm.complete(
            messages=messages,
            system=QA_SIMULATOR_SYSTEM_PROMPT,
            temperature=0.7,
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
