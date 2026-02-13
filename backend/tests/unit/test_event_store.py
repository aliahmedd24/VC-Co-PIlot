import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.brain.events.event_store import EventStore
from app.models.kg_event import KGEventType
from app.models.venture import Venture
from app.models.workspace import Workspace


async def _create_venture(db: AsyncSession) -> Venture:
    """Helper to create a workspace + venture for tests."""
    workspace = Workspace(name="Test WS", slug=f"test-ws-{uuid.uuid4().hex[:8]}")
    db.add(workspace)
    await db.flush()

    venture = Venture(workspace_id=workspace.id, name="Test Venture")
    db.add(venture)
    await db.flush()
    return venture


@pytest.mark.asyncio
async def test_event_created_on_entity_create(db_session: AsyncSession) -> None:
    """Appending an ENTITY_CREATED event persists with correct fields."""
    store = EventStore()
    venture = await _create_venture(db_session)

    event = await store.append(
        db=db_session,
        venture_id=venture.id,
        event_type=KGEventType.ENTITY_CREATED,
        entity_id="test-entity-123",
        payload={"type": "competitor", "data": {"name": "Acme"}, "confidence": 0.9},
        actor="system",
    )
    await db_session.commit()

    assert event.id is not None
    assert event.venture_id == venture.id
    assert event.event_type == KGEventType.ENTITY_CREATED
    assert event.entity_id == "test-entity-123"
    assert event.payload["type"] == "competitor"
    assert event.actor == "system"


@pytest.mark.asyncio
async def test_event_created_on_entity_update(db_session: AsyncSession) -> None:
    """Appending an ENTITY_UPDATED event contains before/after payload."""
    store = EventStore()
    venture = await _create_venture(db_session)

    event = await store.append(
        db=db_session,
        venture_id=venture.id,
        event_type=KGEventType.ENTITY_UPDATED,
        entity_id="entity-456",
        payload={
            "before": {"data": {"name": "Old"}, "status": "suggested", "confidence": 0.5},
            "after": {"data": {"name": "New"}, "status": "confirmed", "confidence": 0.9},
        },
        actor="user:abc",
    )
    await db_session.commit()

    assert event.event_type == KGEventType.ENTITY_UPDATED
    assert "before" in event.payload
    assert "after" in event.payload
    assert event.payload["before"]["data"]["name"] == "Old"
    assert event.payload["after"]["data"]["name"] == "New"


@pytest.mark.asyncio
async def test_events_are_immutable() -> None:
    """EventStore has no update or delete methods — immutability by design."""
    store = EventStore()
    assert not hasattr(store, "update")
    assert not hasattr(store, "delete")
    assert not hasattr(store, "update_event")
    assert not hasattr(store, "delete_event")
    # The only write method is append
    assert hasattr(store, "append")
