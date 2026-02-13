import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kg_event import KGEvent, KGEventType

logger = structlog.get_logger()


class EventStore:
    """Append-only event log for Knowledge Graph mutations.

    This class provides the ONLY interface for writing KG events.
    There are intentionally no update() or delete() methods — events are immutable.
    """

    async def append(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        event_type: KGEventType,
        entity_id: str | None,
        payload: dict[str, Any],
        actor: str,
    ) -> KGEvent:
        """Append a new immutable event to the log."""
        event = KGEvent(
            venture_id=venture_id,
            event_type=event_type,
            entity_id=entity_id,
            payload=payload,
            actor=actor,
        )
        db.add(event)
        await db.flush()
        logger.info(
            "kg_event_appended",
            event_type=event_type.value,
            entity_id=entity_id,
            venture_id=str(venture_id),
        )
        return event

    async def get_events_by_venture(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        event_type: KGEventType | None = None,
        limit: int = 100,
    ) -> list[KGEvent]:
        """Query events for a venture, optionally filtered by type."""
        stmt = select(KGEvent).where(KGEvent.venture_id == venture_id)
        if event_type is not None:
            stmt = stmt.where(KGEvent.event_type == event_type)
        stmt = stmt.order_by(KGEvent.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_events_by_entity(
        self,
        db: AsyncSession,
        entity_id: str,
        limit: int = 50,
    ) -> list[KGEvent]:
        """Query events for a specific entity."""
        stmt = (
            select(KGEvent)
            .where(KGEvent.entity_id == entity_id)
            .order_by(KGEvent.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


event_store = EventStore()
