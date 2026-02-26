"""MCP server exposing the 5 analytics engine tools.

Provides run_valuation, score_readiness, model_scenario,
rank_benchmarks, and match_success_stories for external MCP clients.

Mount via FastAPI:
    from app.mcp.analytics_server import analytics_mcp_app
    app.mount("/mcp/analytics", analytics_mcp_app)
"""

from __future__ import annotations

from typing import Any

import structlog
from fastmcp import FastMCP

from app.core.benchmarks.benchmark_engine import benchmark_engine
from app.core.readiness.readiness_scorer import readiness_scorer
from app.core.scenarios.scenario_modeler import scenario_modeler
from app.core.success_stories.matcher import success_matcher
from app.core.valuation.valuation_engine import valuation_engine

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

analytics_mcp = FastMCP(
    "VC Analytics",
    instructions=(
        "Run startup analytics: valuations, readiness scores, "
        "scenario modeling, benchmark comparisons, and success "
        "story matching."
    ),
)


# ---------------------------------------------------------------------------
# Tool: run_valuation
# ---------------------------------------------------------------------------


@analytics_mcp.tool
async def run_valuation(
    revenue: float,
    growth_rate: float = 0.0,
    stage: str = "seed",
    sector: str = "saas",
    comparable_exits: list[float] | None = None,
) -> dict[str, Any]:
    """Calculate startup valuation using revenue multiples, DCF, and comparables.

    Args:
        revenue: Annual revenue or ARR in USD.
        growth_rate: Year-over-year growth rate (0-1 scale).
        stage: Funding stage (pre_seed, seed, series_a, series_b, growth).
        sector: Industry sector (saas, fintech, healthtech, etc.).
        comparable_exits: List of comparable exit valuations in USD.
    """
    result = valuation_engine.run(
        revenue=revenue,
        growth_rate=growth_rate,
        stage=stage,
        sector=sector,
        comparable_exits=comparable_exits or [],
    )
    return result


# ---------------------------------------------------------------------------
# Tool: score_readiness
# ---------------------------------------------------------------------------


@analytics_mcp.tool
async def score_readiness(
    venture_data: dict[str, Any],
) -> dict[str, Any]:
    """Score investor readiness across multiple dimensions.

    Evaluates team, market, product, traction, and financials.

    Args:
        venture_data: Dict with keys like team, market, product, etc.
    """
    return readiness_scorer.score(venture_data)


# ---------------------------------------------------------------------------
# Tool: model_scenario
# ---------------------------------------------------------------------------


@analytics_mcp.tool
async def model_scenario(
    pre_money_valuation: float,
    investment_amount: float,
    option_pool_pct: float = 0.1,
    existing_shares: int = 10_000_000,
) -> dict[str, Any]:
    """Model a funding round scenario (dilution, cap table effects).

    Args:
        pre_money_valuation: Pre-money valuation in USD.
        investment_amount: Amount being raised in USD.
        option_pool_pct: Option pool percentage (0-1).
        existing_shares: Number of existing shares outstanding.
    """
    return scenario_modeler.model_round(
        pre_money_valuation=pre_money_valuation,
        investment_amount=investment_amount,
        option_pool_pct=option_pool_pct,
        existing_shares=existing_shares,
    )


# ---------------------------------------------------------------------------
# Tool: rank_benchmarks
# ---------------------------------------------------------------------------


@analytics_mcp.tool
async def rank_benchmarks(
    stage: str,
    metrics: dict[str, float],
) -> dict[str, Any]:
    """Compare startup metrics against industry benchmarks.

    Args:
        stage: Funding stage (seed, series_a, etc.).
        metrics: Metric name to value map (e.g. {"mrr": 50000}).
    """
    return benchmark_engine.rank(stage=stage, metrics=metrics)


# ---------------------------------------------------------------------------
# Tool: match_success_stories
# ---------------------------------------------------------------------------


@analytics_mcp.tool
async def match_success_stories(
    sector: str = "saas",
    stage: str = "seed",
    business_model: str = "",
    top_n: int = 5,
) -> dict[str, Any]:
    """Find similar successful startups to inspire or validate strategy.

    Args:
        sector: Industry sector.
        stage: Current funding stage.
        business_model: Business model description.
        top_n: Number of matches to return.
    """
    return success_matcher.match(
        sector=sector,
        stage=stage,
        business_model=business_model,
        top_n=min(top_n, 10),
    )


# ---------------------------------------------------------------------------
# ASGI app for mounting into FastAPI
# ---------------------------------------------------------------------------

analytics_mcp_app = analytics_mcp.http_app(path="/mcp")
