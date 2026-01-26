"""Unit tests for artifact system."""

import pytest
from uuid import uuid4
from datetime import datetime

from app.core.artifacts.diff_engine import DiffEngine
from app.core.artifacts.manager import ArtifactManager
from app.models.artifact import ArtifactType, ArtifactStatus


class TestDiffEngine:
    def test_compute_diff_simple(self):
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3, "c": 4}

        diff = DiffEngine.compute_diff(old, new)

        assert diff["unchanged_count"] == 1
        assert diff["added"] == {"c": 4}
        assert diff["removed"] == {}
        assert diff["modified"] == {"b": {"old": 2, "new": 3}}

    def test_compute_diff_nested(self):
        old = {"nested": {"x": 10, "y": 20}}
        new = {"nested": {"x": 10, "y": 25}}

        diff = DiffEngine.compute_diff(old, new)

        assert diff["modified"]["nested"]["modified"] == {"y": {"old": 20, "new": 25}}
        assert diff["modified"]["nested"]["unchanged_count"] == 1

    def test_apply_diff(self):
        base = {"a": 1, "b": 2}
        diff = {
            "added": {"c": 3},
            "removed": {"a": 1},
            "modified": {"b": {"old": 2, "new": 5}},
        }

        result = DiffEngine.apply_diff(base, diff)

        assert result == {"b": 5, "c": 3}

    def test_apply_diff_reverse(self):
        current = {"b": 5, "c": 3}
        diff = {
            "added": {"c": 3},
            "removed": {"a": 1},
            "modified": {"b": {"old": 2, "new": 5}},
        }

        result = DiffEngine.apply_diff(current, diff, reverse=True)

        assert result == {"a": 1, "b": 2}

    def test_summarize_changes(self):
        diff = {
            "added": {"c": 3, "d": 4},
            "removed": {"a": 1},
            "modified": {"b": {"old": 2, "new": 5}},
        }

        summary = DiffEngine.summarize_changes(diff)

        assert "Added: c, d" in summary
        assert "Removed: a" in summary
        assert "Modified: b" in summary


@pytest.mark.asyncio
class TestArtifactManager:
    async def test_create_artifact(self, db_session):
        manager = ArtifactManager(db_session)
        workspace_id = str(uuid4())
        
        artifact = await manager.create_artifact(
            workspace_id=workspace_id,
            artifact_type=ArtifactType.LEAN_CANVAS,
            title="Test Canvas",
            owner_agent="venture-architect",
            content={"problem": "test problem"},
        )

        assert artifact.title == "Test Canvas"
        assert artifact.status == ArtifactStatus.DRAFT
        assert artifact.content == {"problem": "test problem"}
        assert len(artifact.versions) == 1
        assert artifact.versions[0].version == 1

    async def test_update_artifact_content_creates_version(self, db_session):
        manager = ArtifactManager(db_session)
        workspace_id = str(uuid4())
        
        artifact = await manager.create_artifact(
            workspace_id=workspace_id,
            artifact_type=ArtifactType.LEAN_CANVAS,
            title="V1",
            owner_agent="agent",
            content={"v": 1},
        )
        
        # Update content
        updated = await manager.update_artifact(
            artifact_id=artifact.id,
            content={"v": 2},
            updated_by="user",
        )
        
        await db_session.refresh(updated, attribute_names=["versions"])
        
        assert updated.content == {"v": 2}
        assert len(updated.versions) == 2
        
        v2 = next(v for v in updated.versions if v.version == 2)
        assert v2.diff is not None
        assert v2.content == {"v": 2}

    async def test_restore_version(self, db_session):
        manager = ArtifactManager(db_session)
        workspace_id = str(uuid4())
        
        # Create V1
        artifact = await manager.create_artifact(
            workspace_id=workspace_id,
            artifact_type=ArtifactType.LEAN_CANVAS,
            title="Doc",
            owner_agent="agent",
            content={"step": 1},
        )
        
        # Update to V2
        await manager.update_artifact(
            artifact_id=artifact.id,
            content={"step": 2},
        )
        
        # Restore V1
        restored = await manager.restore_version(
            artifact_id=artifact.id,
            version_number=1,
        )
        
        await db_session.refresh(restored, attribute_names=["versions"])
        
        # Should now be V3 with content of V1
        assert restored.content == {"step": 1}
        assert len(restored.versions) == 3
        
        v3 = next(v for v in restored.versions if v.version == 3)
        assert v3.content == {"step": 1}

    async def test_delete_artifact(self, db_session):
        manager = ArtifactManager(db_session)
        workspace_id = str(uuid4())
        
        artifact = await manager.create_artifact(
            workspace_id=workspace_id,
            artifact_type=ArtifactType.LEAN_CANVAS,
            title="Delete Me",
            owner_agent="agent",
        )
        
        # Soft delete
        await manager.delete_artifact(artifact.id, hard_delete=False)
        await db_session.refresh(artifact)
        assert artifact.status == ArtifactStatus.ARCHIVED
        
        # Hard delete
        await manager.delete_artifact(artifact.id, hard_delete=True)
        found = await manager.get_artifact(artifact.id)
        assert found is None
