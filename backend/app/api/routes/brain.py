"""Brain API routes for KG and venture profile operations."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, get_workspace
from app.core.brain.events.event_store import EventStore
from app.core.brain.kg.knowledge_graph import KnowledgeGraph
from app.core.brain.startup_brain import StartupBrain
from app.models.kg_entity import KGEntity, KGEntityStatus, KGEntityType, KGEventType
from app.models.venture import Venture
from app.schemas.brain import (
    BrainSearchRequest,
    BrainSearchResponse,
    ChunkResult,
    EntityCreate,
    EntityResponse,
    EntityUpdate,
    EvidenceResponse,
    ProposeUpdatesRequest,
    ProposeUpdatesResponse,
    VentureInfo,
    VentureProfileResponse,
)

router = APIRouter()


async def get_venture_for_workspace(workspace_id: str, db: AsyncSession, current_user) -> Venture:
    """Get venture for workspace, verifying access."""
    workspace = await get_workspace(workspace_id, db, current_user)
    result = await db.execute(select(Venture).where(Venture.workspace_id == workspace.id))
    venture = result.scalar_one_or_none()
    if not venture:
        raise HTTPException(status_code=404, detail="No venture configured for workspace")
    return venture


def entity_to_response(entity: KGEntity) -> EntityResponse:
    """Convert KGEntity model to response schema."""
    return EntityResponse(
        id=entity.id,
        type=entity.type.value,
        status=entity.status.value,
        data=entity.data,
        confidence=entity.confidence,
        evidence=[
            EvidenceResponse(
                id=e.id,
                snippet=e.snippet,
                source_type=e.source_type,
                document_id=e.document_id,
                agent_id=e.agent_id,
            )
            for e in (entity.evidence or [])
        ],
        created_at=entity.created_at.isoformat(),
        updated_at=entity.updated_at.isoformat(),
    )


@router.get("/profile/{workspace_id}", response_model=VentureProfileResponse)
async def get_venture_profile(
    workspace_id: str,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get the venture profile including all KG entities."""
    venture = await get_venture_for_workspace(workspace_id, db, current_user)
    brain = StartupBrain(venture.id, db)
    snapshot = await brain.get_snapshot()

    venture_info = None
    if snapshot.get("venture"):
        v = snapshot["venture"]
        venture_info = VentureInfo(
            id=v["id"],
            name=v["name"],
            stage=v["stage"],
            one_liner=v.get("one_liner"),
            problem=v.get("problem"),
            solution=v.get("solution"),
        )

    return VentureProfileResponse(
        venture=venture_info,
        entities=snapshot.get("entities", {}),
        metrics=snapshot.get("metrics"),
    )


@router.post("/entities", response_model=EntityResponse, status_code=201)
async def create_entity(
    workspace_id: str,
    request: EntityCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Create a new KG entity."""
    venture = await get_venture_for_workspace(workspace_id, db, current_user)
    kg = KnowledgeGraph(venture.id, db)
    events = EventStore(venture.id, db)

    # Map enum values
    entity_type = KGEntityType(request.type.value)
    status = KGEntityStatus(request.status.value) if request.status else None

    entity = await kg.create_entity(
        type=entity_type,
        data=request.data,
        confidence=request.confidence,
        status=status,
    )

    # Log event
    await events.log_event(
        event_type=KGEventType.CREATE,
        data={"type": entity_type.value, "data": request.data},
        entity_id=entity.id,
        user_id=current_user.id,
    )

    await db.commit()
    return entity_to_response(entity)


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    workspace_id: str,
    entity_id: str,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get a specific KG entity."""
    venture = await get_venture_for_workspace(workspace_id, db, current_user)
    kg = KnowledgeGraph(venture.id, db)

    entity = await kg.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return entity_to_response(entity)


@router.patch("/entities/{entity_id}", response_model=EntityResponse)
async def update_entity(
    workspace_id: str,
    entity_id: str,
    request: EntityUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Update a KG entity."""
    venture = await get_venture_for_workspace(workspace_id, db, current_user)
    kg = KnowledgeGraph(venture.id, db)
    events = EventStore(venture.id, db)

    # Map status if provided
    new_status = KGEntityStatus(request.status.value) if request.status else None

    entity = await kg.update_entity(
        entity_id=entity_id,
        updates=request.data or {},
        new_confidence=request.confidence,
        new_status=new_status,
    )

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Log event
    await events.log_event(
        event_type=KGEventType.UPDATE,
        data={"updates": request.data, "confidence": request.confidence, "status": request.status},
        entity_id=entity.id,
        user_id=current_user.id,
    )

    await db.commit()
    return entity_to_response(entity)


@router.delete("/entities/{entity_id}", status_code=204)
async def delete_entity(
    workspace_id: str,
    entity_id: str,
    db: DbSession,
    current_user: CurrentUser,
):
    """Delete a KG entity."""
    venture = await get_venture_for_workspace(workspace_id, db, current_user)
    kg = KnowledgeGraph(venture.id, db)
    events = EventStore(venture.id, db)

    # Get entity first to log event
    entity = await kg.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Log event before deletion
    await events.log_event(
        event_type=KGEventType.DELETE,
        data={"type": entity.type.value, "data": entity.data},
        entity_id=entity_id,
        user_id=current_user.id,
    )

    await kg.delete_entity(entity_id)
    await db.commit()


@router.post("/search", response_model=BrainSearchResponse)
async def search_brain(
    workspace_id: str,
    request: BrainSearchRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Search the brain (RAG + KG combined)."""
    venture = await get_venture_for_workspace(workspace_id, db, current_user)
    brain = StartupBrain(venture.id, db)

    # Map entity types if provided
    entity_types = None
    if request.entity_types:
        entity_types = [KGEntityType(t.value) for t in request.entity_types]

    result = await brain.retrieve(
        query=request.query,
        max_chunks=request.max_chunks,
        entity_types=entity_types,
        include_relations=request.include_relations,
    )

    return BrainSearchResponse(
        entities=[entity_to_response(e) for e in result.get("entities", [])],
        citations=[
            ChunkResult(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                snippet=c["snippet"],
                score=c["score"],
            )
            for c in result.get("citations", [])
        ],
    )


@router.post("/propose", response_model=ProposeUpdatesResponse)
async def propose_updates(
    workspace_id: str,
    request: ProposeUpdatesRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Propose KG updates (creates entities with SUGGESTED status)."""
    venture = await get_venture_for_workspace(workspace_id, db, current_user)
    brain = StartupBrain(venture.id, db)

    entities_data = [
        {
            "type": e.type.value,
            "data": e.data,
            "confidence": e.confidence,
        }
        for e in request.entities
    ]

    created = await brain.propose_updates(
        entities_data=entities_data,
        agent_id=request.agent_id,
        user_id=current_user.id,
    )

    await db.commit()

    return ProposeUpdatesResponse(
        created=[entity_to_response(e) for e in created],
        conflicts_detected=0,  # TODO: Count conflicts
    )
