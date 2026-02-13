import json
import re
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.agents.registry import agent_registry
from app.core.artifacts.exporters.markdown_exporter import markdown_exporter
from app.core.artifacts.manager import artifact_manager
from app.core.brain.startup_brain import startup_brain
from app.core.router.moe_router import moe_router
from app.dependencies import get_db
from app.middleware.rate_limiter import EXPORT_RATE_LIMIT, limiter
from app.models.artifact import Artifact
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.user import User
from app.models.venture import Venture
from app.models.workspace import WorkspaceMembership
from app.schemas.artifact import (
    ArtifactChatRequest,
    ArtifactCreate,
    ArtifactExportRequest,
    ArtifactListResponse,
    ArtifactResponse,
    ArtifactUpdate,
    ArtifactVersionListResponse,
    ArtifactVersionResponse,
    ExportTaskResponse,
)
from app.schemas.chat import ChatMessageResponse, SendMessageResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

ARTIFACT_CONTENT_PATTERN = re.compile(
    r"<!--\s*ARTIFACT_CONTENT:\s*(\{.*?\})\s*-->", re.DOTALL
)


def _artifact_to_response(artifact: Artifact) -> ArtifactResponse:
    return ArtifactResponse(
        id=str(artifact.id),
        type=artifact.type,
        title=artifact.title,
        status=artifact.status,
        owner_agent=artifact.owner_agent,
        content=artifact.content,
        current_version=artifact.current_version,
        assumptions=artifact.assumptions,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


async def _verify_artifact_access(
    artifact_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Artifact:
    """Load artifact and verify user has workspace membership."""
    artifact = await artifact_manager.get(db, artifact_id)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == artifact.workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    return artifact


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    request: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """Create a new artifact."""
    workspace_id = uuid.UUID(request.workspace_id)

    # Verify workspace membership
    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    content = request.content or {}

    artifact = await artifact_manager.create(
        db=db,
        workspace_id=workspace_id,
        artifact_type=request.type,
        title=request.title,
        content=content,
        owner_agent="venture-architect",
        created_by_id=current_user.id,
    )

    return _artifact_to_response(artifact)


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    workspace_id: str,
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactListResponse:
    """List artifacts for a workspace."""
    ws_id = uuid.UUID(workspace_id)

    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == ws_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    artifacts = await artifact_manager.list_artifacts(
        db, ws_id, include_archived=include_archived
    )
    return ArtifactListResponse(
        artifacts=[_artifact_to_response(a) for a in artifacts]
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """Get a single artifact with content."""
    artifact = await _verify_artifact_access(artifact_id, current_user.id, db)
    return _artifact_to_response(artifact)


@router.patch("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: uuid.UUID,
    request: ArtifactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """Update artifact status or content with optimistic locking."""
    await _verify_artifact_access(artifact_id, current_user.id, db)

    if request.status is not None:
        await artifact_manager.update_status(db, artifact_id, request.status)

    if request.content is not None:
        await artifact_manager.update(
            db=db,
            artifact_id=artifact_id,
            content=request.content,
            expected_version=request.expected_version,
            created_by=f"user:{current_user.id}",
        )

    # Re-fetch to get clean state with updated timestamps
    artifact = await artifact_manager.get(db, artifact_id)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    if request.title is not None:
        artifact.title = request.title
        await db.flush()

    return _artifact_to_response(artifact)


@router.get("/{artifact_id}/versions", response_model=ArtifactVersionListResponse)
async def list_versions(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactVersionListResponse:
    """List all versions of an artifact."""
    await _verify_artifact_access(artifact_id, current_user.id, db)
    versions = await artifact_manager.get_versions(db, artifact_id)
    return ArtifactVersionListResponse(
        versions=[
            ArtifactVersionResponse(
                id=str(v.id),
                version=v.version,
                content=v.content,
                diff=v.diff,
                created_by=v.created_by,
                created_at=v.created_at,
            )
            for v in versions
        ]
    )


@router.get(
    "/{artifact_id}/versions/{version}", response_model=ArtifactVersionResponse
)
async def get_version(
    artifact_id: uuid.UUID,
    version: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactVersionResponse:
    """Get a specific version of an artifact."""
    await _verify_artifact_access(artifact_id, current_user.id, db)
    v = await artifact_manager.get_version(db, artifact_id, version)
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )
    return ArtifactVersionResponse(
        id=str(v.id),
        version=v.version,
        content=v.content,
        diff=v.diff,
        created_by=v.created_by,
        created_at=v.created_at,
    )


@router.post("/{artifact_id}/chat", response_model=SendMessageResponse)
async def artifact_chat(
    artifact_id: uuid.UUID,
    request: ArtifactChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    """Chat within artifact context — routes to owner agent for refinement."""
    artifact = await _verify_artifact_access(artifact_id, current_user.id, db)

    # Get venture for the workspace
    venture_result = await db.execute(
        select(Venture).where(Venture.workspace_id == artifact.workspace_id)
    )
    venture = venture_result.scalar_one_or_none()
    if venture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace has no venture configured",
        )

    # Get the owner agent
    agent = agent_registry.get(artifact.owner_agent)
    if agent is None:
        agent = agent_registry.get("venture-architect")
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No agents available",
            )

    # Route with artifact continuation
    routing_plan = moe_router.route(
        message=request.content,
        venture_stage=venture.stage,
        active_artifact_agent=artifact.owner_agent,
    )

    # Create or get chat session for this artifact
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.workspace_id == artifact.workspace_id,
        ).order_by(ChatSession.updated_at.desc()).limit(1)
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        session = ChatSession(
            workspace_id=artifact.workspace_id,
            title=f"Artifact: {artifact.title}",
        )
        db.add(session)
        await db.flush()

    # Build enriched prompt with artifact context
    artifact_context = (
        f"\n\n## Current Artifact Content\n"
        f"Type: {artifact.type.value}\n"
        f"Title: {artifact.title}\n"
        f"Content: {json.dumps(artifact.content, indent=2)}\n\n"
        f"Please refine the artifact based on the user's request. "
        f"Return the updated artifact content as a JSON block wrapped in "
        f"<!-- ARTIFACT_CONTENT: {{...}} --> markers."
    )
    enriched_prompt = request.content + artifact_context

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=request.content,
        artifact_id=artifact_id,
    )
    db.add(user_msg)
    await db.flush()

    # Execute agent
    response = await agent.execute(
        prompt=enriched_prompt,
        brain=startup_brain,
        db=db,
        venture=venture,
        routing_plan=routing_plan,
        session_id=str(session.id),
        user_id=str(current_user.id),
    )

    # Try to extract structured artifact content from response
    content_match = ARTIFACT_CONTENT_PATTERN.search(response.content)
    if content_match:
        try:
            new_content: dict[str, object] = json.loads(content_match.group(1))
            await artifact_manager.update(
                db=db,
                artifact_id=artifact_id,
                content=new_content,
                expected_version=artifact.current_version,
                created_by=f"agent:{artifact.owner_agent}",
            )
        except (json.JSONDecodeError, HTTPException):
            logger.warning(
                "artifact_content_extraction_failed",
                artifact_id=str(artifact_id),
            )

    # Clean content (remove ARTIFACT_CONTENT markers)
    clean_content = ARTIFACT_CONTENT_PATTERN.sub("", response.content).strip()

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=clean_content,
        agent_id=routing_plan.selected_agent,
        routing_plan=routing_plan.model_dump(),
        citations=response.citations,
        artifact_id=artifact_id,
    )
    db.add(assistant_msg)
    await db.flush()

    return SendMessageResponse(
        session_id=str(session.id),
        user_message=ChatMessageResponse(
            id=str(user_msg.id),
            role=user_msg.role,
            content=user_msg.content,
            agent_id=None,
            citations=None,
            created_at=user_msg.created_at,
        ),
        assistant_message=ChatMessageResponse(
            id=str(assistant_msg.id),
            role=assistant_msg.role,
            content=assistant_msg.content,
            agent_id=assistant_msg.agent_id,
            citations=assistant_msg.citations,
            created_at=assistant_msg.created_at,
        ),
        routing_plan=routing_plan,
        proposed_updates=response.proposed_updates,
    )


@router.post("/{artifact_id}/export", response_model=None)
@limiter.limit(EXPORT_RATE_LIMIT)
async def export_artifact(
    artifact_id: uuid.UUID,
    export_request: ArtifactExportRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse | ExportTaskResponse:
    """Export artifact to markdown (sync) or PDF (async via Celery)."""
    artifact = await _verify_artifact_access(artifact_id, current_user.id, db)

    if export_request.format == "markdown":
        md = markdown_exporter.export(artifact.type, artifact.title, artifact.content)
        return PlainTextResponse(content=md, media_type="text/markdown")

    # PDF export via Celery
    from app.workers.export_tasks import export_artifact_pdf

    task = export_artifact_pdf.delay(str(artifact_id))
    return ExportTaskResponse(
        task_id=task.id,
        status="pending",
    )
