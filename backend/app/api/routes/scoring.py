import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.brain.startup_brain import startup_brain
from app.core.scoring.readiness_scorer import readiness_scorer
from app.dependencies import get_db
from app.models.user import User
from app.models.venture import Venture
from app.models.workspace import WorkspaceMembership
from app.schemas.scoring import InvestorReadinessScore, ReadinessRequest

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.post("/readiness", response_model=InvestorReadinessScore)
async def get_readiness_score(
    request: ReadinessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvestorReadinessScore:
    """Evaluate investor readiness across 5 dimensions using KG data."""
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

    venture_result = await db.execute(
        select(Venture).where(Venture.workspace_id == workspace_id)
    )
    venture = venture_result.scalar_one_or_none()
    if venture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace has no venture configured",
        )

    entities_raw, _ = await startup_brain.get_snapshot(db=db, venture_id=venture.id)
    entity_results = [startup_brain._entity_to_result(e) for e in entities_raw]

    return readiness_scorer.score(
        entities=entity_results,
        venture_name=venture.name,
        venture_stage=venture.stage.value,
        venture_one_liner=venture.one_liner,
        venture_problem=venture.problem,
        venture_solution=venture.solution,
    )
