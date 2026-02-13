import json
from unittest.mock import MagicMock, patch

import pytest

from app.core.brain.kg.entity_extractor import EntityExtractor


@pytest.mark.asyncio
async def test_extract_entities_from_chunks() -> None:
    """Mock Claude response with valid JSON produces correct entities."""
    extractor = EntityExtractor()

    mock_entities = [
        {
            "type": "competitor",
            "data": {"name": "Acme Corp", "description": "Direct competitor"},
            "confidence": 0.85,
        },
        {
            "type": "metric",
            "data": {"name": "Monthly Revenue", "value": "$50k"},
            "confidence": 0.9,
        },
    ]

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(mock_entities))]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch.object(extractor, "_get_client", return_value=mock_client):
        result = extractor.extract_from_text("Sample document text about competitors and metrics")

    assert len(result) == 2
    assert result[0]["type"] == "competitor"
    assert result[0]["data"]["name"] == "Acme Corp"
    assert result[1]["type"] == "metric"
    assert result[1]["confidence"] == 0.9


@pytest.mark.asyncio
async def test_extraction_invalid_json() -> None:
    """Invalid JSON from Claude returns empty list, no crash."""
    extractor = EntityExtractor()

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is not JSON at all {broken")]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch.object(extractor, "_get_client", return_value=mock_client):
        result = extractor.extract_from_text("Some text to extract from")

    assert result == []
