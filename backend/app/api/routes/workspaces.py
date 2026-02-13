import re
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_workspace
from app.dependencies import get_db
from app.models.user import User
from app.models.venture import Venture
from app.models.workspace import Workspace, WorkspaceMembership, WorkspaceRole
from app.schemas.workspace import VentureResponse, VentureUpdate, WorkspaceCreate, WorkspaceResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _generate_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{slug}-{uuid.uuid4().hex[:8]}"


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    workspace = Workspace(
        name=request.name,
        slug=_generate_slug(request.name),
    )
    db.add(workspace)
    await db.flush()

    membership = WorkspaceMembership(
        user_id=current_user.id,
        workspace_id=workspace.id,
        role=WorkspaceRole.OWNER,
    )
    db.add(membership)

    venture = Venture(
        workspace_id=workspace.id,
        name=request.name,
    )
    db.add(venture)
    await db.flush()

    logger.info("workspace_created", workspace_id=str(workspace.id), user_id=str(current_user.id))

    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        slug=workspace.slug,
        role=WorkspaceRole.OWNER,
        venture=VentureResponse(
            id=str(venture.id),
            name=venture.name,
            stage=venture.stage,
            one_liner=venture.one_liner,
            problem=venture.problem,
            solution=venture.solution,
        ),
        created_at=workspace.created_at,
    )


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceResponse]:
    result = await db.execute(
        select(Workspace, WorkspaceMembership.role)
        .join(WorkspaceMembership)
        .options(selectinload(Workspace.venture))
        .where(WorkspaceMembership.user_id == current_user.id)
    )
    rows = result.all()

    return [
        WorkspaceResponse(
            id=str(ws.id),
            name=ws.name,
            slug=ws.slug,
            role=role,
            venture=VentureResponse(
                id=str(ws.venture.id),
                name=ws.venture.name,
                stage=ws.venture.stage,
                one_liner=ws.venture.one_liner,
                problem=ws.venture.problem,
                solution=ws.venture.solution,
            )
            if ws.venture
            else None,
            created_at=ws.created_at,
        )
        for ws, role in rows
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace_detail(
    workspace: Workspace = Depends(get_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    result = await db.execute(
        select(WorkspaceMembership.role).where(
            WorkspaceMembership.workspace_id == workspace.id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    role = result.scalar_one()

    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        slug=workspace.slug,
        role=role,
        venture=VentureResponse(
            id=str(workspace.venture.id),
            name=workspace.venture.name,
            stage=workspace.venture.stage,
            one_liner=workspace.venture.one_liner,
            problem=workspace.venture.problem,
            solution=workspace.venture.solution,
        )
        if workspace.venture
        else None,
        created_at=workspace.created_at,
    )


@router.patch("/{workspace_id}/venture", response_model=VentureResponse)
async def update_venture(
    update: VentureUpdate,
    workspace: Workspace = Depends(get_workspace),
    db: AsyncSession = Depends(get_db),
) -> VentureResponse:
    if workspace.venture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venture not found for this workspace",
        )

    venture = workspace.venture
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(venture, field, value)

    await db.flush()

    logger.info("venture_updated", venture_id=str(venture.id), fields=list(update_data.keys()))

    return VentureResponse(
        id=str(venture.id),
        name=venture.name,
        stage=venture.stage,
        one_liner=venture.one_liner,
        problem=venture.problem,
        solution=venture.solution,
    )
