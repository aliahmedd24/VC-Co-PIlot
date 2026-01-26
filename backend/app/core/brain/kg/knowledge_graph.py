"""Knowledge Graph operations for venture entities."""

from typing import Any
from uuid import uuid4

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.kg_entity import (
    KGEntity,
    KGEntityStatus,
    KGEntityType,
    KGEvidence,
    KGRelation,
)


class KnowledgeGraph:
    """Knowledge Graph operations for a specific venture."""

    def __init__(self, venture_id: str, session: AsyncSession):
        self.venture_id = venture_id
        self.session = session

    async def create_entity(
        self,
        type: KGEntityType,
        data: dict[str, Any],
        confidence: float = 0.5,
        status: KGEntityStatus | None = None,
    ) -> KGEntity:
        """Create a new KG entity with automatic status based on confidence."""
        if status is None:
            if confidence >= 0.85:
                status = KGEntityStatus.CONFIRMED
            elif confidence >= 0.6:
                status = KGEntityStatus.NEEDS_REVIEW
            else:
                status = KGEntityStatus.SUGGESTED

        entity = KGEntity(
            id=str(uuid4()),
            venture_id=self.venture_id,
            type=type,
            data=data,
            confidence=confidence,
            status=status,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_entity(self, entity_id: str) -> KGEntity | None:
        """Get an entity by ID with evidence eagerly loaded."""
        result = await self.session.execute(
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.id == entity_id, KGEntity.venture_id == self.venture_id)
        )
        return result.scalar_one_or_none()

    async def update_entity(
        self,
        entity_id: str,
        updates: dict[str, Any],
        new_confidence: float | None = None,
        new_status: KGEntityStatus | None = None,
    ) -> KGEntity | None:
        """Update an entity's data, optionally updating confidence/status."""
        entity = await self.get_entity(entity_id)
        if not entity:
            return None

        # Merge data updates
        entity.data = {**entity.data, **updates}

        if new_confidence is not None:
            entity.confidence = new_confidence

        if new_status is not None:
            entity.status = new_status

        await self.session.flush()
        return entity

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity by ID. Returns True if deleted."""
        result = await self.session.execute(
            delete(KGEntity).where(KGEntity.id == entity_id, KGEntity.venture_id == self.venture_id)
        )
        return result.rowcount > 0

    async def search_entities(
        self,
        query: str,
        types: list[KGEntityType] | None = None,
        include_suggested: bool = False,
    ) -> list[KGEntity]:
        """Search entities by keyword matching in data."""
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.venture_id == self.venture_id)
        )

        if not include_suggested:
            stmt = stmt.where(KGEntity.status != KGEntityStatus.SUGGESTED)

        if types:
            stmt = stmt.where(KGEntity.type.in_(types))

        result = await self.session.execute(stmt)
        entities = list(result.scalars().all())

        # Simple keyword search in JSON data
        if query:
            keywords = query.lower().split()
            entities = [e for e in entities if any(kw in str(e.data).lower() for kw in keywords)]

        return entities

    async def get_entities_by_type(
        self, types: list[KGEntityType] | None = None
    ) -> list[KGEntity]:
        """Get all entities, optionally filtered by type."""
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.venture_id == self.venture_id)
        )

        if types:
            stmt = stmt.where(KGEntity.type.in_(types))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_relations(self, entity_ids: list[str]) -> list[KGRelation]:
        """Get relations involving any of the given entity IDs."""
        if not entity_ids:
            return []

        result = await self.session.execute(
            select(KGRelation).where(
                or_(
                    KGRelation.from_entity_id.in_(entity_ids),
                    KGRelation.to_entity_id.in_(entity_ids),
                )
            )
        )
        return list(result.scalars().all())

    async def create_relation(
        self,
        from_entity_id: str,
        to_entity_id: str,
        relation_type: str,
        data: dict[str, Any] | None = None,
    ) -> KGRelation:
        """Create a relation between two entities."""
        relation = KGRelation(
            id=str(uuid4()),
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            relation_type=relation_type,
            data=data,
        )
        self.session.add(relation)
        await self.session.flush()
        return relation

    async def add_evidence(
        self,
        entity_id: str,
        snippet: str,
        source_type: str,
        document_id: str | None = None,
        agent_id: str | None = None,
    ) -> KGEvidence:
        """Add evidence to support an entity."""
        evidence = KGEvidence(
            id=str(uuid4()),
            entity_id=entity_id,
            snippet=snippet,
            source_type=source_type,
            document_id=document_id,
            agent_id=agent_id,
        )
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def detect_conflicts(
        self, entity_type: KGEntityType, data: dict[str, Any]
    ) -> list[KGEntity]:
        """
        Detect potential conflicts with existing entities.
        Returns entities that might be duplicates or contradictory.
        """
        # Get all entities of the same type
        existing = await self.get_entities_by_type([entity_type])

        conflicts = []
        new_name = str(data.get("name", "")).lower()

        for entity in existing:
            existing_name = str(entity.data.get("name", "")).lower()

            # Check for name similarity (simple duplicate detection)
            if new_name and existing_name:
                # Exact match
                if new_name == existing_name or (new_name in existing_name or existing_name in new_name):
                    conflicts.append(entity)

        return conflicts
