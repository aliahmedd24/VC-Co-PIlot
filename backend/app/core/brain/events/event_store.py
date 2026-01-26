"""Event Store for KG event sourcing."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kg_entity import KGEvent, KGEventType


class EventStore:
    """Event sourcing for Knowledge Graph mutations."""

    def __init__(self, venture_id: str, session: AsyncSession):
        self.venture_id = venture_id
        self.session = session

    async def log_event(
        self,
        event_type: KGEventType,
        data: dict[str, Any],
        entity_id: str | None = None,
        agent_id: str | None = None,
        user_id: str | None = None,
    ) -> KGEvent:
        """Log a KG mutation event."""
        event = KGEvent(
            id=str(uuid4()),
            venture_id=self.venture_id,
            entity_id=entity_id,
            event_type=event_type,
            data=data,
            agent_id=agent_id,
            user_id=user_id,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_events(
        self,
        entity_id: str | None = None,
        event_types: list[KGEventType] | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[KGEvent]:
        """Query events with optional filters."""
        stmt = (
            select(KGEvent)
            .where(KGEvent.venture_id == self.venture_id)
            .order_by(KGEvent.created_at.desc())
            .limit(limit)
        )

        if entity_id:
            stmt = stmt.where(KGEvent.entity_id == entity_id)

        if event_types:
            stmt = stmt.where(KGEvent.event_type.in_(event_types))

        if since:
            stmt = stmt.where(KGEvent.created_at >= since)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_entity_history(self, entity_id: str) -> list[KGEvent]:
        """Get all events for a specific entity in chronological order."""
        stmt = (
            select(KGEvent)
            .where(
                KGEvent.venture_id == self.venture_id,
                KGEvent.entity_id == entity_id,
            )
            .order_by(KGEvent.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def replay_events(self, since: datetime | None = None) -> dict[str, list[KGEvent]]:
        """
        Get all events grouped by entity_id for state reconstruction.
        Returns dict of entity_id -> list of events in chronological order.
        """
        events = await self.get_events(since=since, limit=10000)

        # Group by entity_id
        by_entity: dict[str, list[KGEvent]] = {}
        for event in reversed(events):  # Reverse to get chronological order
            entity_id = event.entity_id or "_venture_"
            if entity_id not in by_entity:
                by_entity[entity_id] = []
            by_entity[entity_id].append(event)

        return by_entity
