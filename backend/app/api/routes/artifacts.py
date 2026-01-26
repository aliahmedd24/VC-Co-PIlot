"""Artifact API routes for CRUD operations, versioning, chat, and export."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, get_workspace
from app.core.agents.router import AgentRouter
from app.core.artifacts.manager import ArtifactManager
from app.core.brain.startup_brain import StartupBrain
from app.models.artifact import Artifact, ArtifactStatus, ArtifactType
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.venture import Venture
from app.schemas.artifact import (
    ArtifactChatRequest,
    ArtifactCreate,
    ArtifactExportRequest,
    ArtifactExportResponse,
    ArtifactListResponse,
    ArtifactResponse,
    ArtifactUpdate,
    ArtifactVersionResponse,
    ExportFormat,
)
from app.services.embeddings import EmbeddingService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def _artifact_to_response(artifact: Artifact, version_number: int = 1) -> ArtifactResponse:
    """Convert Artifact model to response schema."""
    versions = []
    
    # Check if versions are loaded to avoid implicit lazy load in async
    is_loaded = "versions" not in inspect(artifact).unloaded
    
    if is_loaded and artifact.versions:
        versions = [
            ArtifactVersionResponse(
                id=v.id,
                version=v.version,
                content=v.content,
                diff=v.diff,
                created_by=v.created_by,
                created_at=v.created_at,
            )
            for v in artifact.versions
        ]

    return ArtifactResponse(
        id=artifact.id,
        workspace_id=artifact.workspace_id,
        type=artifact.type,
        title=artifact.title,
        status=artifact.status,
        owner_agent=artifact.owner_agent,
        content=artifact.content,
        assumptions=artifact.assumptions,
        created_by_id=artifact.created_by_id,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
        current_version=version_number,
        versions=versions,
    )


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    workspace_id: str,
    db: DbSession,
    current_user: CurrentUser,
    artifact_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """List artifacts for a workspace."""
    # Verify workspace access
    await get_workspace(workspace_id, db, current_user)

    manager = ArtifactManager(db)

    # Parse filters
    type_filter = ArtifactType(artifact_type) if artifact_type else None
    status_filter = ArtifactStatus(status) if status else None

    artifacts, total = await manager.list_artifacts(
        workspace_id=workspace_id,
        artifact_type=type_filter,
        status=status_filter,
        page=page,
        page_size=page_size,
    )

    # Get version numbers for each artifact
    items = []
    for artifact in artifacts:
        version_num = await manager.get_current_version_number(artifact.id)
        items.append(_artifact_to_response(artifact, version_num))

    return ArtifactListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("", response_model=ArtifactResponse, status_code=201)
async def create_artifact(
    request: ArtifactCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Create a new artifact."""
    # Verify workspace access
    await get_workspace(request.workspace_id, db, current_user)

    manager = ArtifactManager(db)

    artifact = await manager.create_artifact(
        workspace_id=request.workspace_id,
        artifact_type=ArtifactType(request.type.value),
        title=request.title,
        owner_agent=request.owner_agent,
        content=request.content,
        assumptions=request.assumptions,
        created_by_id=current_user.id,
    )

    await db.commit()
    await db.refresh(artifact)

    return _artifact_to_response(artifact, 1)


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    db: DbSession,
    current_user: CurrentUser,
    include_versions: bool = False,
):
    """Get an artifact by ID."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id, include_versions=include_versions)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    await get_workspace(artifact.workspace_id, db, current_user)

    version_num = await manager.get_current_version_number(artifact_id)
    return _artifact_to_response(artifact, version_num)


@router.patch("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: str,
    request: ArtifactUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Update an artifact. Content changes create a new version."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    await get_workspace(artifact.workspace_id, db, current_user)

    updated = await manager.update_artifact(
        artifact_id=artifact_id,
        title=request.title,
        status=ArtifactStatus(request.status.value) if request.status else None,
        content=request.content,
        assumptions=request.assumptions,
        updated_by=current_user.id,
    )

    await db.commit()
    await db.refresh(updated)

    version_num = await manager.get_current_version_number(artifact_id)
    return _artifact_to_response(updated, version_num)


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: str,
    db: DbSession,
    current_user: CurrentUser,
    hard_delete: bool = False,
):
    """Delete or archive an artifact."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    await get_workspace(artifact.workspace_id, db, current_user)

    await manager.delete_artifact(artifact_id, hard_delete=hard_delete)
    await db.commit()

    return {"status": "deleted" if hard_delete else "archived"}


