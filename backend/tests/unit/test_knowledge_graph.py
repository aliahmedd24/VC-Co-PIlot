import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.brain.events.event_store import EventStore
from app.core.brain.kg.knowledge_graph import KnowledgeGraph
from app.models.kg_entity import (
    KGEntityStatus,
    KGEntityType,
    KGRelation,
    KGRelationType,
)
from app.models.venture import Venture
from app.models.workspace import Workspace


async def _create_venture(db: AsyncSession) -> Venture:
    workspace = Workspace(name="Test WS", slug=f"test-ws-{uuid.uuid4().hex[:8]}")
    db.add(workspace)
    await db.flush()
    venture = Venture(workspace_id=workspace.id, name="Test Venture")
    db.add(venture)
    await db.flush()
    return venture


@pytest.mark.asyncio
async def test_create_entity(db_session: AsyncSession) -> None:
    """Create entity with confidence >= 0.85 auto-sets status to CONFIRMED."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    entity = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "Acme Corp", "description": "Direct competitor"},
        confidence=0.9,
        actor="test",
    )
    await db_session.commit()

    assert entity.id is not None
    assert entity.type == KGEntityType.COMPETITOR
    assert entity.status == KGEntityStatus.CONFIRMED
    assert entity.data["name"] == "Acme Corp"
    assert entity.confidence == 0.9


@pytest.mark.asyncio
async def test_update_entity(db_session: AsyncSession) -> None:
    """Update merges data dict correctly."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    entity = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.MARKET,
        data={"name": "FinTech", "tam": "$10B"},
        confidence=0.7,
    )

    updated = await kg.update_entity(
        db=db_session,
        entity_id=entity.id,
        data={"sam": "$1B"},
    )
    await db_session.commit()

    assert updated.data["name"] == "FinTech"
    assert updated.data["tam"] == "$10B"
    assert updated.data["sam"] == "$1B"


@pytest.mark.asyncio
async def test_search_entities_by_keyword(db_session: AsyncSession) -> None:
    """Keyword in entity data matches; unrelated entities excluded."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "Stripe"},
        confidence=0.8,
    )
    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "Plaid"},
        confidence=0.8,
    )
    await db_session.commit()

    results = await kg.search_entities(
        db=db_session,
        venture_id=venture.id,
        keyword="Stripe",
    )

    assert len(results) == 1
    assert results[0].data["name"] == "Stripe"


@pytest.mark.asyncio
async def test_search_entities_by_type_filter(db_session: AsyncSession) -> None:
    """Only requested types returned."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "Rival Inc"},
        confidence=0.7,
    )
    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.MARKET,
        data={"name": "B2B SaaS"},
        confidence=0.7,
    )
    await db_session.commit()

    results = await kg.search_entities(
        db=db_session,
        venture_id=venture.id,
        entity_types=[KGEntityType.MARKET],
    )

    assert len(results) == 1
    assert results[0].type == KGEntityType.MARKET


@pytest.mark.asyncio
async def test_conflict_detection(db_session: AsyncSession) -> None:
    """Two entities of same type with overlapping name trigger NEEDS_REVIEW + CONFLICTS_WITH."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    first = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "BigCorp"},
        confidence=0.9,
    )
    assert first.status == KGEntityStatus.CONFIRMED

    second = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "BigCorp", "extra": "different source"},
        confidence=0.9,
    )
    await db_session.commit()

    # Second entity should be NEEDS_REVIEW due to conflict
    assert second.status == KGEntityStatus.NEEDS_REVIEW

    # CONFLICTS_WITH relation should exist
    relations = await db_session.execute(
        select(KGRelation).where(
            KGRelation.from_entity_id == second.id,
            KGRelation.type == KGRelationType.CONFLICTS_WITH,
        )
    )
    relation = relations.scalar_one_or_none()
    assert relation is not None
    assert relation.to_entity_id == first.id


@pytest.mark.asyncio
async def test_max_entities_per_type(db_session: AsyncSession) -> None:
    """51st entity of same type raises ValueError."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    # Create 50 entities
    for i in range(50):
        await kg.create_entity(
            db=db_session,
            venture_id=venture.id,
            entity_type=KGEntityType.RISK,
            data={"name": f"Risk {i}"},
            confidence=0.3,
        )
    await db_session.commit()

    # 51st should fail
    with pytest.raises(ValueError, match="Max 50"):
        await kg.create_entity(
            db=db_session,
            venture_id=venture.id,
            entity_type=KGEntityType.RISK,
            data={"name": "Risk 50"},
            confidence=0.3,
        )
