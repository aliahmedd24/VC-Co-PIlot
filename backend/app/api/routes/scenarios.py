from fastapi import APIRouter

from app.core.scenario.scenario_modeler import scenario_modeler
from app.schemas.scenario import ScenarioModelResult, ScenarioRequest

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("", response_model=ScenarioModelResult)
async def run_scenario_model(
    request: ScenarioRequest,
) -> ScenarioModelResult:
    """Model funding rounds, dilution, and exit scenarios."""
    return scenario_modeler.model(
        rounds=request.rounds,
        exit_multiples=request.exit_multiples,
    )