@router.get("/{artifact_id}/versions", response_model=list[ArtifactVersionResponse])
async def list_versions(
    artifact_id: str,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = 50,
):
    """List version history for an artifact."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    await get_workspace(artifact.workspace_id, db, current_user)

    versions = await manager.list_versions(artifact_id, limit=limit)

    return [
        ArtifactVersionResponse(
            id=v.id,
            version=v.version,
            content=v.content,
            diff=v.diff,
            created_by=v.created_by,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/{artifact_id}/versions/{version}", response_model=ArtifactVersionResponse)
async def get_version(
    artifact_id: str,
    version: int,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get a specific version of an artifact."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    await get_workspace(artifact.workspace_id, db, current_user)

    version_obj = await manager.get_version(artifact_id, version)

    if not version_obj:
        raise HTTPException(status_code=404, detail="Version not found")

    return ArtifactVersionResponse(
        id=version_obj.id,
        version=version_obj.version,
        content=version_obj.content,
        diff=version_obj.diff,
        created_by=version_obj.created_by,
        created_at=version_obj.created_at,
    )


@router.post("/{artifact_id}/restore/{version}", response_model=ArtifactResponse)
async def restore_version(
    artifact_id: str,
    version: int,
    db: DbSession,
    current_user: CurrentUser,
):
    """Restore an artifact to a previous version."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    await get_workspace(artifact.workspace_id, db, current_user)

    restored = await manager.restore_version(
        artifact_id=artifact_id,
        version_number=version,
        restored_by=current_user.id,
    )

    if not restored:
        raise HTTPException(status_code=404, detail="Version not found")

    await db.commit()
    await db.refresh(restored)

    version_num = await manager.get_current_version_number(artifact_id)
    return _artifact_to_response(restored, version_num)


@router.post("/{artifact_id}/chat")
async def artifact_chat(
    artifact_id: str,
    request: ArtifactChatRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Chat within the context of an artifact."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    workspace = await get_workspace(artifact.workspace_id, db, current_user)

    # Get venture for brain
    result = await db.execute(select(Venture).where(Venture.workspace_id == workspace.id))
    venture = result.scalar_one_or_none()

    if not venture:
        raise HTTPException(status_code=400, detail="No venture configured")

    # Get or create chat session
    if request.session_id:
        sess_result = await db.execute(
            select(ChatSession).where(ChatSession.id == request.session_id)
        )
        session = sess_result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(
            id=str(uuid4()),
            workspace_id=workspace.id,
            title=f"Artifact: {artifact.title[:40]}",
        )
        db.add(session)
        await db.flush()

    # Save user message
    user_msg = ChatMessage(
        id=str(uuid4()),
        session_id=session.id,
        role=MessageRole.USER,
        content=request.content,
        user_id=current_user.id,
        artifact_id=artifact_id,
    )
    db.add(user_msg)

    # Initialize brain with artifact context
    embedder = EmbeddingService()
    brain = StartupBrain(venture.id, db, embedder)

    # Route to artifact's owner agent
    agent_router = AgentRouter()
    agent = agent_router.get_agent(artifact.owner_agent)

    if not agent:
        raise HTTPException(status_code=500, detail=f"Agent not found: {artifact.owner_agent}")

    # Build artifact context prompt
    artifact_context = f"""
You are working on an artifact:
- Title: {artifact.title}
- Type: {artifact.type.value}
- Status: {artifact.status.value}

Current Content:
{artifact.content}

User's request about this artifact:
"""

    # Get routing plan
    routing_plan = await agent_router.route(request.content, {"active_artifact": artifact_id})

    # Execute agent with artifact context
    response = await agent.execute(
        prompt=artifact_context + request.content,
        brain=brain,
        routing_plan=routing_plan,
        session_id=session.id,
        user_id=current_user.id,
    )

    # Save assistant message
    assistant_msg = ChatMessage(
        id=str(uuid4()),
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=response.content,
        agent_id=agent.name,
        artifact_id=artifact_id,
        citations=response.citations,
    )
    db.add(assistant_msg)
    await db.commit()

    return {
        "session_id": session.id,
        "message_id": assistant_msg.id,
        "content": response.content,
        "agent_id": agent.name,
        "artifact_id": artifact_id,
        "citations": response.citations,
        "proposed_updates": response.proposed_updates,
    }


@router.post("/{artifact_id}/export", response_model=ArtifactExportResponse)
async def export_artifact(
    artifact_id: str,
    request: ArtifactExportRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Export an artifact to Markdown or PDF."""
    manager = ArtifactManager(db)
    artifact = await manager.get_artifact(artifact_id, include_versions=request.include_versions)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify workspace access
    await get_workspace(artifact.workspace_id, db, current_user)

    # Queue export task
    from app.workers.export_tasks import export_artifact_task

    task = export_artifact_task.delay(
        artifact_id=artifact_id,
        format=request.format.value,
        include_versions=request.include_versions,
    )

    return ArtifactExportResponse(
        artifact_id=artifact_id,
        format=request.format,
        task_id=task.id,
        status="pending",
    )
