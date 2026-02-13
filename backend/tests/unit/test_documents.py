from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_create_workspace(
    client: AsyncClient, email: str = "doc@test.com"
) -> tuple[dict[str, str], str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws = await client.post(
        "/api/v1/workspaces",
        json={"name": "Doc Test WS"},
        headers=headers,
    )
    workspace_id = ws.json()["id"]
    return headers, workspace_id


@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient) -> None:
    headers, workspace_id = await _register_and_create_workspace(client, "upload@test.com")

    with patch("app.api.routes.documents.storage_service") as mock_storage:
        mock_storage.upload_file.return_value = "documents/test-key"

        # Patch celery task to prevent actual enqueuing
        with patch("app.workers.document_tasks.process_document") as mock_task:
            mock_task.delay = MagicMock()

            response = await client.post(
                "/api/v1/documents/upload",
                params={"workspace_id": workspace_id},
                files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
                headers=headers,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test.pdf"
    assert data["status"] == "pending"
    assert data["mime_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_upload_invalid_type(client: AsyncClient) -> None:
    headers, workspace_id = await _register_and_create_workspace(client, "invalid_type@test.com")

    response = await client.post(
        "/api/v1/documents/upload",
        params={"workspace_id": workspace_id},
        files={"file": ("test.exe", b"fake exe content", "application/x-msdownload")},
        headers=headers,
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_exceeds_size_limit(client: AsyncClient) -> None:
    headers, workspace_id = await _register_and_create_workspace(client, "big_file@test.com")

    # Create a file > 50MB
    large_content = b"x" * (50 * 1024 * 1024 + 1)

    response = await client.post(
        "/api/v1/documents/upload",
        params={"workspace_id": workspace_id},
        files={"file": ("large.pdf", large_content, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient) -> None:
    headers, workspace_id = await _register_and_create_workspace(client, "list_docs@test.com")

    with patch("app.api.routes.documents.storage_service") as mock_storage:
        mock_storage.upload_file.return_value = "documents/key1"

        with patch("app.workers.document_tasks.process_document") as mock_task:
            mock_task.delay = MagicMock()

            await client.post(
                "/api/v1/documents/upload",
                params={"workspace_id": workspace_id},
                files={"file": ("doc1.pdf", b"content1", "application/pdf")},
                headers=headers,
            )

    response = await client.get(
        "/api/v1/documents",
        params={"workspace_id": workspace_id},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["documents"]) >= 1
