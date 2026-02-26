import uuid
from typing import Any

import structlog
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.brain.events.event_store import EventStore, event_store
from app.models.kg_entity import (
    KGEntity,
    KGEntityStatus,
    KGEntityType,
    KGEvidence,
    KGRelation,
    KGRelationType,
)
from app.models.kg_event import KGEventType

logger = structlog.get_logger()


class KnowledgeGraph:
    """CRUD operations on KG entities, always routed through the EventStore."""

    CONFIDENCE_CONFIRMED = 0.85
    CONFIDENCE_NEEDS_REVIEW = 0.60
    MAX_ENTITIES_PER_TYPE = 50

    def __init__(self, events: EventStore) -> None:
        self.events = events

    def _auto_status(self, confidence: float) -> KGEntityStatus:
        """Determine entity status based on confidence score."""
        if confidence >= self.CONFIDENCE_CONFIRMED:
            return KGEntityStatus.CONFIRMED
        elif confidence >= self.CONFIDENCE_NEEDS_REVIEW:
            return KGEntityStatus.NEEDS_REVIEW
        else:
            return KGEntityStatus.SUGGESTED

    async def create_entity(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        entity_type: KGEntityType,
        data: dict[str, Any],
        confidence: float = 0.5,
        actor: str = "system",
        evidence_snippet: str | None = None,
        document_id: uuid.UUID | None = None,
        agent_id: str | None = None,
    ) -> KGEntity:
        """Create a KG entity with auto-status, conflict detection, and event logging."""
        # 1. Enforce max entities per type per venture
        count_result = await db.execute(
            select(func.count())
            .select_from(KGEntity)
            .where(
                KGEntity.venture_id == venture_id,
                KGEntity.type == entity_type,
            )
        )
        count = count_result.scalar_one()
        if count >= self.MAX_ENTITIES_PER_TYPE:
            raise ValueError(
                f"Max {self.MAX_ENTITIES_PER_TYPE} entities of type "
                f"{entity_type.value} per venture"
            )

        # 2. Auto-set status based on confidence
        status = self._auto_status(confidence)

        # 3. Check for conflict (same type with matching name)
        conflict_entity = await self._find_conflict(db, venture_id, entity_type, data)

        # 4. Create entity
        entity = KGEntity(
            venture_id=venture_id,
            type=entity_type,
            status=KGEntityStatus.NEEDS_REVIEW if conflict_entity else status,
            data=data,
            confidence=confidence,
        )
        db.add(entity)
        await db.flush()

        # 5. Create evidence if provided
        if evidence_snippet:
            evidence = KGEvidence(
                entity_id=entity.id,
                snippet=evidence_snippet,
                document_id=document_id,
                source_type="document" if document_id else "manual",
                agent_id=agent_id,
            )
            db.add(evidence)

        # 6. Log creation event
        await self.events.append(
            db=db,
            venture_id=venture_id,
            event_type=KGEventType.ENTITY_CREATED,
            entity_id=str(entity.id),
            payload={"type": entity_type.value, "data": data, "confidence": confidence},
            actor=actor,
        )

        # 7. Handle conflict if detected
        if conflict_entity:
            relation = KGRelation(
                from_entity_id=entity.id,
                to_entity_id=conflict_entity.id,
                type=KGRelationType.CONFLICTS_WITH,
            )
            db.add(relation)

            if conflict_entity.status != KGEntityStatus.PINNED:
                conflict_entity.status = KGEntityStatus.NEEDS_REVIEW

            await self.events.append(
                db=db,
                venture_id=venture_id,
                event_type=KGEventType.CONFLICT_DETECTED,
                entity_id=str(entity.id),
                payload={"conflicting_entity_id": str(conflict_entity.id)},
                actor=actor,
            )
            logger.info(
                "kg_conflict_detected",
                new_entity_id=str(entity.id),
                existing_entity_id=str(conflict_entity.id),
            )

        await db.flush()
        return entity

    async def update_entity(
        self,
        db: AsyncSession,
        entity_id: uuid.UUID,
        data: dict[str, Any] | None = None,
        status: KGEntityStatus | None = None,
        confidence: float | None = None,
        actor: str = "system",
    ) -> KGEntity:
        """Update entity fields, merge data dict, log before/after event."""
        result = await db.execute(
            select(KGEntity).where(KGEntity.id == entity_id)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            raise ValueError("Entity not found")

        before: dict[str, Any] = {
            "data": entity.data,
            "status": entity.status.value,
            "confidence": entity.confidence,
        }

        if data is not None:
            merged = dict(entity.data or {})
            merged.update(data)
            entity.data = merged
        if status is not None:
            entity.status = status
        if confidence is not None:
            entity.confidence = confidence
            if status is None:
                entity.status = self._auto_status(confidence)

        after: dict[str, Any] = {
            "data": entity.data,
            "status": entity.status.value,
            "confidence": entity.confidence,
        }

        event_type = (
            KGEventType.ENTITY_CONFIRMED
            if status == KGEntityStatus.CONFIRMED
            else KGEventType.ENTITY_UPDATED
        )
        await self.events.append(
            db=db,
            venture_id=entity.venture_id,
            event_type=event_type,
            entity_id=str(entity.id),
            payload={"before": before, "after": after},
            actor=actor,
        )

        await db.flush()
        return entity

    async def delete_entity(
        self,
        db: AsyncSession,
        entity_id: uuid.UUID,
        actor: str = "system",
    ) -> None:
        """Delete an entity and log the deletion event."""
        result = await db.execute(
            select(KGEntity).where(KGEntity.id == entity_id)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            raise ValueError("Entity not found")

        await self.events.append(
            db=db,
            venture_id=entity.venture_id,
            event_type=KGEventType.ENTITY_DELETED,
            entity_id=str(entity.id),
            payload={"type": entity.type.value, "data": entity.data},
            actor=actor,
        )

        await db.delete(entity)
        await db.flush()

    async def search_entities(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        keyword: str | None = None,
        entity_types: list[KGEntityType] | None = None,
        limit: int = 20,
    ) -> list[KGEntity]:
        """Search entities by keyword in data and/or type filter."""
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.venture_id == venture_id)
        )
        if entity_types:
            stmt = stmt.where(KGEntity.type.in_(entity_types))
        if keyword:
            stmt = stmt.where(
                cast(KGEntity.data, String).ilike(f"%{keyword}%")
            )
        stmt = stmt.order_by(KGEntity.confidence.desc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_entities_by_venture(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
    ) -> list[KGEntity]:
        """Get all entities for a venture, ordered by type then confidence."""
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.venture_id == venture_id)
            .order_by(KGEntity.type, KGEntity.confidence.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_entity(
        self,
        db: AsyncSession,
        entity_id: uuid.UUID,
    ) -> KGEntity | None:
        """Get a single entity by ID with evidence loaded."""
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.id == entity_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_entities_advanced(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        keyword: str | None = None,
        entity_types: list[KGEntityType] | None = None,
        min_confidence: float = 0.0,
        status_filter: KGEntityStatus | None = None,
        stale_days: int | None = None,
        limit: int = 20,
    ) -> list[KGEntity]:
        """Search entities with advanced filtering beyond basic search_entities.

        Args:
            keyword: Text search within entity data JSON.
            entity_types: Filter by entity types.
            min_confidence: Minimum confidence threshold (0.0-1.0).
            status_filter: Filter by entity status.
            stale_days: If set, only return entities not updated in N days.
            limit: Max entities to return (capped at 50).
        """
        from datetime import UTC, datetime, timedelta

        limit = min(limit, 50)
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.venture_id == venture_id)
        )

        if entity_types:
            stmt = stmt.where(KGEntity.type.in_(entity_types))
        if keyword:
            stmt = stmt.where(
                cast(KGEntity.data, String).ilike(f"%{keyword}%")
            )
        if min_confidence > 0.0:
            stmt = stmt.where(KGEntity.confidence >= min_confidence)
        if status_filter is not None:
            stmt = stmt.where(KGEntity.status == status_filter)
        if stale_days is not None:
            cutoff = datetime.now(UTC) - timedelta(days=stale_days)
            stmt = stmt.where(KGEntity.updated_at < cutoff)

        stmt = stmt.order_by(KGEntity.confidence.desc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_relations(
        self,
        db: AsyncSession,
        entity_ids: list[uuid.UUID],
        relation_type: KGRelationType | None = None,
        direction: str = "both",
    ) -> list[KGRelation]:
        """Query relations for given entity IDs with optional filtering.

        Args:
            entity_ids: Entity IDs to find relations for.
            relation_type: Optional filter by relation type.
            direction: 'outgoing', 'incoming', or 'both'.
        """
        from sqlalchemy import or_

        stmt = select(KGRelation)

        if direction == "outgoing":
            stmt = stmt.where(KGRelation.from_entity_id.in_(entity_ids))
        elif direction == "incoming":
            stmt = stmt.where(KGRelation.to_entity_id.in_(entity_ids))
        else:
            stmt = stmt.where(
                or_(
                    KGRelation.from_entity_id.in_(entity_ids),
                    KGRelation.to_entity_id.in_(entity_ids),
                )
            )

        if relation_type is not None:
            stmt = stmt.where(KGRelation.type == relation_type)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def traverse(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        entity_type: KGEntityType,
        entity_name: str | None = None,
        relation_type: KGRelationType | None = None,
        direction: str = "both",
        start_limit: int = 10,
    ) -> dict[str, Any]:
        """Traverse KG relations from entities matching criteria.

        Combines entity lookup, relation query, and connected entity loading
        into a single encapsulated operation.

        Returns:
            Dict with start_entities count, relation_count, and detailed
            relations list including from/to entity data.
        """
        # 1. Find starting entities
        stmt = (
            select(KGEntity)
            .where(
                KGEntity.venture_id == venture_id,
                KGEntity.type == entity_type,
            )
        )
        if entity_name:
            stmt = stmt.where(
                cast(KGEntity.data, String).ilike(f"%{entity_name}%")
            )
        stmt = stmt.limit(start_limit)
        result = await db.execute(stmt)
        start_entities = list(result.scalars().all())

        if not start_entities:
            return {
                "start_entities": 0,
                "relation_count": 0,
                "relations": [],
                "message": f"No {entity_type.value} entities found matching criteria.",
            }

        entity_ids = [e.id for e in start_entities]

        # 2. Find relations
        relations = await self.get_relations(db, entity_ids, relation_type, direction)

        # 3. Fetch connected entities
        connected_ids = set()
        for rel in relations:
            connected_ids.add(rel.from_entity_id)
            connected_ids.add(rel.to_entity_id)
        connected_ids -= set(entity_ids)

        connected_entities: dict[str, dict[str, Any]] = {}
        if connected_ids:
            conn_stmt = select(KGEntity).where(KGEntity.id.in_(list(connected_ids)))
            conn_result = await db.execute(conn_stmt)
            for e in conn_result.scalars().all():
                connected_entities[str(e.id)] = {
                    "type": e.type.value,
                    "data": e.data,
                    "confidence": e.confidence,
                }

        # Build start entity lookup
        start_lookup: dict[str, dict[str, Any]] = {}
        for e in start_entities:
            start_lookup[str(e.id)] = {
                "type": e.type.value,
                "data": e.data,
                "confidence": e.confidence,
            }

        return {
            "start_entities": len(start_entities),
            "relation_count": len(relations),
            "relations": [
                {
                    "from": start_lookup.get(
                        str(r.from_entity_id),
                        connected_entities.get(str(r.from_entity_id), {}),
                    ),
                    "to": start_lookup.get(
                        str(r.to_entity_id),
                        connected_entities.get(str(r.to_entity_id), {}),
                    ),
                    "type": r.type.value,
                    "metadata": r.relation_metadata,
                }
                for r in relations
            ],
        }

    async def _find_conflict(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        entity_type: KGEntityType,
        data: dict[str, Any],
    ) -> KGEntity | None:
        """Find an existing entity of the same type with a matching name field."""
        name = data.get("name")
        if not name or not isinstance(name, str):
            return None
        stmt = (
            select(KGEntity)
            .where(
                KGEntity.venture_id == venture_id,
                KGEntity.type == entity_type,
                cast(KGEntity.data, String).ilike(f"%{name}%"),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


knowledge_graph = KnowledgeGraph(event_store)

