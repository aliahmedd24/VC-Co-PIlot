"""Tests for workspace endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test creating a workspace."""
    response = await client.post(
        "/api/v1/workspaces/",
        headers=auth_headers,
        json={"name": "My Startup", "venture_name": "My Venture"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Startup"
    assert "slug" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_list_workspaces(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test listing user's workspaces."""
    # Create a workspace first
    await client.post(
        "/api/v1/workspaces/",
        headers=auth_headers,
        json={"name": "Test Workspace"},
    )

    response = await client.get("/api/v1/workspaces/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Workspace"


@pytest.mark.asyncio
async def test_get_workspace_detail(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting workspace details."""
    # Create a workspace
    create_response = await client.post(
        "/api/v1/workspaces/",
        headers=auth_headers,
        json={"name": "Detail Test", "venture_name": "Test Venture"},
    )
    workspace_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Detail Test"
    assert data["venture"]["name"] == "Test Venture"


@pytest.mark.asyncio
async def test_delete_workspace(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test deleting a workspace."""
    # Create a workspace
    create_response = await client.post(
        "/api/v1/workspaces/",
        headers=auth_headers,
        json={"name": "To Delete"},
    )
    workspace_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
