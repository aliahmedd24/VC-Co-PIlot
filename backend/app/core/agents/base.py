"""Base agent abstract class."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from app.core.agents.response import AgentResponse, Citation
from app.core.brain.startup_brain import StartupBrain
from app.core.tools.registry import tool_registry
from app.config import settings


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

    def get_default_tools(self) -> list[str]:
        """Get the list of default tools for this agent.

        Override in subclasses to specify which tools the agent should have access to.
        Available tools: web_search, calculator, extract_entities, query_knowledge_graph

        Returns:
            List of tool names (empty list means no tools)
        """
        return []

    async def execute_with_tools(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        available_tools: list[str] | None = None,
        max_iterations: int | None = None,
    ) -> AgentResponse:
        """Execute agent with tool calling loop.

        This method enables the agent to autonomously use tools during execution.
        It implements a multi-step loop where:
        1. LLM is called with tool definitions
        2. If LLM requests tool use, tools are executed
        3. Tool results are fed back to the LLM
        4. Loop continues until LLM returns final answer (max iterations limit)

        Args:
            message: User's message/query
            context: Optional context (e.g., chat history)
            available_tools: List of tool names to make available (defaults to get_default_tools())
            max_iterations: Maximum tool calling iterations (defaults to settings.max_tool_iterations)

        Returns:
            AgentResponse with content, citations from all tools, and metadata
        """
        # Check if tool use is enabled
        if not settings.enable_tool_use:
            # Fall back to regular execution
            return await self.execute(message, context)

        # Import LLM client here to avoid circular dependency
        from app.core.agents.llm_client import get_llm_client

        # Get LLM client
        llm = get_llm_client("claude")

        # Get brain context
        brain_context = await self.get_context(message)
        snapshot = await self.get_venture_snapshot()

        # Determine which tools to use
        if available_tools is None:
            available_tools = self.get_default_tools()

        if not available_tools:
            # No tools, fall back to regular execution
            return await self.execute(message, context)

        # Get tool definitions
        tool_definitions = tool_registry.get_definitions(available_tools)
        tool_schemas = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema
            }
            for t in tool_definitions
        ]

        # Build initial messages
        messages = []

        # Add chat history if provided
        if context and "history" in context:
            history = context["history"][-10:]  # Last 10 messages for context
            for msg in history:
                messages.append(msg)

        # Add user message with context
        user_message = self._build_user_message_with_context(message, brain_context, snapshot)
        messages.append({"role": "user", "content": user_message})

        # Tool execution loop
        all_citations = []
        tool_execution_log = []
        iterations = 0
        max_iters = max_iterations or settings.max_tool_iterations
        final_content = ""

        while iterations < max_iters:
            iterations += 1

            # Call LLM with tools
            try:
                response = await llm.complete_with_tools(
                    messages=messages,
                    tools=tool_schemas,
                    system=self._get_system_prompt(),
                    temperature=0.7,
                    max_tokens=4096
                )
            except Exception as e:
                # If tool calling fails, fall back to regular execution
                return AgentResponse(
                    content=f"Error during tool execution: {str(e)}. Falling back to standard response.",
                    agent_id=self.name,
                    citations=[],
                    confidence=0.5
                )

            # Check if there are tool calls
            if not response["tool_calls"]:
                # No more tool calls, we have the final answer
                final_content = response["content"]
                break

            # Add assistant message with tool calls
            assistant_message = {"role": "assistant", "content": []}

            # Add text content if present
            if response["content"]:
                assistant_message["content"].append({
                    "type": "text",
                    "text": response["content"]
                })

            # Add tool use blocks
            for tool_call in response["tool_calls"]:
                assistant_message["content"].append({
                    "type": "tool_use",
                    "id": tool_call["id"],
                    "name": tool_call["name"],
                    "input": tool_call["input"]
                })

            messages.append(assistant_message)

            # Execute tools
            tool_results_message = {"role": "user", "content": []}

            for tool_call in response["tool_calls"]:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]
                tool_id = tool_call["id"]

                # Execute tool with brain context
                result = await tool_registry.execute(
                    tool_name,
                    **tool_input,
                    brain=self.brain  # Pass brain for KG queries
                )

                # Log tool execution
                tool_execution_log.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "success": result.success,
                    "error": result.error
                })

                # Collect citations from successful tool calls
                if result.success and result.citations:
                    all_citations.extend([
                        Citation(
                            chunk_id=None,
                            document_id=None,
                            snippet=c.get("snippet", ""),
                            relevance=c.get("relevance", 0.5),
                            metadata=c
                        )
                        for c in result.citations
                    ])

                # Add tool result to message
                tool_result_content = str(result.result) if result.success else f"Error: {result.error}"
                tool_results_message["content"].append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": tool_result_content
                })

            messages.append(tool_results_message)

        # If we hit max iterations without final answer, get one more response
        if iterations >= max_iters and not final_content:
            try:
                final_response = await llm.complete(
                    messages=[
                        {"role": "user", "content": "Based on the tool results above, provide your final answer."}
                    ] + messages,
                    system=self._get_system_prompt(),
                    temperature=0.7,
                    max_tokens=2048
                )
                final_content = final_response
            except Exception:
                final_content = "Unable to generate final response after tool execution."

        # Add citations from brain context
        context_citations = self._extract_citations_from_context(brain_context)
        all_citations.extend(context_citations)

        # Build final response
        return AgentResponse(
            content=final_content,
            agent_id=self.name,
            citations=all_citations,
            confidence=0.8,
            metadata={
                "tool_calls_made": len(tool_execution_log),
                "iterations": iterations,
                "tools_used": list(set(log["tool"] for log in tool_execution_log)),
                "tool_execution_log": tool_execution_log
            }
        )

    def _build_user_message_with_context(
        self,
        message: str,
        brain_context: dict[str, Any],
        snapshot: dict[str, Any]
    ) -> str:
        """Build user message with context from brain.

        Args:
            message: Original user message
            brain_context: Context from brain.retrieve()
            snapshot: Venture snapshot

        Returns:
            Formatted message with context
        """
        parts = [message]

        # Add venture snapshot
        if snapshot and snapshot.get("venture"):
            venture_info = snapshot["venture"]
            parts.append(f"\n\n## Venture Context")
            if venture_info.get("name"):
                parts.append(f"\nVenture: {venture_info['name']}")
            if venture_info.get("problem"):
                parts.append(f"\nProblem: {venture_info['problem']}")
            if venture_info.get("solution"):
                parts.append(f"\nSolution: {venture_info['solution']}")

        # Add relevant context
        formatted_context = self.format_context_for_prompt(brain_context)
        if formatted_context != "No relevant context found.":
            parts.append(f"\n\n{formatted_context}")

        return "\n".join(parts)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent.

        Override in subclasses to customize the system prompt.

        Returns:
            System prompt string
        """
        return f"""You are {self.name}, an AI assistant specializing in: {self.description}

When using tools:
- Use query_knowledge_graph FIRST to check existing information
- Use web_search for current/external information not in the knowledge base
- Use calculator for mathematical operations and financial calculations
- Use extract_entities to structure unstructured data

Be thorough, accurate, and cite your sources."""

    def _extract_citations_from_context(self, context: dict[str, Any]) -> list[Citation]:
        """Extract citations from brain context.

        Args:
            context: Context from brain.retrieve()

        Returns:
            List of Citation objects
        """
        citations = []
        for cite in context.get("citations", []):
            citations.append(Citation(
                chunk_id=cite.get("chunk_id"),
                document_id=cite.get("document_id"),
                snippet=cite.get("snippet", ""),
                relevance=cite.get("relevance", 0.5)
            ))
        return citations
