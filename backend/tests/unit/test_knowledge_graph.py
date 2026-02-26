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


# --------------------------------------------------------------------------- #
# search_entities_advanced
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_search_entities_advanced_confidence_filter(
    db_session: AsyncSession,
) -> None:
    """search_entities_advanced filters by min_confidence."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "HighConf"},
        confidence=0.9,
    )
    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "LowConf"},
        confidence=0.3,
    )
    await db_session.commit()

    results = await kg.search_entities_advanced(
        db=db_session,
        venture_id=venture.id,
        min_confidence=0.8,
    )
    assert len(results) == 1
    assert results[0].data["name"] == "HighConf"


@pytest.mark.asyncio
async def test_search_entities_advanced_status_filter(
    db_session: AsyncSession,
) -> None:
    """search_entities_advanced filters by status."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.MARKET,
        data={"name": "Confirmed Market"},
        confidence=0.9,
    )
    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.MARKET,
        data={"name": "Suggested Market"},
        confidence=0.4,
    )
    await db_session.commit()

    results = await kg.search_entities_advanced(
        db=db_session,
        venture_id=venture.id,
        status_filter=KGEntityStatus.CONFIRMED,
    )
    assert len(results) == 1
    assert results[0].data["name"] == "Confirmed Market"


@pytest.mark.asyncio
async def test_search_entities_advanced_combined_filters(
    db_session: AsyncSession,
) -> None:
    """search_entities_advanced combines type + confidence + keyword."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "Alpha Corp"},
        confidence=0.9,
    )
    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.COMPETITOR,
        data={"name": "Beta Corp"},
        confidence=0.3,
    )
    await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.MARKET,
        data={"name": "Alpha Market"},
        confidence=0.9,
    )
    await db_session.commit()

    # Only high-confidence competitors with "Alpha"
    results = await kg.search_entities_advanced(
        db=db_session,
        venture_id=venture.id,
        keyword="Alpha",
        entity_types=[KGEntityType.COMPETITOR],
        min_confidence=0.8,
    )
    assert len(results) == 1
    assert results[0].data["name"] == "Alpha Corp"


# --------------------------------------------------------------------------- #
# get_relations
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_relations_outgoing(db_session: AsyncSession) -> None:
    """get_relations direction=outgoing returns only outgoing edges."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    e1 = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.PRODUCT,
        data={"name": "Product A"},
        confidence=0.8,
    )
    e2 = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.ICP,
        data={"name": "ICP One"},
        confidence=0.8,
    )
    # Product TARGETS ICP
    rel = KGRelation(
        from_entity_id=e1.id,
        to_entity_id=e2.id,
        type=KGRelationType.TARGETS,
    )
    db_session.add(rel)
    await db_session.flush()
    await db_session.commit()

    # Outgoing from product
    outgoing = await kg.get_relations(
        db=db_session,
        entity_ids=[e1.id],
        direction="outgoing",
    )
    assert len(outgoing) == 1
    assert outgoing[0].to_entity_id == e2.id

    # Incoming to product should be empty
    incoming = await kg.get_relations(
        db=db_session,
        entity_ids=[e1.id],
        direction="incoming",
    )
    assert len(incoming) == 0


@pytest.mark.asyncio
async def test_get_relations_with_type_filter(db_session: AsyncSession) -> None:
    """get_relations filters by relation_type."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    e1 = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.PRODUCT,
        data={"name": "Widget"},
        confidence=0.8,
    )
    e2 = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.ICP,
        data={"name": "SMB"},
        confidence=0.8,
    )
    e3 = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.PRODUCT,
        data={"name": "Dependency"},
        confidence=0.8,
    )

    db_session.add(KGRelation(
        from_entity_id=e1.id, to_entity_id=e2.id,
        type=KGRelationType.TARGETS,
    ))
    db_session.add(KGRelation(
        from_entity_id=e1.id, to_entity_id=e3.id,
        type=KGRelationType.DEPENDS_ON,
    ))
    await db_session.flush()
    await db_session.commit()

    # Only TARGETS
    targets = await kg.get_relations(
        db=db_session,
        entity_ids=[e1.id],
        relation_type=KGRelationType.TARGETS,
    )
    assert len(targets) == 1
    assert targets[0].type == KGRelationType.TARGETS


# --------------------------------------------------------------------------- #
# traverse
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_traverse_returns_connected_entities(db_session: AsyncSession) -> None:
    """traverse follows one hop and returns full entity data."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    product = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.PRODUCT,
        data={"name": "SaaS Platform"},
        confidence=0.9,
    )
    icp = await kg.create_entity(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.ICP,
        data={"name": "Enterprise"},
        confidence=0.85,
    )
    db_session.add(KGRelation(
        from_entity_id=product.id,
        to_entity_id=icp.id,
        type=KGRelationType.TARGETS,
    ))
    await db_session.flush()
    await db_session.commit()

    result = await kg.traverse(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.PRODUCT,
        relation_type=KGRelationType.TARGETS,
        direction="outgoing",
    )
    assert result["start_entities"] == 1
    assert result["relation_count"] == 1
    assert len(result["relations"]) == 1
    rel_data = result["relations"][0]
    assert rel_data["from"]["data"]["name"] == "SaaS Platform"
    assert rel_data["to"]["data"]["name"] == "Enterprise"
    assert rel_data["type"] == "targets"


@pytest.mark.asyncio
async def test_traverse_no_matching_entities(db_session: AsyncSession) -> None:
    """traverse returns empty result when no entities match."""
    kg = KnowledgeGraph(EventStore())
    venture = await _create_venture(db_session)

    result = await kg.traverse(
        db=db_session,
        venture_id=venture.id,
        entity_type=KGEntityType.RISK,
        entity_name="nonexistent",
    )
    assert result["start_entities"] == 0
    assert result["relations"] == []
    assert "message" in result
