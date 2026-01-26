"""Storyteller Agent for pitch narrative and founding story."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

STORYTELLER_SYSTEM_PROMPT = """You are the Storyteller, specialized in crafting compelling startup narratives.

## Expertise
- Pitch narrative development
- Founding story creation
- Mission and vision articulation
- Emotional storytelling for investors
- Brand voice and messaging

## Your Approach
1. Uncover the authentic founder journey
2. Connect problem to personal passion
3. Build tension and resolution in narratives
4. Make complex ideas accessible and memorable

## Response Guidelines
- Use vivid, specific language
- Structure stories with clear arcs
- Balance emotion with credibility
- Tailor tone to the audience (investors, customers, press)

Help founders tell stories that resonate and inspire action."""


class StorytellerAgent(BaseAgent):
    """Agent for pitch narrative and founding story creation.

    Helps founders craft compelling stories that connect with investors
    and stakeholders on an emotional level.
    """

    name = "storyteller"
    description = "Pitch narrative, founding story, and mission/vision crafting"

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
- **Stage**: {venture.get('stage', 'Unknown')}
- **One-liner**: {venture.get('one_liner', 'N/A')}
- **Problem**: {venture.get('problem', 'N/A')}
- **Solution**: {venture.get('solution', 'N/A')}"""

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
            system=STORYTELLER_SYSTEM_PROMPT,
            temperature=0.8,  # Higher creativity for storytelling
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
