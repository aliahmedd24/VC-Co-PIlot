"""Tool handlers wrapping the 5 existing pure-Python engines."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.benchmarks.benchmark_engine import benchmark_engine
from app.core.scenario.scenario_modeler import scenario_modeler
from app.core.scoring.readiness_scorer import readiness_scorer
from app.core.success_stories.matcher import success_story_matcher
from app.core.tools.registry import ToolDefinition, tool_registry
from app.core.valuation.valuation_engine import valuation_engine
from app.schemas.scenario import RoundInput
from app.schemas.valuation import ValuationRequest

if TYPE_CHECKING:
    from app.core.tools.executor import ToolExecutor


# --------------------------------------------------------------------------- #
# Tool: run_valuation
# --------------------------------------------------------------------------- #

RUN_VALUATION_DEF = ToolDefinition(
    name="run_valuation",
    description=(
        "Calculate startup valuation using revenue multiples, simplified DCF, "
        "and comparable analysis. Use when the user asks about valuation, "
        "company worth, or needs valuation data for fundraising."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "revenue": {
                "type": "number",
                "description": "Annual revenue or ARR in USD",
            },
            "growth_rate": {
                "type": "number",
                "description": "Year-over-year growth rate (e.g. 1.5 = 150% growth)",
            },
            "industry": {
                "type": "string",
                "default": "saas",
                "description": "Industry sector (saas, fintech, healthtech, ecommerce)",
            },
            "stage": {
                "type": "string",
                "default": "seed",
                "description": "Funding stage (seed, series_a, series_b, growth)",
            },
            "discount_rate": {
                "type": "number",
                "default": 0.30,
                "description": "DCF discount rate (0.01-1.0)",
            },
            "projection_years": {
                "type": "integer",
                "default": 5,
                "description": "Years for DCF projection (1-10)",
            },
            "comparable_exits": {
                "type": "array",
                "items": {"type": "number"},
                "description": "List of comparable exit valuations in USD",
            },
        },
    },
)


async def handle_run_valuation(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Execute the ValuationEngine with provided inputs."""
    request = ValuationRequest(
        revenue=tool_input.get("revenue"),
        growth_rate=tool_input.get("growth_rate"),
        industry=tool_input.get("industry", "saas"),
        stage=tool_input.get("stage", ctx.venture.stage.value),
        discount_rate=tool_input.get("discount_rate", 0.30),
        projection_years=tool_input.get("projection_years", 5),
        comparable_exits=tool_input.get("comparable_exits"),
    )
    result = valuation_engine.valuate(request)
    return result.model_dump()


# --------------------------------------------------------------------------- #
# Tool: score_readiness
# --------------------------------------------------------------------------- #

SCORE_READINESS_DEF = ToolDefinition(
    name="score_readiness",
    description=(
        "Assess investor readiness across 5 dimensions (team, product, market, "
        "traction, financials). Returns overall score, grade, dimension breakdown, "
        "gaps, and priority actions. Uses the venture's knowledge graph data."
    ),
    input_schema={
        "type": "object",
        "properties": {},
    },
)


