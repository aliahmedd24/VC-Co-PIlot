import pytest
from httpx import AsyncClient


async def _register_and_get_headers(
    client: AsyncClient, email: str = "ws@example.com"
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepass123", "name": "Test"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient) -> None:
    headers = await _register_and_get_headers(client, "create_ws@test.com")

    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "My Startup"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Startup"
    assert data["role"] == "owner"
    assert data["venture"] is not None
    assert data["venture"]["name"] == "My Startup"
    assert "slug" in data


@pytest.mark.asyncio
async def test_list_workspaces(client: AsyncClient) -> None:
    headers = await _register_and_get_headers(client, "list_ws@test.com")

    await client.post("/api/v1/workspaces", json={"name": "WS 1"}, headers=headers)
    await client.post("/api/v1/workspaces", json={"name": "WS 2"}, headers=headers)

    response = await client.get("/api/v1/workspaces", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_update_venture(client: AsyncClient) -> None:
    headers = await _register_and_get_headers(client, "venture@test.com")

    ws_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Venture Test"},
        headers=headers,
    )
    workspace_id = ws_response.json()["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/venture",
        json={
            "name": "Updated Venture",
            "stage": "seed",
            "one_liner": "AI-powered analytics",
            "problem": "Data is hard",
            "solution": "We make it easy",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Venture"
    assert data["stage"] == "seed"
    assert data["one_liner"] == "AI-powered analytics"


@pytest.mark.asyncio
async def test_workspace_access_denied(client: AsyncClient) -> None:
    headers_a = await _register_and_get_headers(client, "user_a@test.com")
    headers_b = await _register_and_get_headers(client, "user_b@test.com")

    ws_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Private WS"},
        headers=headers_a,
    )
    workspace_id = ws_response.json()["id"]

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=headers_b,
    )
    assert response.status_code == 404
