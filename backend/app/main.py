from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.config import settings
from app.mcp.analytics_server import analytics_mcp_app
from app.mcp.brain_server import mcp_app
from app.mcp.memory_server import memory_mcp_app
from app.mcp.research_server import research_mcp_app
from app.middleware.metrics import instrumentator
from app.middleware.rate_limiter import limiter

logger = structlog.get_logger()


def _register_tools() -> None:
    """Register all agent tools at startup."""
    from app.core.tools.artifact_tools import register_artifact_tools
    from app.core.tools.brain_tools import register_brain_tools
    from app.core.tools.delegation_tools import register_delegation_tools
    from app.core.tools.document_tools import register_document_tools
    from app.core.tools.engine_tools import register_engine_tools
    from app.core.tools.presentation_tools import register_presentation_tools
    from app.core.tools.research_tools import register_research_tools
    from app.core.tools.skill_tools import register_skill_tools

    register_engine_tools()
    register_brain_tools()
    register_artifact_tools()
    register_research_tools()
    register_delegation_tools()
    register_skill_tools()
    register_presentation_tools()
    register_document_tools()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _register_tools()
    logger.info("app_starting", app_name=settings.app_name)
    async with (
        mcp_app.lifespan(app),
        analytics_mcp_app.lifespan(app),
        research_mcp_app.lifespan(app),
        memory_mcp_app.lifespan(app),
    ):
        yield
    logger.info("app_shutting_down")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
instrumentator.instrument(app).expose(app, endpoint="/metrics")

app.include_router(api_router)

# MCP server — accessible at /mcp/brain/mcp
app.mount("/mcp/brain", mcp_app)
app.mount("/mcp/analytics", analytics_mcp_app)
app.mount("/mcp/research", research_mcp_app)
app.mount("/mcp/memory", memory_mcp_app)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
