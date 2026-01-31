"""Startup Brain - unified interface to RAG + Knowledge Graph."""

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.brain.events.event_store import EventStore
from app.core.brain.kg.knowledge_graph import KnowledgeGraph
from app.core.brain.rag.retriever import (
    EmbeddingService,
    RAGRetriever,
    VisualContentWithScore,
)
from app.models.kg_entity import KGEntity, KGEntityType
from app.models.venture import Venture


class StartupBrain:
    """Unified interface to RAG + Knowledge Graph with event sourcing.

    This is the main entry point for agents to access venture context,
    combining document retrieval (RAG) with structured knowledge (KG).
    """

    def __init__(
        self,
        venture_id: str,
        session: AsyncSession,
        embedder: EmbeddingService | None = None,
    ):
        self.venture_id = venture_id
        self.session = session
        self.rag = RAGRetriever(venture_id, session, embedder)
        self.kg = KnowledgeGraph(venture_id, session)
        self.events = EventStore(venture_id, session)

    async def retrieve(
        self,
        query: str,
        max_chunks: int = 10,
        max_visual: int = 5,
        include_visual: bool = True,
        entity_types: list[KGEntityType] | None = None,
        include_relations: bool = True,
    ) -> dict[str, Any]:
        """Unified retrieval combining RAG, visual content, and KG.

        Args:
            query: Search query string.
            max_chunks: Maximum number of document chunks to return.
            max_visual: Maximum number of visual content items to return.
            include_visual: Whether to include visual content search.
            entity_types: Optional filter for KG entity types.
            include_relations: Whether to include entity relations.

        Returns:
            Dict with 'chunks', 'visual_content', 'entities', 'citations', and 'visual_citations'.
        """
        # Run RAG, visual, and KG searches in parallel
        tasks = [
            self.rag.search(query, limit=max_chunks),
            self.kg.search_entities(query, types=entity_types),
        ]

        if include_visual:
            tasks.insert(1, self.rag.search_visual(query, limit=max_visual))
            chunks, visual_content, entities = await asyncio.gather(*tasks)
        else:
            chunks, entities = await asyncio.gather(*tasks)
            visual_content = []

        # Build citations from chunks
        citations = [
            {
                "chunk_id": c.id,
                "document_id": c.document_id,
                "snippet": c.content[:200],
                "score": c.final_score,
            }
            for c in chunks
        ]

        # Build visual citations
        visual_citations = self._format_visual_citations(visual_content)

        # Optionally load relations for entities
        if include_relations and entities:
            entity_ids = [e.id for e in entities]
            relations = await self.kg.get_relations(entity_ids)
            # Attach relations to entities (as attribute for convenience)
            relations_by_entity: dict[str, list] = {}
            for r in relations:
                for eid in [r.from_entity_id, r.to_entity_id]:
                    if eid not in relations_by_entity:
                        relations_by_entity[eid] = []
                    relations_by_entity[eid].append(r)

        return {
            "chunks": chunks,
            "visual_content": visual_content,
            "entities": entities,
            "citations": citations,
            "visual_citations": visual_citations,
        }

    def _format_visual_citations(
        self, visual_results: list[VisualContentWithScore]
    ) -> list[dict[str, Any]]:
        """Format visual content results as citations.

        Args:
            visual_results: List of VisualContentWithScore objects.

        Returns:
            List of citation dicts with visual content info.
        """
        citations = []
        for v in visual_results:
            # Extract snippet from vision analysis or extracted text
            snippet = self._extract_visual_snippet(v)
            citations.append({
                "visual_id": v.id,
                "document_id": v.document_id,
                "page_number": v.page_number,
                "content_type": v.content_type,
                "snippet": snippet,
                "score": v.final_score,
                "thumbnail_key": v.thumbnail_key,
            })
        return citations

    def _extract_visual_snippet(self, visual: VisualContentWithScore) -> str:
        """Extract a text snippet from visual content for display.

        Args:
            visual: VisualContentWithScore object.

        Returns:
            Truncated text snippet.
        """
        # Prefer extracted text if available
        if visual.extracted_text:
            return visual.extracted_text[:200]

        # Fall back to vision analysis content
        if visual.vision_analysis:
            content = visual.vision_analysis.get("content", "")
            if content:
                return content[:200]

        return f"[{visual.content_type} on page {visual.page_number}]"

    async def get_snapshot(
        self, entity_types: list[KGEntityType] | None = None
    ) -> dict[str, Any]:
        """Get current venture state for agent context.

        Returns a structured snapshot of the venture including
        basic info and all KG entities grouped by type.
        """
        # Get venture
        result = await self.session.execute(select(Venture).where(Venture.id == self.venture_id))
        venture = result.scalar_one_or_none()

        if not venture:
            return {"venture": None, "entities": {}, "metrics": None}

        # Get entities grouped by type
        entities = await self.kg.get_entities_by_type(entity_types)

        entities_by_type: dict[str, list[dict]] = {}
        for entity in entities:
            key = entity.type.value
            if key not in entities_by_type:
                entities_by_type[key] = []
            entities_by_type[key].append(
                {
                    "id": entity.id,
                    "data": entity.data,
                    "confidence": entity.confidence,
                    "status": entity.status.value,
                }
            )

        return {
            "venture": {
                "id": venture.id,
                "name": venture.name,
                "stage": venture.stage.value,
                "one_liner": venture.one_liner,
                "problem": venture.problem,
                "solution": venture.solution,
            },
            "entities": entities_by_type,
            "metrics": None,  # TODO: Extract from METRIC entities
        }

    async def propose_updates(
        self,
        entities_data: list[dict[str, Any]],
        agent_id: str | None = None,
        user_id: str | None = None,
    ) -> list[KGEntity]:
        """Propose updates to the knowledge graph.

        Creates entities with SUGGESTED status for human review.
        Logs events for all proposed changes.

        Args:
            entities_data: List of dicts with 'type', 'data', 'confidence'.
            agent_id: ID of the agent proposing changes.
            user_id: ID of the user (if applicable).

        Returns:
            List of created entities.
        """
        from app.models.kg_entity import KGEventType

        created = []
        for item in entities_data:
            entity_type = item.get("type")
            if isinstance(entity_type, str):
                entity_type = KGEntityType(entity_type)

            # Check for conflicts
            conflicts = await self.kg.detect_conflicts(entity_type, item.get("data", {}))

            # Create entity
            entity = await self.kg.create_entity(
                type=entity_type,
                data=item.get("data", {}),
                confidence=item.get("confidence", 0.5),
            )

            # Log event
            await self.events.log_event(
                event_type=KGEventType.CREATE,
                data={
                    "entity_type": entity_type.value,
                    "entity_data": item.get("data", {}),
                    "conflicts": [c.id for c in conflicts],
                },
                entity_id=entity.id,
                agent_id=agent_id,
                user_id=user_id,
            )

            created.append(entity)

        return created
