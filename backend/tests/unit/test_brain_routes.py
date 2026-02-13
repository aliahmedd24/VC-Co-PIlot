import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(
    client: AsyncClient, email: str = "brain@example.com"
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepass123", "name": "Test"},
    )
    token: str = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_workspace(
    client: AsyncClient, headers: dict[str, str], name: str = "Brain Test WS"
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": name},
        headers=headers,
    )
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.asyncio
async def test_create_entity_api(client: AsyncClient) -> None:
    """POST /brain/entities creates entity and returns 201."""
    headers = await _register_and_get_headers(client, "create_ent@test.com")
    ws = await _create_workspace(client, headers)
    venture_id = ws["venture"]["id"]

    response = await client.post(
        "/api/v1/brain/entities",
        json={
            "venture_id": venture_id,
            "type": "competitor",
            "data": {"name": "Test Competitor"},
            "confidence": 0.85,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "competitor"
    assert data["data"]["name"] == "Test Competitor"
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_update_entity_api(client: AsyncClient) -> None:
    """PATCH /brain/entities/{id} returns updated entity."""
    headers = await _register_and_get_headers(client, "update_ent@test.com")
    ws = await _create_workspace(client, headers)
    venture_id = ws["venture"]["id"]

    # Create entity first
    create_resp = await client.post(
        "/api/v1/brain/entities",
        json={
            "venture_id": venture_id,
            "type": "market",
            "data": {"name": "FinTech"},
            "confidence": 0.7,
        },
        headers=headers,
    )
    entity_id = create_resp.json()["id"]

    # Update it
    response = await client.patch(
        f"/api/v1/brain/entities/{entity_id}",
        json={"data": {"tam": "$10B"}, "confidence": 0.9},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "FinTech"
    assert data["data"]["tam"] == "$10B"
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_delete_entity_api(client: AsyncClient) -> None:
    """DELETE /brain/entities/{id} returns 204."""
    headers = await _register_and_get_headers(client, "delete_ent@test.com")
    ws = await _create_workspace(client, headers)
    venture_id = ws["venture"]["id"]

    create_resp = await client.post(
        "/api/v1/brain/entities",
        json={
            "venture_id": venture_id,
            "type": "risk",
            "data": {"name": "Market Risk"},
            "confidence": 0.5,
        },
        headers=headers,
    )
    entity_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/brain/entities/{entity_id}",
        headers=headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_venture_profile(client: AsyncClient) -> None:
    """GET /brain/profile/{workspace_id} returns full profile."""
    headers = await _register_and_get_headers(client, "profile@test.com")
    ws = await _create_workspace(client, headers)
    workspace_id = ws["id"]
    venture_id = ws["venture"]["id"]

    # Create an entity first
    await client.post(
        "/api/v1/brain/entities",
        json={
            "venture_id": venture_id,
            "type": "competitor",
            "data": {"name": "ProfileCo"},
            "confidence": 0.8,
        },
        headers=headers,
    )

    response = await client.get(
        f"/api/v1/brain/profile/{workspace_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "venture" in data
    assert "entities_by_type" in data
    assert data["total_entities"] >= 1
    assert "total_documents" in data


@pytest.mark.asyncio
async def test_brain_search(client: AsyncClient) -> None:
    """POST /brain/search returns BrainSearchResponse."""
    headers = await _register_and_get_headers(client, "search@test.com")
    ws = await _create_workspace(client, headers)
    workspace_id = ws["id"]
    venture_id = ws["venture"]["id"]

    # Create an entity to find via KG search
    await client.post(
        "/api/v1/brain/entities",
        json={
            "venture_id": venture_id,
            "type": "competitor",
            "data": {"name": "SearchTarget"},
            "confidence": 0.8,
        },
        headers=headers,
    )

    # Mock embedding service (avoid real OpenAI call)
    with patch(
        "app.api.routes.brain.embedding_service"
    ) as mock_embed:
        mock_embed.embed_text.return_value = [0.1] * 1536

        # Also mock the RAG retriever to avoid pgvector SQL in SQLite
        with patch(
            "app.core.brain.startup_brain.startup_brain.rag"
        ) as mock_rag:
            mock_rag.search = AsyncMock(return_value=[])

            response = await client.post(
                "/api/v1/brain/search",
                json={
                    "workspace_id": workspace_id,
                    "query": "SearchTarget",
                    "max_chunks": 5,
                },
                headers=headers,
            )

    assert response.status_code == 200
    data = response.json()
    assert "chunks" in data
    assert "entities" in data
    assert "citations" in data


@pytest.mark.asyncio
async def test_brain_routes_require_auth(client: AsyncClient) -> None:
    """All brain routes return 403 without authentication token."""
    fake_ws_id = str(uuid.uuid4())
    fake_entity_id = str(uuid.uuid4())

    endpoints: list[tuple[str, str, dict[str, Any] | None]] = [
        ("POST", "/api/v1/brain/search", {
            "workspace_id": fake_ws_id, "query": "test",
        }),
        ("GET", f"/api/v1/brain/profile/{fake_ws_id}", None),
        ("POST", "/api/v1/brain/entities", {
            "venture_id": fake_ws_id, "type": "market", "data": {},
        }),
        ("PATCH", f"/api/v1/brain/entities/{fake_entity_id}", {
            "data": {},
        }),
        ("DELETE", f"/api/v1/brain/entities/{fake_entity_id}", None),
    ]

    for method, url, body in endpoints:
        if method == "GET":
            resp = await client.get(url)
        elif method == "POST":
            resp = await client.post(url, json=body)
        elif method == "PATCH":
            resp = await client.patch(url, json=body)
        elif method == "DELETE":
            resp = await client.delete(url)
        else:
            continue

        assert resp.status_code == 403, (
            f"{method} {url} returned {resp.status_code}, expected 403"
        )
