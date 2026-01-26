"""Artifact manager for CRUD operations and versioning."""

from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.artifacts.diff_engine import DiffEngine
from app.models.artifact import Artifact, ArtifactStatus, ArtifactType, ArtifactVersion


class ArtifactManager:
    """Manager for artifact CRUD operations with automatic versioning."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.diff_engine = DiffEngine()

    async def create_artifact(
        self,
        workspace_id: str,
        artifact_type: ArtifactType,
        title: str,
        owner_agent: str,
        content: dict[str, Any] | None = None,
        assumptions: list[dict[str, Any]] | None = None,
        created_by_id: str | None = None,
    ) -> Artifact:
        """
        Create a new artifact with an initial version.

        Args:
            workspace_id: The workspace this artifact belongs to
            artifact_type: Type of artifact (lean_canvas, pitch_narrative, etc.)
            title: Human-readable title
            owner_agent: The agent that owns/created this artifact
            content: Initial JSONB content
            assumptions: Optional list of assumptions
            created_by_id: User ID who created this artifact

        Returns:
            The created Artifact instance
        """
        artifact_id = str(uuid4())
        content = content or {}

        artifact = Artifact(
            id=artifact_id,
            workspace_id=workspace_id,
            type=artifact_type,
            title=title,
            status=ArtifactStatus.DRAFT,
            owner_agent=owner_agent,
            content=content,
            assumptions=assumptions,
            created_by_id=created_by_id,
        )
        self.session.add(artifact)

        # Create initial version (version 1)
        version = ArtifactVersion(
            id=str(uuid4()),
            artifact_id=artifact_id,
            version=1,
            content=content,
            diff=None,  # No diff for first version
            created_by=owner_agent,
        )
        self.session.add(version)

        await self.session.commit()
        
        # Re-fetch to ensure relationships are loaded
        return await self.get_artifact(artifact_id, include_versions=True)

    async def get_artifact(
        self,
        artifact_id: str,
        include_versions: bool = False,
        version_limit: int = 10,
    ) -> Artifact | None:
        """
        Get an artifact by ID.

        Args:
            artifact_id: The artifact ID
            include_versions: Whether to load version history
            version_limit: Max number of versions to include

        Returns:
            The Artifact or None if not found
        """
        query = select(Artifact).where(Artifact.id == artifact_id)

        if include_versions:
            query = query.options(joinedload(Artifact.versions))

        result = await self.session.execute(query)
        artifact = result.unique().scalar_one_or_none()

        if artifact and include_versions and len(artifact.versions) > version_limit:
            artifact.versions = artifact.versions[:version_limit]

        return artifact

    async def list_artifacts(
        self,
        workspace_id: str,
        artifact_type: ArtifactType | None = None,
        status: ArtifactStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Artifact], int]:
        """
        List artifacts for a workspace with optional filters.

        Args:
            workspace_id: The workspace to list artifacts for
            artifact_type: Optional filter by type
            status: Optional filter by status
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (artifacts list, total count)
        """
        query = select(Artifact).where(Artifact.workspace_id == workspace_id)
        count_query = select(func.count(Artifact.id)).where(
            Artifact.workspace_id == workspace_id
        )

        if artifact_type:
            query = query.where(Artifact.type == artifact_type)
            count_query = count_query.where(Artifact.type == artifact_type)

        if status:
            query = query.where(Artifact.status == status)
            count_query = count_query.where(Artifact.status == status)

        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Artifact.updated_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        artifacts = list(result.scalars().all())

        return artifacts, total

    async def update_artifact(
        self,
        artifact_id: str,
        title: str | None = None,
        status: ArtifactStatus | None = None,
        content: dict[str, Any] | None = None,
        assumptions: list[dict[str, Any]] | None = None,
        updated_by: str | None = None,
    ) -> Artifact | None:
        """
        Update an artifact. If content changes, creates a new version.

        Args:
            artifact_id: The artifact to update
            title: New title (optional)
            status: New status (optional)
            content: New content (optional, triggers versioning)
            assumptions: New assumptions (optional)
            updated_by: Who is making this update

        Returns:
            The updated Artifact or None if not found
        """
        artifact = await self.get_artifact(artifact_id, include_versions=True)
        if not artifact:
            return None

        # Track if content changed (requires new version)
        content_changed = content is not None and content != artifact.content

        # Update basic fields
        if title is not None:
            artifact.title = title
        if status is not None:
            artifact.status = status
        if assumptions is not None:
            artifact.assumptions = assumptions

        # Handle content update with versioning
        if content_changed:
            # Compute diff from old to new content
            diff = self.diff_engine.compute_diff(artifact.content, content)

            # Get current max version
            max_version = 1
            if artifact.versions:
                max_version = max(v.version for v in artifact.versions)

            # Create new version
            new_version = ArtifactVersion(
                id=str(uuid4()),
                artifact_id=artifact_id,
                version=max_version + 1,
                content=content,
                diff=diff,
                created_by=updated_by,
            )
            self.session.add(new_version)

            # Update artifact content
            artifact.content = content

        await self.session.commit()
        
        # Re-fetch with versions to ensure everything is loaded and avoid lazy loading issues
        return await self.get_artifact(artifact_id, include_versions=True)

    async def delete_artifact(
        self,
        artifact_id: str,
        hard_delete: bool = False,
    ) -> bool:
        """
        Delete an artifact.

        Args:
            artifact_id: The artifact to delete
            hard_delete: If True, permanently delete. If False, archive.

        Returns:
            True if deleted/archived, False if not found
        """
        artifact = await self.get_artifact(artifact_id)
        if not artifact:
            return False

        if hard_delete:
            await self.session.delete(artifact)
        else:
            artifact.status = ArtifactStatus.ARCHIVED

        await self.session.flush()
        return True

    async def get_version(
        self,
        artifact_id: str,
        version_number: int,
    ) -> ArtifactVersion | None:
        """
        Get a specific version of an artifact.

        Args:
            artifact_id: The artifact ID
            version_number: The version number to retrieve

        Returns:
            The ArtifactVersion or None if not found
        """
        query = select(ArtifactVersion).where(
            ArtifactVersion.artifact_id == artifact_id,
            ArtifactVersion.version == version_number,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_versions(
        self,
        artifact_id: str,
        limit: int = 50,
    ) -> list[ArtifactVersion]:
        """
        List all versions of an artifact.

        Args:
            artifact_id: The artifact ID
            limit: Maximum number of versions to return

        Returns:
            List of ArtifactVersion objects, newest first
        """
        query = (
            select(ArtifactVersion)
            .where(ArtifactVersion.artifact_id == artifact_id)
            .order_by(ArtifactVersion.version.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def restore_version(
        self,
        artifact_id: str,
        version_number: int,
        restored_by: str | None = None,
    ) -> Artifact | None:
        """
        Restore an artifact to a previous version.

        This creates a new version with the content from the specified version.

        Args:
            artifact_id: The artifact to restore
            version_number: The version number to restore to
            restored_by: Who is performing the restore

        Returns:
            The updated Artifact or None if not found
        """
        # Get the version to restore
        target_version = await self.get_version(artifact_id, version_number)
        if not target_version:
            return None

        # Update artifact with the old version's content
        return await self.update_artifact(
            artifact_id=artifact_id,
            content=target_version.content,
            updated_by=restored_by or f"restore_to_v{version_number}",
        )

    async def get_current_version_number(self, artifact_id: str) -> int:
        """Get the current (latest) version number for an artifact."""
        query = select(func.max(ArtifactVersion.version)).where(
            ArtifactVersion.artifact_id == artifact_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 1
