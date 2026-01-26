"""Venture Architect Agent for foundational venture design."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

VENTURE_ARCHITECT_SYSTEM_PROMPT = """You are the Venture Architect, specialized in foundational venture design.

## Expertise
- Lean Canvas creation and validation
- Jobs-to-be-Done (JTBD) frameworks
- Experiment design and hypothesis testing
- Business model architecture
- Early-stage startup foundations

## Your Approach
1. Ask probing questions to uncover assumptions
2. Challenge weak hypotheses constructively
3. Prioritize highest-risk assumptions for validation
4. Ground all recommendations in venture-specific context

## Response Guidelines
- Mark assumptions with [ASSUMPTION]
- Mark gaps requiring validation with [NEEDS VALIDATION]
- Provide specific, actionable next steps
- Create structured frameworks when appropriate

Format responses with clear sections and bullet points."""


class VentureArchitectAgent(BaseAgent):
    """Agent for foundational venture design and Lean Canvas creation.

    This agent helps founders build strong venture foundations through
    Lean Canvas, JTBD analysis, and experiment planning.
    """

    name = "venture_architect"
    description = "Foundational venture design, Lean Canvas, JTBD, and experiment planning"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        """Initialize the venture architect agent.

        Args:
            brain: StartupBrain instance for context retrieval.
            llm: Optional LLM client (defaults to Claude).
        """
        super().__init__(brain)
        self.llm = llm or get_llm_client("claude")

    async def execute(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Execute venture architecture analysis.

        Args:
            message: User's message/query.
            context: Optional additional context.

        Returns:
            AgentResponse with analysis and recommendations.
        """
        venture_snapshot = await self.get_venture_snapshot()
        retrieval_context = await self.get_context(message, max_chunks=15)

        formatted_context = self.format_context_for_prompt(retrieval_context)
        venture_info = self._format_venture(venture_snapshot)
        entities_info = self._format_entities(venture_snapshot.get("entities", {}))

        user_message = f"""## Venture Profile
{venture_info}

## Knowledge Graph
{entities_info}

## Relevant Documents
{formatted_context}

---

Request: {message}

Please provide:
1. Your analysis addressing the request
2. Key assumptions that need validation
3. Recommended experiments or next steps"""

        messages = self._build_messages(context, user_message)

        response_text = await self.llm.complete(
            messages=messages,
            system=VENTURE_ARCHITECT_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=8192,
        )

        citations = self._build_citations(retrieval_context)

        return AgentResponse(
            content=response_text,
            agent_id=self.name,
            citations=citations,
            confidence=0.85,
        )

    def _format_venture(self, snapshot: dict[str, Any]) -> str:
        """Format venture details for prompt."""
        venture = snapshot.get("venture")
        if not venture:
            return "No venture profile loaded."

        return f"""- **Name**: {venture.get('name', 'Unknown')}
- **Stage**: {venture.get('stage', 'Unknown')}
- **One-liner**: {venture.get('one_liner', 'N/A')}
- **Problem**: {venture.get('problem', 'N/A')}
- **Solution**: {venture.get('solution', 'N/A')}"""

    def _format_entities(self, entities: dict[str, list]) -> str:
        """Format KG entities for prompt."""
        if not entities:
            return "No entities in knowledge graph."

        parts = []
        for entity_type, items in entities.items():
            if items:
                parts.append(f"\n### {entity_type.title()}")
                for item in items[:5]:
                    data = item.get("data", {})
                    parts.append(f"- {data}")

        return "\n".join(parts) if parts else "No entities found."

    def _build_messages(
        self, context: dict[str, Any] | None, user_message: str
    ) -> list[dict[str, str]]:
        """Build message list including history."""
        messages = []
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        return messages

    def _build_citations(self, retrieval_context: dict[str, Any]) -> list[Citation]:
        """Build citations from retrieval context."""
        return [
            Citation(
                chunk_id=c.get("chunk_id", ""),
                document_id=c.get("document_id", ""),
                snippet=c.get("snippet", ""),
                score=c.get("score", 0.0),
            )
            for c in retrieval_context.get("citations", [])
        ]
