"""Tests for the 5 engine tool handlers."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.tools.engine_tools import (
    handle_match_success_stories,
    handle_model_scenario,
    handle_rank_benchmarks,
    handle_run_valuation,
    handle_score_readiness,
)
from app.models.venture import VentureStage


def _make_ctx(stage: VentureStage = VentureStage.SEED) -> Any:
    """Create a mock ToolExecutor context."""
    ctx = MagicMock()
    ctx.venture.stage = stage
    ctx.venture.id = "venture-1"
    ctx.venture.name = "TestVenture"
    ctx.venture.one_liner = "A test venture"
    ctx.venture.problem = "Test problem"
    ctx.venture.solution = "Test solution"
    ctx.db = AsyncMock()
    ctx.brain = MagicMock()
    return ctx


# --------------------------------------------------------------------------- #
# run_valuation
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_run_valuation_revenue_multiple() -> None:
    """run_valuation returns valuation with revenue data."""
    ctx = _make_ctx()
    result = await handle_run_valuation(
        {"revenue": 1_000_000, "growth_rate": 1.5, "industry": "saas", "stage": "seed"},
        ctx,
    )
    assert result["mid"] > 0
    assert result["low"] > 0
    assert result["high"] > result["mid"]
    assert len(result["methods"]) >= 1


@pytest.mark.asyncio
async def test_run_valuation_no_revenue() -> None:
    """run_valuation with no revenue skips methods and returns warnings."""
    ctx = _make_ctx()
    result = await handle_run_valuation({}, ctx)
    assert result["mid"] == 0
    assert len(result["warnings"]) > 0


@pytest.mark.asyncio
async def test_run_valuation_with_comparables() -> None:
    """run_valuation with comparable exits includes comparable analysis."""
    ctx = _make_ctx()
    result = await handle_run_valuation(
        {
            "revenue": 500_000,
            "growth_rate": 1.0,
            "comparable_exits": [5_000_000, 10_000_000, 20_000_000],
        },
        ctx,
    )
    method_names = [m["method"] for m in result["methods"]]
    assert "comparable_analysis" in method_names


# --------------------------------------------------------------------------- #
# score_readiness
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_score_readiness_empty_kg() -> None:
    """score_readiness with no entities returns low score."""
    ctx = _make_ctx()
    ctx.brain.kg.get_entities_by_venture = AsyncMock(return_value=[])
    result = await handle_score_readiness({}, ctx)
    assert "overall_score" in result
    assert "grade" in result
    assert "dimensions" in result
    assert "top_priority_actions" in result


# --------------------------------------------------------------------------- #
# model_scenario
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_model_scenario_single_round() -> None:
    """model_scenario with a single round computes dilution."""
    ctx = _make_ctx()
    result = await handle_model_scenario(
        {
            "rounds": [
                {"raise_amount": 2_000_000, "pre_money_valuation": 8_000_000},
            ],
        },
        ctx,
    )
    assert len(result["scenarios"]) == 1
    assert result["scenarios"][0]["dilution_pct"] > 0
    assert len(result["exit_scenarios"]) > 0
    assert len(result["cap_table_progression"]) == 1


@pytest.mark.asyncio
async def test_model_scenario_multi_round() -> None:
    """model_scenario with multiple rounds tracks founder dilution."""
    ctx = _make_ctx()
    result = await handle_model_scenario(
        {
            "rounds": [
                {"raise_amount": 1_000_000, "pre_money_valuation": 4_000_000},
                {"raise_amount": 5_000_000, "pre_money_valuation": 20_000_000},
            ],
            "exit_multiples": [5.0, 10.0],
        },
        ctx,
    )
    assert len(result["scenarios"]) == 2
    # Founder ownership decreases with each round
    assert (
        result["scenarios"][1]["founder_ownership_after"]
        < result["scenarios"][0]["founder_ownership_after"]
    )
    assert len(result["exit_scenarios"]) == 2


# --------------------------------------------------------------------------- #
# rank_benchmarks
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_rank_benchmarks_saas_seed() -> None:
    """rank_benchmarks returns percentile data for saas/seed cohort."""
    ctx = _make_ctx()
    result = await handle_rank_benchmarks(
        {"industry": "saas", "stage": "seed", "metrics": {"mrr": 50000}},
        ctx,
    )
    assert "peer_cohort" in result
    assert "metrics" in result


@pytest.mark.asyncio
async def test_rank_benchmarks_no_cohort() -> None:
    """rank_benchmarks handles unknown industry/stage."""
    ctx = _make_ctx()
    result = await handle_rank_benchmarks(
        {"industry": "quantum_computing", "stage": "seed", "metrics": {}},
        ctx,
    )
    assert result["cohort_size"] == 0


# --------------------------------------------------------------------------- #
# match_success_stories
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_match_success_stories_basic() -> None:
    """match_success_stories returns matches with similarity scores."""
    ctx = _make_ctx()
    result = await handle_match_success_stories(
        {"industry": "saas", "stage": "seed", "top_n": 3},
        ctx,
    )
    assert "matches" in result
    assert len(result["matches"]) <= 3
    if result["matches"]:
        assert "similarity_score" in result["matches"][0]
        assert "parallels" in result["matches"][0]
