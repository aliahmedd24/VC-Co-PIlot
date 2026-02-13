import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.brain.rag.retriever import RAGRetriever


@pytest.mark.asyncio
async def test_freshness_weighting() -> None:
    """Newer chunks get higher freshness weight than older chunks."""
    retriever = RAGRetriever()

    recent = datetime.now(tz=UTC) - timedelta(days=1)
    old = datetime.now(tz=UTC) - timedelta(days=100)

    weight_recent = retriever.freshness_weight(recent)
    weight_old = retriever.freshness_weight(old)

    assert weight_recent > weight_old
    # 1-day-old should be close to 1.0
    assert weight_recent > 0.99
    # 100-day-old should be decayed significantly (half-life = 70 days)
    assert weight_old < 0.5


@pytest.mark.asyncio
async def test_search_returns_ranked_chunks() -> None:
    """Results are sorted by final_score descending."""
    retriever = RAGRetriever()

    now = datetime.now(tz=UTC)
    mock_rows = [
        MagicMock(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content="Old but very similar",
            created_at=now - timedelta(days=200),
            similarity=0.98,
        ),
        MagicMock(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content="Recent and somewhat similar",
            created_at=now - timedelta(days=1),
            similarity=0.80,
        ),
    ]

    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    chunks = await retriever.search(
        db=mock_db,
        venture_id=uuid.uuid4(),
        query_embedding=[0.1] * 1536,
        max_chunks=10,
    )

    assert len(chunks) == 2
    # Recent chunk should rank higher despite lower raw similarity
    assert chunks[0].content == "Recent and somewhat similar"
    assert chunks[0].final_score > chunks[1].final_score


@pytest.mark.asyncio
async def test_search_scoped_to_venture() -> None:
    """The SQL query includes venture_id binding."""
    retriever = RAGRetriever()
    venture_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    await retriever.search(
        db=mock_db,
        venture_id=venture_id,
        query_embedding=[0.1] * 10,
        max_chunks=5,
    )

    # Verify execute was called with venture_id in params
    call_args = mock_db.execute.call_args
    params = call_args[0][1]
    assert params["venture_id"] == str(venture_id)


@pytest.mark.asyncio
async def test_empty_query() -> None:
    """Empty result returns empty list, no error."""
    retriever = RAGRetriever()

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    chunks = await retriever.search(
        db=mock_db,
        venture_id=uuid.uuid4(),
        query_embedding=[0.1] * 10,
        max_chunks=10,
    )

    assert chunks == []
