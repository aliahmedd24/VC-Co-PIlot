from fastapi import APIRouter

from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.auth import router as auth_router
from app.api.routes.benchmarks import router as benchmarks_router
from app.api.routes.brain import router as brain_router
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.scoring import router as scoring_router
from app.api.routes.valuation import router as valuation_router
from app.api.routes.workspaces import router as workspaces_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(workspaces_router)
api_router.include_router(documents_router)
api_router.include_router(brain_router)
api_router.include_router(chat_router)
api_router.include_router(artifacts_router)
api_router.include_router(scoring_router)
api_router.include_router(valuation_router)
api_router.include_router(scenarios_router)
api_router.include_router(benchmarks_router)
