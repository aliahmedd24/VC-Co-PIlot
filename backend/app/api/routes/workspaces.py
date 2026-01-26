from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.venture import Venture, VentureStage
from app.models.workspace import Workspace, WorkspaceMembership, WorkspaceRole

router = APIRouter()


class WorkspaceCreate(BaseModel):
    name: str
    venture_name: str | None = None
    venture_stage: VentureStage = VentureStage.IDEATION


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str

    class Config:
        from_attributes = True


class WorkspaceDetailResponse(WorkspaceResponse):
    venture: dict | None = None


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Workspace:
    """Create a new workspace and venture."""
    # Generate unique slug
    base_slug = slugify(data.name)
    slug = base_slug
    counter = 1

    while True:
        result = await db.execute(select(Workspace).where(Workspace.slug == slug))
        if result.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create workspace
    workspace = Workspace(
        id=str(uuid4()),
        name=data.name,
        slug=slug,
    )
    db.add(workspace)
    await db.flush()

    # Add owner membership
    membership = WorkspaceMembership(
        id=str(uuid4()),
        user_id=current_user.id,
        workspace_id=workspace.id,
        role=WorkspaceRole.OWNER,
    )
    db.add(membership)

    # Create venture
    venture = Venture(
        id=str(uuid4()),
        workspace_id=workspace.id,
        name=data.venture_name or data.name,
        stage=data.venture_stage,
    )
    db.add(venture)

    await db.flush()
    return workspace


@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: DbSession,
    current_user: CurrentUser,
) -> list[Workspace]:
    """List workspaces for current user."""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMembership)
        .where(WorkspaceMembership.user_id == current_user.id)
        .order_by(Workspace.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get workspace details."""
    result = await db.execute(
        select(Workspace)
        .options(selectinload(Workspace.venture))
        .join(WorkspaceMembership)
        .where(
            Workspace.id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    venture_data = None
    if workspace.venture:
        venture_data = {
            "id": workspace.venture.id,
            "name": workspace.venture.name,
            "stage": workspace.venture.stage.value,
            "one_liner": workspace.venture.one_liner,
        }

    return {
        "id": workspace.id,
        "name": workspace.name,
        "slug": workspace.slug,
        "venture": venture_data,
    }


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a workspace (owner only)."""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMembership)
        .where(
            Workspace.id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
            WorkspaceMembership.role == WorkspaceRole.OWNER,
        )
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found or you are not the owner",
        )

    await db.delete(workspace)
