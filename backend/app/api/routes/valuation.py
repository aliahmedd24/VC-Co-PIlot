from fastapi import APIRouter

from app.core.valuation.valuation_engine import valuation_engine
from app.schemas.valuation import ValuationRequest, ValuationResult

router = APIRouter(prefix="/valuation", tags=["valuation"])


@router.post("", response_model=ValuationResult)
async def run_valuation(
    request: ValuationRequest,
) -> ValuationResult:
    """Run startup valuation using up to 3 methods."""
    return valuation_engine.valuate(request)
