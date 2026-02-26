import abc
import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any

import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.brain.startup_brain import StartupBrain
from app.core.router.types import RoutingPlan
from app.core.skills.skill_loader import skill_loader
from app.core.tools.executor import ToolExecutor
from app.core.tools.registry import tool_registry
from app.models.kg_entity import KGEntityType
from app.models.venture import Venture, VentureStage
from app.schemas.brain import ChunkResult, EntityResult
from app.services.embedding_service import embedding_service

logger = structlog.get_logger()

CITATION_PATTERN = re.compile(r"\[Source:\s*([^\]]+)\]")
UPDATE_PATTERN = re.compile(r"<!--\s*PROPOSED_UPDATE:\s*(\{.*?\})\s*-->", re.DOTALL)

MAX_TOOL_ROUNDS = 5


class AgentConfig(BaseModel):
    id: str
    name: str
    description: str
    supported_stages: list[VentureStage]
    required_context: list[KGEntityType]
    can_create_artifacts: list[str]
    max_tool_rounds: int = MAX_TOOL_ROUNDS


class AgentResponse(BaseModel):
    content: str
    artifact_id: str | None = None
    artifact_content: dict[str, Any] | None = None
    citations: list[dict[str, str]] = []
    proposed_updates: list[dict[str, Any]] = []


