"""Base agent abstract class."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from app.core.agents.response import AgentResponse
from app.core.brain.startup_brain import StartupBrain


class BaseAgent(ABC):
    """Abstract base class for all agents.

    All agents must:
    - Define a unique `name` and `description`
    - Implement `execute()` for synchronous responses
    - Optionally implement `stream()` for streaming responses
    - Use the injected `brain` for context retrieval
    """

    name: str = "base_agent"
    description: str = "Base agent class"

    def __init__(self, brain: StartupBrain):
        """Initialize agent with a StartupBrain instance.

        Args:
            brain: StartupBrain instance for context retrieval.
        """
        self.brain = brain

    @abstractmethod
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
            AgentResponse with content, citations, and suggested entities.
        """
        pass

    async def stream(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream the agent's response token by token.

        Default implementation calls execute() and yields the full response.
        Override for true streaming support.

        Args:
            message: User's message/query.
            context: Optional additional context.

        Yields:
            Response content chunks.
        """
        response = await self.execute(message, context)
        yield response.content

    async def get_context(
        self,
        query: str,
        max_chunks: int = 10,
    ) -> dict[str, Any]:
        """Retrieve context from the brain for the given query.

        Args:
            query: Search query string.
            max_chunks: Maximum document chunks to retrieve.

        Returns:
            Dict with 'chunks', 'entities', and 'citations'.
        """
        return await self.brain.retrieve(query, max_chunks=max_chunks)

    async def get_venture_snapshot(self) -> dict[str, Any]:
        """Get the current venture state snapshot.

        Returns:
            Dict with 'venture', 'entities', and 'metrics'.
        """
        return await self.brain.get_snapshot()

    def format_context_for_prompt(self, context: dict[str, Any]) -> str:
        """Format retrieved context for inclusion in LLM prompt.

        Args:
            context: Context dict from get_context().

        Returns:
            Formatted string for the prompt.
        """
        parts = []

        # Add document chunks
        chunks = context.get("chunks", [])
        if chunks:
            parts.append("## Relevant Documents\n")
            for i, chunk in enumerate(chunks[:5], 1):
                content = getattr(chunk, "content", str(chunk))[:500]
                parts.append(f"[{i}] {content}\n")

        # Add KG entities
        entities = context.get("entities", [])
        if entities:
            parts.append("\n## Knowledge Graph Entities\n")
            for entity in entities[:10]:
                entity_type = getattr(entity, "type", "unknown")
                entity_data = getattr(entity, "data", {})
                parts.append(f"- {entity_type}: {entity_data}\n")

        return "".join(parts) if parts else "No relevant context found."
