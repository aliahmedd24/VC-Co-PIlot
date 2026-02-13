import json
import uuid
from typing import Any

import structlog
from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.artifacts.diff_engine import compute_diff
from app.models.artifact import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    ArtifactVersion,
)

logger = structlog.get_logger()

MAX_VERSIONS = 100
MAX_CONTENT_SIZE_BYTES = 500 * 1024  # 500KB


class ArtifactManager:
    """Business logic for creating, updating, and querying artifacts."""

    async def create(
        self,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        artifact_type: ArtifactType,
        title: str,
        content: dict[str, Any],
        owner_agent: str,
        created_by_id: uuid.UUID | None = None,
    ) -> Artifact:
        """Create a new artifact with an initial version (v1)."""
        self._validate_content_size(content)

        artifact = Artifact(
            workspace_id=workspace_id,
            type=artifact_type,
            title=title,
            status=ArtifactStatus.DRAFT,
            owner_agent=owner_agent,
            content=content,
            created_by_id=created_by_id,
            current_version=1,
        )
        db.add(artifact)
        await db.flush()

        created_by = f"user:{created_by_id}" if created_by_id else f"agent:{owner_agent}"
        initial_version = ArtifactVersion(
            artifact_id=artifact.id,
            version=1,
            content=content,
            diff=None,
            created_by=created_by,
        )
        db.add(initial_version)
        await db.flush()

        logger.info(
            "artifact_created",
            artifact_id=str(artifact.id),
            type=artifact_type.value,
            title=title,
        )
        return artifact

    async def update(
        self,
        db: AsyncSession,
        artifact_id: uuid.UUID,
        content: dict[str, Any],
        expected_version: int,
        created_by: str,
    ) -> Artifact:
        """Update artifact content with optimistic locking and diff tracking."""
        artifact = await self.get(db, artifact_id)
        if artifact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found",
            )

        if artifact.current_version != expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Version conflict: expected {expected_version}, "
                f"current is {artifact.current_version}",
            )

        self._validate_content_size(content)

        diff = compute_diff(artifact.content, content)
        new_version = artifact.current_version + 1

        version_row = ArtifactVersion(
            artifact_id=artifact_id,
            version=new_version,
            content=content,
            diff=diff if diff else None,
            created_by=created_by,
        )
        db.add(version_row)

        artifact.content = content
        artifact.current_version = new_version
        await db.flush()

        await self._prune_versions(db, artifact_id)

        logger.info(
            "artifact_updated",
            artifact_id=str(artifact_id),
            version=new_version,
        )
        return artifact

    async def get(
        self,
        db: AsyncSession,
        artifact_id: uuid.UUID,
    ) -> Artifact | None:
        """Get a single artifact by ID."""
        result = await db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        return result.scalar_one_or_none()

    async def list_artifacts(
        self,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        include_archived: bool = False,
    ) -> list[Artifact]:
        """List artifacts for a workspace, excluding archived by default."""
        query = select(Artifact).where(Artifact.workspace_id == workspace_id)
        if not include_archived:
            query = query.where(Artifact.status != ArtifactStatus.ARCHIVED)
        query = query.order_by(Artifact.updated_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_versions(
        self,
        db: AsyncSession,
        artifact_id: uuid.UUID,
    ) -> list[ArtifactVersion]:
        """Get all versions for an artifact, ordered by version number."""
        result = await db.execute(
            select(ArtifactVersion)
            .where(ArtifactVersion.artifact_id == artifact_id)
            .order_by(ArtifactVersion.version)
        )
        return list(result.scalars().all())

    async def get_version(
        self,
        db: AsyncSession,
        artifact_id: uuid.UUID,
        version: int,
    ) -> ArtifactVersion | None:
        """Get a specific version of an artifact."""
        result = await db.execute(
            select(ArtifactVersion).where(
                ArtifactVersion.artifact_id == artifact_id,
                ArtifactVersion.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        db: AsyncSession,
        artifact_id: uuid.UUID,
        new_status: ArtifactStatus,
    ) -> Artifact:
        """Update the status of an artifact."""
        artifact = await self.get(db, artifact_id)
        if artifact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found",
            )
        artifact.status = new_status
        await db.flush()
        return artifact

    async def _prune_versions(
        self,
        db: AsyncSession,
        artifact_id: uuid.UUID,
    ) -> None:
        """Enforce max 100 versions per artifact. Keep v1 always, delete oldest."""
        count_result = await db.execute(
            select(func.count())
            .select_from(ArtifactVersion)
            .where(ArtifactVersion.artifact_id == artifact_id)
        )
        total = count_result.scalar() or 0

        if total <= MAX_VERSIONS:
            return

        excess = total - MAX_VERSIONS
        # Find the oldest non-initial versions to delete
        oldest_result = await db.execute(
            select(ArtifactVersion.id)
            .where(
                ArtifactVersion.artifact_id == artifact_id,
                ArtifactVersion.version > 1,
            )
            .order_by(ArtifactVersion.version.asc())
            .limit(excess)
        )
        ids_to_delete = [row[0] for row in oldest_result.all()]

        if ids_to_delete:
            await db.execute(
                delete(ArtifactVersion).where(
                    ArtifactVersion.id.in_(ids_to_delete)
                )
            )
            await db.flush()

    @staticmethod
    def _validate_content_size(content: dict[str, Any]) -> None:
        """Raise 413 if content exceeds 500KB when serialized."""
        size = len(json.dumps(content).encode("utf-8"))
        if size > MAX_CONTENT_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Artifact content exceeds {MAX_CONTENT_SIZE_BYTES} bytes limit",
            )


artifact_manager = ArtifactManager()
