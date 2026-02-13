import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_workspace
from app.core.brain.kg.knowledge_graph import knowledge_graph
from app.core.brain.startup_brain import StartupBrain, startup_brain
from app.dependencies import get_db
from app.models.document import Document
from app.models.kg_entity import KGEntity
from app.models.user import User
from app.models.venture import Venture
from app.models.workspace import Workspace, WorkspaceMembership
from app.schemas.brain import (
    BrainSearchRequest,
    BrainSearchResponse,
    EntityCreate,
    EntityResult,
    EntityUpdate,
    VentureProfileResponse,
)
from app.schemas.workspace import VentureResponse
from app.services.embedding_service import embedding_service

logger = structlog.get_logger()

router = APIRouter(prefix="/brain", tags=["brain"])


async def _get_venture_for_workspace(
    workspace: Workspace,
    db: AsyncSession,
) -> Venture:
    """Get the venture for a workspace, raising 404 if not found."""
    stmt = select(Venture).where(Venture.workspace_id == workspace.id)
    result = await db.execute(stmt)
    venture = result.scalar_one_or_none()
    if venture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venture not found for workspace",
        )
    return venture


async def _verify_entity_access(
    entity_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> KGEntity:
    """Verify the user has access to the entity via workspace membership."""
    entity = await knowledge_graph.get_entity(db, entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )

    # Find the workspace via venture
    venture = await db.execute(
        select(Venture).where(Venture.id == entity.venture_id)
    )
    venture_obj = venture.scalar_one_or_none()
    if venture_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )

    # Check workspace membership
    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == venture_obj.workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )

    return entity


@router.post("/search", response_model=BrainSearchResponse)
async def brain_search(
    request: BrainSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrainSearchResponse:
    """Search the Startup Brain: RAG + KG combined."""
    # Verify workspace membership
    workspace_id = uuid.UUID(request.workspace_id)
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

    # Get venture
    venture_result = await db.execute(
        select(Venture).where(Venture.workspace_id == workspace_id)
    )
    venture = venture_result.scalar_one_or_none()
    if venture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venture not found",
        )

    # Embed the query
    query_embedding = embedding_service.embed_text(request.query)

    return await startup_brain.retrieve(
        db=db,
        venture_id=venture.id,
        query=request.query,
        query_embedding=query_embedding,
        entity_types=request.entity_types,
        max_chunks=request.max_chunks,
    )


@router.get("/profile/{workspace_id}", response_model=VentureProfileResponse)
async def venture_profile(
    workspace_id: uuid.UUID,
    workspace: Workspace = Depends(get_workspace),
    db: AsyncSession = Depends(get_db),
) -> VentureProfileResponse:
    """Get the full venture profile with all KG entities grouped by type."""
    venture = await _get_venture_for_workspace(workspace, db)

    entities, total_entities = await startup_brain.get_snapshot(db, venture.id)

    # Count documents
    doc_count_result = await db.execute(
        select(func.count())
        .select_from(Document)
        .where(Document.workspace_id == workspace.id)
    )
    total_documents = doc_count_result.scalar_one()

    entities_by_type = StartupBrain.group_entities_by_type(entities)

    return VentureProfileResponse(
        venture=VentureResponse(
            id=str(venture.id),
            name=venture.name,
            stage=venture.stage,
            one_liner=venture.one_liner,
            problem=venture.problem,
            solution=venture.solution,
        ),
        entities_by_type=entities_by_type,
        total_documents=total_documents,
        total_entities=total_entities,
    )


@router.post("/entities", response_model=EntityResult, status_code=status.HTTP_201_CREATED)
async def create_entity(
    request: EntityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntityResult:
    """Create a new KG entity manually."""
    venture_id = uuid.UUID(request.venture_id)

    # Verify venture exists and user has workspace access
    venture_result = await db.execute(
        select(Venture).where(Venture.id == venture_id)
    )
    venture = venture_result.scalar_one_or_none()
    if venture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venture not found",
        )

    membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == venture.workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venture not found",
        )

    try:
        entity = await knowledge_graph.create_entity(
            db=db,
            venture_id=venture_id,
            entity_type=request.type,
            data=request.data,
            confidence=request.confidence,
            actor=f"user:{current_user.id}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.info("entity_created_via_api", entity_id=str(entity.id))

    return EntityResult(
        id=str(entity.id),
        type=entity.type,
        status=entity.status,
        data=entity.data or {},
        confidence=entity.confidence,
        evidence_count=0,
    )


@router.patch("/entities/{entity_id}", response_model=EntityResult)
async def update_entity(
    entity_id: uuid.UUID,
    request: EntityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntityResult:
    """Update an existing KG entity."""
    entity = await _verify_entity_access(entity_id, current_user, db)

    try:
        updated = await knowledge_graph.update_entity(
            db=db,
            entity_id=entity_id,
            data=request.data,
            status=request.status,
            confidence=request.confidence,
            actor=f"user:{current_user.id}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return EntityResult(
        id=str(updated.id),
        type=updated.type,
        status=updated.status,
        data=updated.data or {},
        confidence=updated.confidence,
        evidence_count=len(entity.evidence) if entity.evidence else 0,
    )


@router.delete("/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a KG entity."""
    await _verify_entity_access(entity_id, current_user, db)

    try:
        await knowledge_graph.delete_entity(
            db=db,
            entity_id=entity_id,
            actor=f"user:{current_user.id}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
