import asyncio
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.brain.kg.knowledge_graph import KnowledgeGraph, knowledge_graph
from app.core.brain.rag.retriever import RAGRetriever, rag_retriever
from app.models.kg_entity import KGEntity, KGEntityType
from app.schemas.brain import BrainSearchResponse, EntityResult

logger = structlog.get_logger()


class StartupBrain:
    """Unified retrieval layer combining RAG + Knowledge Graph."""

    def __init__(self, rag: RAGRetriever, kg: KnowledgeGraph) -> None:
        self.rag = rag
        self.kg = kg

    async def retrieve(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        query: str,
        query_embedding: list[float],
        entity_types: list[KGEntityType] | None = None,
        max_chunks: int = 10,
    ) -> BrainSearchResponse:
        """Run RAG search and KG search in parallel, combine results."""
        chunks_coro = self.rag.search(db, venture_id, query_embedding, max_chunks)
        entities_coro = self.kg.search_entities(
            db, venture_id, keyword=query, entity_types=entity_types
        )

        chunks, entities = await asyncio.gather(chunks_coro, entities_coro)

        entity_results = [self._entity_to_result(e) for e in entities]

        citations: list[dict[str, Any]] = [
            {"chunk_id": c.chunk_id, "document_id": c.document_id, "score": c.final_score}
            for c in chunks
        ]

        return BrainSearchResponse(
            chunks=chunks,
            entities=entity_results,
            citations=citations,
        )

    async def get_snapshot(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
    ) -> tuple[list[KGEntity], int]:
        """Get all entities for a venture grouped for profile view."""
        entities = await self.kg.get_entities_by_venture(db, venture_id)
        return entities, len(entities)

    @staticmethod
    def _entity_to_result(entity: KGEntity) -> EntityResult:
        return EntityResult(
            id=str(entity.id),
            type=entity.type,
            status=entity.status,
            data=entity.data or {},
            confidence=entity.confidence,
            evidence_count=len(entity.evidence) if entity.evidence else 0,
        )

    @staticmethod
    def group_entities_by_type(
        entities: list[KGEntity],
    ) -> dict[str, list[EntityResult]]:
        """Group entities by type for the profile response."""
        grouped: dict[str, list[EntityResult]] = {}
        for entity in entities:
            key = entity.type.value
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(StartupBrain._entity_to_result(entity))
        return grouped


startup_brain = StartupBrain(rag=rag_retriever, kg=knowledge_graph)