class BaseAgent(abc.ABC):
    """Abstract base for all specialized agents. Stateless — all context from Brain + DB."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._client: AsyncAnthropic | None = None

    @abc.abstractmethod
    def get_agent_specific_instructions(self) -> str:
        """Return domain-specific system prompt instructions."""

    def _get_client(self) -> AsyncAnthropic:
        """Lazy-init the async Anthropic client."""
        if self._client is None:
            self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def execute(
        self,
        prompt: str,
        brain: StartupBrain,
        db: AsyncSession,
        venture: Venture,
        routing_plan: RoutingPlan,
        session_id: str,
        user_id: str,
        use_tools: bool = True,
    ) -> AgentResponse:
        """Execute the agent: retrieve context, call Claude, extract structured output.

        Args:
            use_tools: If False, agent runs without tools (used for delegation).
        """
        query_embedding = await asyncio.to_thread(
            embedding_service.embed_text, prompt
        )

        retrieve_result = await brain.retrieve(
            db=db,
            venture_id=venture.id,
            query=prompt,
            query_embedding=query_embedding,
            entity_types=self.config.required_context or None,
            max_chunks=5,
        )

        entities_raw, _ = await brain.get_snapshot(db=db, venture_id=venture.id)
        entity_results = [brain._entity_to_result(e) for e in entities_raw]
        filtered = [
            e for e in entity_results
            if e.type in self.config.required_context
        ]

        system_prompt = self._build_system_prompt(
            venture=venture,
            entities=filtered,
            chunks=retrieve_result.chunks,
        )

        # Check if this agent has tools configured (and tools are enabled)
        tools = tool_registry.get_tools_for_agent(self.config.id) if use_tools else []
        if tools:
            executor = ToolExecutor(
                registry=tool_registry,
                db=db,
                brain=brain,
                venture=venture,
                user_id=user_id,
                agent_id=self.config.id,
            )
            response_text = await self._call_claude_with_tools(
                system_prompt, prompt, tools, executor,
            )
        else:
            response_text = await self._call_claude(system_prompt, prompt)

        citations = self._extract_citations(response_text)
        proposed_updates = self._extract_proposed_updates(response_text)

        clean_content = UPDATE_PATTERN.sub("", response_text).strip()

        return AgentResponse(
            content=clean_content,
            citations=citations,
            proposed_updates=proposed_updates,
        )

    def _build_system_prompt(
        self,
        venture: Venture,
        entities: list[EntityResult],
        chunks: list[ChunkResult],
    ) -> str:
        """Build the full system prompt with venture context + agent instructions."""
        parts: list[str] = [
            f"You are {self.config.name}, part of the AI VC Co-Pilot platform.",
        ]

        # Tier 1: Inject agent skill (SKILL.md) + relevant shared skills
        agent_skill = skill_loader.load_agent_skill(self.config.id)
        if agent_skill:
            parts.append(f"\n## Domain Expertise\n{agent_skill}")
        shared_skills = skill_loader.load_shared_skills(self.config.id)
        if shared_skills:
            parts.append(f"\n## Shared Knowledge\n{shared_skills}")

        parts.append(f"Venture: {venture.name}")
        parts.append(f"Stage: {venture.stage.value}")

        if venture.one_liner:
            parts.append(f"One-liner: {venture.one_liner}")

        if entities:
            parts.append("\n## Known Entities")
            for entity in entities[:20]:
                name = entity.data.get("name", "unnamed")
                parts.append(
                    f"- [{entity.type.value}] {name} "
                    f"(confidence: {entity.confidence:.2f})"
                )

        if chunks:
            parts.append("\n## Relevant Context (from documents)")
            for chunk in chunks[:5]:
                snippet = chunk.content[:300]
                parts.append(
                    f"- [Source: {chunk.document_id}] {snippet}"
                )

        parts.append(f"\n## Your Instructions\n{self.get_agent_specific_instructions()}")

        parts.append(
            "\n## Response Guidelines"
            "\n- Cite sources using [Source: <document_id>] notation."
            "\n- If you identify new entities or updates, embed them as:"
            "\n  <!-- PROPOSED_UPDATE: {\"entity_type\": \"...\", \"data\": {...}} -->"
            "\n- Be specific and actionable. Ground advice in the venture's data."
        )

        return "\n".join(parts)

    async def execute_streaming(
        self,
        prompt: str,
        brain: StartupBrain,
        db: AsyncSession,
        venture: Venture,
        routing_plan: RoutingPlan,
        session_id: str,
        user_id: str,
    ) -> AsyncIterator[str]:
        """Stream tokens from Claude. Yields text fragments as they arrive."""
        query_embedding = await asyncio.to_thread(
            embedding_service.embed_text, prompt
        )

        retrieve_result = await brain.retrieve(
            db=db,
            venture_id=venture.id,
            query=prompt,
            query_embedding=query_embedding,
            entity_types=self.config.required_context or None,
            max_chunks=5,
        )

        entities_raw, _ = await brain.get_snapshot(db=db, venture_id=venture.id)
        entity_results = [brain._entity_to_result(e) for e in entities_raw]
        filtered = [
            e for e in entity_results
            if e.type in self.config.required_context
        ]

        system_prompt = self._build_system_prompt(
            venture=venture,
            entities=filtered,
            chunks=retrieve_result.chunks,
        )

        # Check if this agent has tools configured
        tools = tool_registry.get_tools_for_agent(self.config.id)
        if tools:
            executor = ToolExecutor(
                registry=tool_registry,
                db=db,
                brain=brain,
                venture=venture,
                user_id=user_id,
                agent_id=self.config.id,
            )
            async for token in self._stream_claude_with_tools(
                system_prompt, prompt, tools, executor,
            ):
                yield token
        else:
            async for token in self._stream_claude(system_prompt, prompt):
                yield token

    async def _call_claude(self, system: str, prompt: str) -> str:
        """Call Claude with the system prompt and user message (no tools)."""
        client = self._get_client()
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        content_block = response.content[0]
        result: str = content_block.text  # type: ignore[union-attr]
        return result

    async def _call_claude_with_tools(
        self,
        system: str,
        prompt: str,
        tools: list[dict[str, Any]],
        executor: ToolExecutor,
    ) -> str:
        """Call Claude with tools, handling the tool_use/tool_result loop.

        Claude may respond with tool_use blocks. We execute each tool,
        send results back, and let Claude continue reasoning. This loops
        up to max_tool_rounds times.
        """
        client = self._get_client()
        messages: list[Any] = [{"role": "user", "content": prompt}]
        max_rounds = self.config.max_tool_rounds
        text_parts: list[str] = []

        for round_num in range(max_rounds):
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=tools,  # type: ignore[arg-type]
            )

            # Separate text and tool_use blocks
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]

            for tb in text_blocks:
                text_parts.append(tb.text)

            if not tool_use_blocks:
                # No tool calls — done
                break

            # Append assistant response (with tool_use blocks) to messages
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and build tool_result messages
            tool_results: list[dict[str, Any]] = []
            for tool_block in tool_use_blocks:
                logger.info(
                    "tool_call",
                    agent=self.config.id,
                    tool=tool_block.name,
                    round=round_num + 1,
                )
                result = await executor.execute(
                    tool_name=tool_block.name,
                    tool_input=tool_block.input,  # type: ignore[arg-type]
                )
                serialized = tool_registry._truncate_result(tool_block.name, result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": serialized,
                })

            messages.append({"role": "user", "content": tool_results})

        return "".join(text_parts)

    async def _stream_claude(self, system: str, prompt: str) -> AsyncIterator[str]:
        """Stream Claude response token by token (no tools)."""
        client = self._get_client()
        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def _stream_claude_with_tools(
        self,
        system: str,
        prompt: str,
        tools: list[dict[str, Any]],
        executor: ToolExecutor,
    ) -> AsyncIterator[str]:
        """Stream Claude response with tool support.

        Yields text tokens and special markers for tool activity.
        Tool calls pause the stream, execute, then resume.
        """
        client = self._get_client()
        messages: list[Any] = [{"role": "user", "content": prompt}]
        max_rounds = self.config.max_tool_rounds

        for round_num in range(max_rounds):
            async with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=tools,  # type: ignore[arg-type]
            ) as stream:
                async for text in stream.text_stream:
                    yield text

            # After stream completes, check for tool use
            final_message = await stream.get_final_message()
            tool_blocks = [b for b in final_message.content if b.type == "tool_use"]

            if not tool_blocks:
                return

            # Execute tools
            messages.append({
                "role": "assistant",
                "content": final_message.content,
            })
            tool_results: list[dict[str, Any]] = []
            for tb in tool_blocks:
                logger.info(
                    "streaming_tool_call",
                    agent=self.config.id,
                    tool=tb.name,
                    round=round_num + 1,
                )
                # Emit tool call marker for SSE
                yield f"__TOOL_CALL__{tb.name}"

                result = await executor.execute(tb.name, tb.input)  # type: ignore[arg-type]
                serialized = tool_registry._truncate_result(tb.name, result)

                yield f"__TOOL_RESULT__{tb.name}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": serialized,
                })
            messages.append({"role": "user", "content": tool_results})

    @staticmethod
    def _extract_citations(text: str) -> list[dict[str, str]]:
        """Extract [Source: doc_id] citations from response text."""
        matches = CITATION_PATTERN.findall(text)
        seen: set[str] = set()
        citations: list[dict[str, str]] = []
        for doc_id in matches:
            doc_id = doc_id.strip()
            if doc_id not in seen:
                seen.add(doc_id)
                citations.append({"document_id": doc_id})
        return citations

    @staticmethod
    def _extract_proposed_updates(text: str) -> list[dict[str, Any]]:
        """Extract <!-- PROPOSED_UPDATE: {...} --> markers from response text."""
        matches = UPDATE_PATTERN.findall(text)
        updates: list[dict[str, Any]] = []
        for match in matches:
            try:
                parsed: dict[str, Any] = json.loads(match)
                updates.append(parsed)
            except json.JSONDecodeError:
                logger.warning("proposed_update_invalid_json", raw_preview=match[:200])
        return updates
