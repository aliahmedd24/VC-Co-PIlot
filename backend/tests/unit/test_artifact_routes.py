import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(
    client: AsyncClient, email: str = "artifact@example.com"
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepass123", "name": "Test"},
    )
    token: str = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_workspace(
    client: AsyncClient, headers: dict[str, str], name: str = "Artifact Test WS"
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": name},
        headers=headers,
    )
    result: dict[str, Any] = response.json()
    return result


async def _create_artifact(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    title: str = "Test Canvas",
    artifact_type: str = "lean_canvas",
    content: dict[str, Any] | None = None,
) -> Any:
    body: dict[str, Any] = {
        "workspace_id": workspace_id,
        "type": artifact_type,
        "title": title,
    }
    if content is not None:
        body["content"] = content
    response = await client.post(
        "/api/v1/artifacts",
        json=body,
        headers=headers,
    )
    return response


@pytest.mark.asyncio
async def test_create_artifact_api(client: AsyncClient) -> None:
    """POST /artifacts creates an artifact and returns it."""
    headers = await _register_and_get_headers(client, "art1@test.com")
    ws = await _create_workspace(client, headers)

    response = await _create_artifact(
        client,
        headers,
        ws["id"],
        title="My Lean Canvas",
        content={"problem": ["High CAC"]},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Lean Canvas"
    assert data["type"] == "lean_canvas"
    assert data["status"] == "draft"
    assert data["current_version"] == 1
    assert data["content"] == {"problem": ["High CAC"]}


@pytest.mark.asyncio
async def test_list_artifacts(client: AsyncClient) -> None:
    """GET /artifacts returns artifacts for workspace, excludes archived."""
    headers = await _register_and_get_headers(client, "art2@test.com")
    ws = await _create_workspace(client, headers)

    # Create two artifacts
    await _create_artifact(client, headers, ws["id"], "Canvas 1")
    await _create_artifact(client, headers, ws["id"], "Canvas 2")

    response = await client.get(
        f"/api/v1/artifacts?workspace_id={ws['id']}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["artifacts"]) == 2


@pytest.mark.asyncio
async def test_get_artifact(client: AsyncClient) -> None:
    """GET /artifacts/{id} returns full artifact with content."""
    headers = await _register_and_get_headers(client, "art3@test.com")
    ws = await _create_workspace(client, headers)

    create_resp = await _create_artifact(
        client, headers, ws["id"], content={"problem": ["Test"]}
    )
    artifact_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/artifacts/{artifact_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == artifact_id
    assert data["content"] == {"problem": ["Test"]}


@pytest.mark.asyncio
async def test_update_artifact_status(client: AsyncClient) -> None:
    """PATCH /artifacts/{id} changes status."""
    headers = await _register_and_get_headers(client, "art4@test.com")
    ws = await _create_workspace(client, headers)

    create_resp = await _create_artifact(client, headers, ws["id"])
    artifact_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/artifacts/{artifact_id}",
        json={"status": "in_progress", "expected_version": 1},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_list_versions(client: AsyncClient) -> None:
    """GET /artifacts/{id}/versions returns version history."""
    headers = await _register_and_get_headers(client, "art5@test.com")
    ws = await _create_workspace(client, headers)

    create_resp = await _create_artifact(
        client, headers, ws["id"], content={"problem": ["v1"]}
    )
    artifact_id = create_resp.json()["id"]

    # Update to create version 2
    await client.patch(
        f"/api/v1/artifacts/{artifact_id}",
        json={"content": {"problem": ["v1", "v2"]}, "expected_version": 1},
        headers=headers,
    )

    response = await client.get(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["versions"]) == 2
    assert data["versions"][0]["version"] == 1
    assert data["versions"][1]["version"] == 2


@pytest.mark.asyncio
async def test_get_specific_version(client: AsyncClient) -> None:
    """GET /artifacts/{id}/versions/{version} returns specific version content."""
    headers = await _register_and_get_headers(client, "art6@test.com")
    ws = await _create_workspace(client, headers)

    create_resp = await _create_artifact(
        client, headers, ws["id"], content={"problem": ["v1"]}
    )
    artifact_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/artifacts/{artifact_id}/versions/1",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["content"] == {"problem": ["v1"]}
    assert data["diff"] is None  # Initial version has no diff


@pytest.mark.asyncio
async def test_export_markdown(client: AsyncClient) -> None:
    """POST /artifacts/{id}/export with markdown format returns rendered text."""
    headers = await _register_and_get_headers(client, "art7@test.com")
    ws = await _create_workspace(client, headers)

    create_resp = await _create_artifact(
        client,
        headers,
        ws["id"],
        content={
            "problem": ["High CAC"],
            "solution": ["AI outreach"],
            "key_metrics": ["MRR"],
            "unique_value_prop": "10x faster",
            "unfair_advantage": "",
            "channels": [],
            "customer_segments": ["B2B SaaS"],
            "cost_structure": [],
            "revenue_streams": [],
        },
    )
    artifact_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/artifacts/{artifact_id}/export",
        json={"format": "markdown"},
        headers=headers,
    )
    assert response.status_code == 200
    assert "High CAC" in response.text
    assert "10x faster" in response.text


@pytest.mark.asyncio
async def test_export_pdf_enqueues_task(client: AsyncClient) -> None:
    """POST /artifacts/{id}/export with pdf format returns a task_id."""
    headers = await _register_and_get_headers(client, "art8@test.com")
    ws = await _create_workspace(client, headers)

    create_resp = await _create_artifact(client, headers, ws["id"])
    artifact_id = create_resp.json()["id"]

    mock_task = MagicMock()
    mock_task.id = "celery-task-123"

    with patch(
        "app.workers.export_tasks.export_artifact_pdf"
    ) as mock_export:
        mock_export.delay.return_value = mock_task
        response = await client.post(
            f"/api/v1/artifacts/{artifact_id}/export",
            json={"format": "pdf"},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "celery-task-123"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_artifact_routes_require_auth(client: AsyncClient) -> None:
    """Artifact endpoints return 401 without token."""
    response = await client.get(
        f"/api/v1/artifacts?workspace_id={uuid.uuid4()}"
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_artifact_workspace_access(client: AsyncClient) -> None:
    """Cannot access artifacts in workspaces you don't belong to."""
    headers = await _register_and_get_headers(client, "art10@test.com")
    ws = await _create_workspace(client, headers)

    create_resp = await _create_artifact(client, headers, ws["id"])
    artifact_id = create_resp.json()["id"]

    # Register a different user
    other_headers = await _register_and_get_headers(client, "other@test.com")

    response = await client.get(
        f"/api/v1/artifacts/{artifact_id}",
        headers=other_headers,
    )
    assert response.status_code == 404
