import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.artifacts.manager import ArtifactManager
from app.models.artifact import ArtifactStatus, ArtifactType


@pytest.fixture
def manager() -> ArtifactManager:
    return ArtifactManager()


@pytest.fixture
def workspace_id() -> uuid.UUID:
    return uuid.uuid4()


async def test_create_artifact(
    db_session: AsyncSession, manager: ArtifactManager, workspace_id: uuid.UUID
) -> None:
    content = {"problem": ["High CAC"], "solution": ["AI outreach"]}
    artifact = await manager.create(
        db=db_session,
        workspace_id=workspace_id,
        artifact_type=ArtifactType.LEAN_CANVAS,
        title="Test Canvas",
        content=content,
        owner_agent="venture-architect",
    )

    assert artifact.title == "Test Canvas"
    assert artifact.type == ArtifactType.LEAN_CANVAS
    assert artifact.status == ArtifactStatus.DRAFT
    assert artifact.current_version == 1
    assert artifact.content == content

    # Verify initial version was created
    versions = await manager.get_versions(db_session, artifact.id)
    assert len(versions) == 1
    assert versions[0].version == 1
    assert versions[0].diff is None


async def test_update_artifact_content(
    db_session: AsyncSession, manager: ArtifactManager, workspace_id: uuid.UUID
) -> None:
    artifact = await manager.create(
        db=db_session,
        workspace_id=workspace_id,
        artifact_type=ArtifactType.LEAN_CANVAS,
        title="Canvas",
        content={"problem": ["v1"]},
        owner_agent="venture-architect",
    )

    updated = await manager.update(
        db=db_session,
        artifact_id=artifact.id,
        content={"problem": ["v1", "v2 addition"]},
        expected_version=1,
        created_by="user:test",
    )

    assert updated.current_version == 2
    assert updated.content == {"problem": ["v1", "v2 addition"]}

    versions = await manager.get_versions(db_session, artifact.id)
    assert len(versions) == 2
    assert versions[1].version == 2
    # Diff should capture the change
    assert versions[1].diff is not None


async def test_optimistic_locking(
    db_session: AsyncSession, manager: ArtifactManager, workspace_id: uuid.UUID
) -> None:
    artifact = await manager.create(
        db=db_session,
        workspace_id=workspace_id,
        artifact_type=ArtifactType.LEAN_CANVAS,
        title="Canvas",
        content={"problem": ["v1"]},
        owner_agent="venture-architect",
    )

    # Update once to move to v2
    await manager.update(
        db=db_session,
        artifact_id=artifact.id,
        content={"problem": ["v2"]},
        expected_version=1,
        created_by="user:test",
    )

    # Try to update with stale version (1) — should 409
    with pytest.raises(HTTPException) as exc_info:
        await manager.update(
            db=db_session,
            artifact_id=artifact.id,
            content={"problem": ["v3 conflict"]},
            expected_version=1,
            created_by="user:other",
        )
    assert exc_info.value.status_code == 409


async def test_max_versions_pruning(
    db_session: AsyncSession, manager: ArtifactManager, workspace_id: uuid.UUID
) -> None:
    artifact = await manager.create(
        db=db_session,
        workspace_id=workspace_id,
        artifact_type=ArtifactType.LEAN_CANVAS,
        title="Canvas",
        content={"v": 1},
        owner_agent="venture-architect",
    )

    # Create 100 more versions (total 101)
    for i in range(2, 102):
        await manager.update(
            db=db_session,
            artifact_id=artifact.id,
            content={"v": i},
            expected_version=i - 1,
            created_by="user:test",
        )

    # Should have pruned to 100
    versions = await manager.get_versions(db_session, artifact.id)
    assert len(versions) <= 100

    # Version 1 should always be preserved
    v1 = await manager.get_version(db_session, artifact.id, 1)
    assert v1 is not None
    assert v1.version == 1


async def test_content_size_limit(
    db_session: AsyncSession, manager: ArtifactManager, workspace_id: uuid.UUID
) -> None:
    # Create content larger than 500KB
    large_content = {"data": "x" * (500 * 1024 + 1)}

    with pytest.raises(HTTPException) as exc_info:
        await manager.create(
            db=db_session,
            workspace_id=workspace_id,
            artifact_type=ArtifactType.CUSTOM,
            title="Large",
            content=large_content,
            owner_agent="venture-architect",
        )
    assert exc_info.value.status_code == 413
