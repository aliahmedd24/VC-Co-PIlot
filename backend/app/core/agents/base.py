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
from app.models.kg_entity import KGEntityType
from app.models.venture import Venture, VentureStage
from app.schemas.brain import ChunkResult, EntityResult
from app.services.embedding_service import embedding_service

logger = structlog.get_logger()

CITATION_PATTERN = re.compile(r"\[Source:\s*([^\]]+)\]")
UPDATE_PATTERN = re.compile(r"<!--\s*PROPOSED_UPDATE:\s*(\{.*?\})\s*-->", re.DOTALL)


class AgentConfig(BaseModel):
    id: str
    name: str
    description: str
    supported_stages: list[VentureStage]
    required_context: list[KGEntityType]
    can_create_artifacts: list[str]


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
    ) -> AgentResponse:
        """Execute the agent: retrieve context, call Claude, extract structured output."""
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
            f"Venture: {venture.name}",
            f"Stage: {venture.stage.value}",
        ]

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

        async for token in self._stream_claude(system_prompt, prompt):
            yield token

    async def _call_claude(self, system: str, prompt: str) -> str:
        """Call Claude with the system prompt and user message."""
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

    async def _stream_claude(self, system: str, prompt: str) -> AsyncIterator[str]:
        """Stream Claude response token by token."""
        client = self._get_client()
        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

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
