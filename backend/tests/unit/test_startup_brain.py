import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.brain.startup_brain import StartupBrain
from app.models.kg_entity import KGEntityStatus, KGEntityType
from app.schemas.brain import ChunkResult


def _make_mock_entity(
    entity_type: KGEntityType = KGEntityType.COMPETITOR,
    name: str = "TestCo",
) -> MagicMock:
    entity = MagicMock()
    entity.id = uuid.uuid4()
    entity.type = entity_type
    entity.status = KGEntityStatus.CONFIRMED
    entity.data = {"name": name}
    entity.confidence = 0.9
    entity.evidence = []
    return entity


@pytest.mark.asyncio
async def test_retrieve_combines_rag_and_kg() -> None:
    """Retrieve returns both chunks and entities for a query."""
    mock_rag = AsyncMock()
    mock_kg = AsyncMock()

    chunk = ChunkResult(
        chunk_id=str(uuid.uuid4()),
        document_id=str(uuid.uuid4()),
        content="Sample chunk text",
        similarity=0.85,
        freshness_weight=0.99,
        final_score=0.84,
    )
    mock_rag.search.return_value = [chunk]

    mock_entity = _make_mock_entity()
    mock_kg.search_entities.return_value = [mock_entity]

    brain = StartupBrain(rag=mock_rag, kg=mock_kg)
    mock_db = AsyncMock()

    result = await brain.retrieve(
        db=mock_db,
        venture_id=uuid.uuid4(),
        query="competitors",
        query_embedding=[0.1] * 10,
    )

    assert len(result.chunks) == 1
    assert result.chunks[0].content == "Sample chunk text"
    assert len(result.entities) == 1
    assert result.entities[0].data["name"] == "TestCo"
    assert len(result.citations) == 1


@pytest.mark.asyncio
async def test_get_snapshot() -> None:
    """Get snapshot returns entities grouped for profile."""
    mock_rag = AsyncMock()
    mock_kg = AsyncMock()

    entities = [
        _make_mock_entity(KGEntityType.COMPETITOR, "Alpha"),
        _make_mock_entity(KGEntityType.MARKET, "FinTech"),
    ]
    mock_kg.get_entities_by_venture.return_value = entities

    brain = StartupBrain(rag=mock_rag, kg=mock_kg)
    mock_db = AsyncMock()

    result_entities, total = await brain.get_snapshot(
        db=mock_db,
        venture_id=uuid.uuid4(),
    )

    assert total == 2
    assert len(result_entities) == 2
