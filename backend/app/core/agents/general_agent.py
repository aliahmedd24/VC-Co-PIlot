"""General conversational agent for startup questions."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain

GENERAL_AGENT_SYSTEM_PROMPT = """You are an AI VC Co-Pilot assistant helping startups navigate their journey.

You have access to the startup's knowledge base including documents, market research, and structured data.
Always be helpful, constructive, and provide actionable advice.

When answering:
1. Draw from the provided context when relevant
2. Be specific and practical in your advice
3. Cite sources when referencing specific documents
4. If you don't know something, say so honestly
5. Suggest follow-up questions or next steps when appropriate

Format your responses clearly with headers and bullet points when helpful."""


class GeneralAgent(BaseAgent):
    """Default conversational agent for general startup questions.

    This agent handles general inquiries about startups, fundraising,
    product development, and other common VC-related topics.
    """

    name = "general_agent"
    description = "General conversational agent for startup questions and guidance"

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        """Initialize the general agent.

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
        """Execute the agent with the given message.

        Args:
            message: User's message/query.
            context: Optional additional context (e.g., chat history).

        Returns:
            AgentResponse with content and citations.
        """
        # Get venture snapshot and relevant context
        venture_snapshot = await self.get_venture_snapshot()
        retrieval_context = await self.get_context(message)

        # Build the prompt
        formatted_context = self.format_context_for_prompt(retrieval_context)

        venture_info = ""
        venture = venture_snapshot.get("venture")
        if venture:
            venture_info = f"""## Current Venture
- Name: {venture.get('name', 'Unknown')}
- Stage: {venture.get('stage', 'Unknown')}
- One-liner: {venture.get('one_liner', 'N/A')}
"""

        # Build messages
        messages = []

        # Add chat history if provided
        if context and "history" in context:
            for msg in context["history"][-10:]:  # Last 10 messages
                messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                )

        # Add current message with context
        user_message = f"""Context about the startup:
{venture_info}
{formatted_context}

---

User question: {message}"""

        messages.append({"role": "user", "content": user_message})

        # Get LLM response
        response_text = await self.llm.complete(
            messages=messages,
            system=GENERAL_AGENT_SYSTEM_PROMPT,
            temperature=0.7,
        )

        # Build citations from retrieved chunks
        citations = []
        for citation_data in retrieval_context.get("citations", []):
            citations.append(
                Citation(
                    chunk_id=citation_data.get("chunk_id", ""),
                    document_id=citation_data.get("document_id", ""),
                    snippet=citation_data.get("snippet", ""),
                    score=citation_data.get("score", 0.0),
                )
            )

        return AgentResponse(
            content=response_text,
            agent_id=self.name,
            citations=citations,
            confidence=0.8,
        )

    async def stream(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ):
        """Stream the agent's response.

        Args:
            message: User's message/query.
            context: Optional additional context.

        Yields:
            Response content chunks.
        """
        # Get context (same as execute)
        venture_snapshot = await self.get_venture_snapshot()
        retrieval_context = await self.get_context(message)
        formatted_context = self.format_context_for_prompt(retrieval_context)

        venture_info = ""
        venture = venture_snapshot.get("venture")
        if venture:
            venture_info = f"""## Current Venture
- Name: {venture.get('name', 'Unknown')}
- Stage: {venture.get('stage', 'Unknown')}
"""

        messages = []
        if context and "history" in context:
            for msg in context["history"][-10:]:
                messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                )

        user_message = f"""Context:
{venture_info}
{formatted_context}

---

User question: {message}"""

        messages.append({"role": "user", "content": user_message})

        async for chunk in self.llm.stream(
            messages=messages,
            system=GENERAL_AGENT_SYSTEM_PROMPT,
            temperature=0.7,
        ):
            yield chunk
