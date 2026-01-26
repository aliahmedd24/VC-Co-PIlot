"""Integration tests for artifacts API."""

import pytest
from httpx import AsyncClient

from app.models.artifact import ArtifactType, ArtifactStatus


@pytest.mark.asyncio
async def test_artifacts_api_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
):
    # 1. Create Workspace
    resp = await client.post(
        "/api/v1/workspaces/",
        json={"name": "Artifact Test Workspace", "slug": "artifact-test-ws"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    workspace = resp.json()
    ws_id = workspace["id"]

    # 2. Create Artifact
    resp = await client.post(
        "/api/v1/artifacts",
        json={
            "workspace_id": ws_id,
            "type": ArtifactType.LEAN_CANVAS.value,
            "title": "My Lean Canvas",
            "owner_agent": "venture-architect",
            "content": {"problem": "Too complicated"},
            "assumptions": [{"id": 1, "text": "Assume X"}],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    artifact = resp.json()
    artifact_id = artifact["id"]
    
    assert artifact["title"] == "My Lean Canvas"
    assert artifact["status"] == ArtifactStatus.DRAFT.value
    assert artifact["current_version"] == 1
    assert artifact["content"]["problem"] == "Too complicated"

    # 3. Get Artifact List
    resp = await client.get(
        f"/api/v1/artifacts?workspace_id={ws_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == artifact_id

    # 4. Update Artifact (New Version)
    resp = await client.patch(
        f"/api/v1/artifacts/{artifact_id}",
        json={
            "content": {"problem": "Simplified"},
            "status": ArtifactStatus.IN_PROGRESS.value,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    updated = resp.json()
    
    assert updated["content"]["problem"] == "Simplified"
    assert updated["current_version"] == 2
    assert updated["status"] == ArtifactStatus.IN_PROGRESS.value

    # 5. Check Versions
    resp = await client.get(
        f"/api/v1/artifacts/{artifact_id}/versions",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2
    assert versions[0]["version"] == 2
    assert versions[1]["version"] == 1
    
    # Check diff
    assert versions[0]["diff"] is not None
    assert "modified" in versions[0]["diff"]

    # 6. Restore Version 1
    resp = await client.post(
        f"/api/v1/artifacts/{artifact_id}/restore/1",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    restored = resp.json()
    
    assert restored["current_version"] == 3
    assert restored["content"]["problem"] == "Too complicated"

    # 7. Test Export (Async)
    resp = await client.post(
        f"/api/v1/artifacts/{artifact_id}/export",
        json={"format": "markdown"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    export_resp = resp.json()
    assert export_resp["status"] == "pending"
    assert export_resp["task_id"] is not None

    # 8. Delete Artifact
    resp = await client.delete(
        f"/api/v1/artifacts/{artifact_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    
    # Verify initialized as archived
    resp = await client.get(
        f"/api/v1/artifacts/{artifact_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == ArtifactStatus.ARCHIVED.value
