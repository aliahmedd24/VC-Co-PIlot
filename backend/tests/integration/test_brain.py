"""Integration tests for Brain API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def workspace_with_venture(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
) -> dict:
    """Create a workspace with venture for testing brain endpoints."""
    response = await client.post(
        "/api/v1/workspaces/",
        headers=auth_headers,
        json={"name": "Brain Test Workspace", "venture_name": "Brain Test Venture"},
    )
    assert response.status_code == 201
    workspace = response.json()
    return workspace


@pytest.mark.asyncio
async def test_get_venture_profile(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test getting venture profile."""
    workspace_id = workspace_with_venture["id"]

    response = await client.get(
        f"/api/v1/brain/profile/{workspace_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert "venture" in data
    assert "entities" in data
    assert data["venture"]["name"] == "Brain Test Venture"


@pytest.mark.asyncio
async def test_create_entity(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test creating a KG entity."""
    workspace_id = workspace_with_venture["id"]

    response = await client.post(
        f"/api/v1/brain/entities?workspace_id={workspace_id}",
        headers=auth_headers,
        json={
            "type": "market",
            "data": {"name": "B2B SaaS", "tam": "$50B"},
            "confidence": 0.8,
        },
    )
    assert response.status_code == 201
    data = response.json()

    assert data["type"] == "market"
    assert data["data"]["name"] == "B2B SaaS"
    assert data["confidence"] == 0.8
    assert data["status"] == "needs_review"  # 0.8 confidence -> needs_review


@pytest.mark.asyncio
async def test_create_entity_confirmed_status(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test that high confidence entities get CONFIRMED status."""
    workspace_id = workspace_with_venture["id"]

    response = await client.post(
        f"/api/v1/brain/entities?workspace_id={workspace_id}",
        headers=auth_headers,
        json={
            "type": "competitor",
            "data": {"name": "Competitor Inc"},
            "confidence": 0.9,
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_get_entity(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test getting a specific entity."""
    workspace_id = workspace_with_venture["id"]

    # Create entity first
    create_response = await client.post(
        f"/api/v1/brain/entities?workspace_id={workspace_id}",
        headers=auth_headers,
        json={
            "type": "icp",
            "data": {"name": "Enterprise CTO"},
            "confidence": 0.7,
        },
    )
    entity_id = create_response.json()["id"]

    # Get it
    response = await client.get(
        f"/api/v1/brain/entities/{entity_id}?workspace_id={workspace_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Enterprise CTO"


@pytest.mark.asyncio
async def test_update_entity(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test updating a KG entity."""
    workspace_id = workspace_with_venture["id"]

    # Create entity
    create_response = await client.post(
        f"/api/v1/brain/entities?workspace_id={workspace_id}",
        headers=auth_headers,
        json={
            "type": "product",
            "data": {"name": "MVP"},
            "confidence": 0.5,
        },
    )
    entity_id = create_response.json()["id"]

    # Update it
    response = await client.patch(
        f"/api/v1/brain/entities/{entity_id}?workspace_id={workspace_id}",
        headers=auth_headers,
        json={
            "data": {"name": "Production App", "version": "2.0"},
            "confidence": 0.9,
            "status": "confirmed",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["data"]["name"] == "Production App"
    assert data["data"]["version"] == "2.0"
    assert data["confidence"] == 0.9
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_delete_entity(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test deleting a KG entity."""
    workspace_id = workspace_with_venture["id"]

    # Create entity
    create_response = await client.post(
        f"/api/v1/brain/entities?workspace_id={workspace_id}",
        headers=auth_headers,
        json={"type": "risk", "data": {"description": "Test risk"}},
    )
    entity_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/brain/entities/{entity_id}?workspace_id={workspace_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(
        f"/api/v1/brain/entities/{entity_id}?workspace_id={workspace_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_brain(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test searching the brain."""
    workspace_id = workspace_with_venture["id"]

    # Create some entities
    await client.post(
        f"/api/v1/brain/entities?workspace_id={workspace_id}",
        headers=auth_headers,
        json={"type": "market", "data": {"name": "Healthcare SaaS market"}},
    )
    await client.post(
        f"/api/v1/brain/entities?workspace_id={workspace_id}",
        headers=auth_headers,
        json={"type": "competitor", "data": {"name": "HealthTech Inc"}},
    )

    # Search
    response = await client.post(
        f"/api/v1/brain/search?workspace_id={workspace_id}",
        headers=auth_headers,
        json={"query": "healthcare"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "entities" in data
    assert "citations" in data


@pytest.mark.asyncio
async def test_propose_updates(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace_with_venture: dict,
) -> None:
    """Test proposing KG updates."""
    workspace_id = workspace_with_venture["id"]

    response = await client.post(
        f"/api/v1/brain/propose?workspace_id={workspace_id}",
        headers=auth_headers,
        json={
            "entities": [
                {"type": "metric", "data": {"name": "MRR", "value": "$50k"}, "confidence": 0.7},
                {"type": "metric", "data": {"name": "Churn", "value": "2%"}, "confidence": 0.6},
            ],
            "agent_id": "test-agent",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["created"]) == 2
    # All proposed entities should be SUGGESTED status initially (based on confidence)


@pytest.mark.asyncio
async def test_profile_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test getting profile for non-existent workspace."""
    response = await client.get(
        "/api/v1/brain/profile/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404