async def handle_score_readiness(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Score readiness using all KG entities for the current venture."""
    from app.core.brain.startup_brain import StartupBrain

    entities_raw = await ctx.brain.kg.get_entities_by_venture(
        ctx.db, ctx.venture.id,
    )
    entity_results = [StartupBrain._entity_to_result(e) for e in entities_raw]
    result = readiness_scorer.score(
        entities=entity_results,
        venture_name=ctx.venture.name,
        venture_stage=ctx.venture.stage.value,
        venture_one_liner=ctx.venture.one_liner,
        venture_problem=ctx.venture.problem,
        venture_solution=ctx.venture.solution,
    )
    return result.model_dump()


# --------------------------------------------------------------------------- #
# Tool: model_scenario
# --------------------------------------------------------------------------- #

MODEL_SCENARIO_DEF = ToolDefinition(
    name="model_scenario",
    description=(
        "Model funding scenarios including dilution, cap table progression, "
        "and exit outcomes. Provide funding rounds with raise amounts and "
        "pre-money valuations."
    ),
    input_schema={
        "type": "object",
        "required": ["rounds"],
        "properties": {
            "rounds": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["raise_amount", "pre_money_valuation"],
                    "properties": {
                        "raise_amount": {
                            "type": "number",
                            "description": "Amount to raise in USD",
                        },
                        "pre_money_valuation": {
                            "type": "number",
                            "description": "Pre-money valuation in USD",
                        },
                        "option_pool_pct": {
                            "type": "number",
                            "default": 0.10,
                            "description": "Option pool percentage (0.0-0.5)",
                        },
                    },
                },
                "minItems": 1,
                "maxItems": 5,
            },
            "exit_multiples": {
                "type": "array",
                "items": {"type": "number"},
                "default": [1.0, 3.0, 5.0, 10.0, 20.0],
                "description": "Multiples to model exit scenarios at",
            },
        },
    },
)


async def handle_model_scenario(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Execute the ScenarioModeler with provided round inputs."""
    rounds_raw = tool_input.get("rounds", [])
    rounds = [
        RoundInput(
            raise_amount=r["raise_amount"],
            pre_money_valuation=r["pre_money_valuation"],
            option_pool_pct=r.get("option_pool_pct", 0.10),
        )
        for r in rounds_raw
    ]
    exit_multiples = tool_input.get("exit_multiples")
    result = scenario_modeler.model(rounds=rounds, exit_multiples=exit_multiples)
    return result.model_dump()


# --------------------------------------------------------------------------- #
# Tool: rank_benchmarks
# --------------------------------------------------------------------------- #

RANK_BENCHMARKS_DEF = ToolDefinition(
    name="rank_benchmarks",
    description=(
        "Rank the venture's metrics against peer cohort benchmarks. Returns "
        "percentile rankings, strengths, and weaknesses compared to similar companies."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "industry": {
                "type": "string",
                "default": "saas",
                "description": "Industry sector for peer cohort",
            },
            "stage": {
                "type": "string",
                "default": "seed",
                "description": "Funding stage for peer cohort",
            },
            "metrics": {
                "type": "object",
                "additionalProperties": {"type": "number"},
                "description": "Metric name -> value map (e.g. {\"mrr\": 50000})",
            },
        },
    },
)


async def handle_rank_benchmarks(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Execute the BenchmarkEngine with provided metrics."""
    industry = tool_input.get("industry", "saas")
    stage = tool_input.get("stage", ctx.venture.stage.value)
    metrics = tool_input.get("metrics", {})
    result = benchmark_engine.rank(
        industry=industry,
        stage=stage,
        metrics=metrics,
    )
    return result.model_dump()


# --------------------------------------------------------------------------- #
# Tool: match_success_stories
# --------------------------------------------------------------------------- #

MATCH_SUCCESS_STORIES_DEF = ToolDefinition(
    name="match_success_stories",
    description=(
        "Find analogous startup success stories based on industry, stage, "
        "business model, and traits. Returns similar companies with parallels "
        "and differences."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "industry": {
                "type": "string",
                "description": "Industry sector to match against",
            },
            "stage": {
                "type": "string",
                "default": "seed",
                "description": "Funding stage",
            },
            "business_model": {
                "type": "string",
                "default": "",
                "description": "Business model type (e.g. saas, marketplace)",
            },
            "attributes": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "Additional attributes like traits",
            },
            "top_n": {
                "type": "integer",
                "default": 5,
                "description": "Number of matches to return",
            },
        },
    },
)


async def handle_match_success_stories(
    tool_input: dict[str, Any], ctx: ToolExecutor,
) -> dict[str, Any]:
    """Execute the SuccessStoryMatcher with provided attributes."""
    result = success_story_matcher.match(
        industry=tool_input.get("industry", "saas"),
        stage=tool_input.get("stage", ctx.venture.stage.value),
        business_model=tool_input.get("business_model", ""),
        attributes=tool_input.get("attributes"),
        top_n=tool_input.get("top_n", 5),
    )
    return result.model_dump()


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

def register_engine_tools() -> None:
    """Register all 5 engine tools with the global tool registry."""
    tool_registry.register(RUN_VALUATION_DEF, handle_run_valuation)
    tool_registry.register(SCORE_READINESS_DEF, handle_score_readiness)
    tool_registry.register(MODEL_SCENARIO_DEF, handle_model_scenario)
    tool_registry.register(RANK_BENCHMARKS_DEF, handle_rank_benchmarks)
    tool_registry.register(MATCH_SUCCESS_STORIES_DEF, handle_match_success_stories)
