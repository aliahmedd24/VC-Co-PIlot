from fastapi import APIRouter

from app.core.benchmarks.benchmark_engine import benchmark_engine
from app.core.success_stories.matcher import success_story_matcher
from app.schemas.benchmark import (
    BenchmarkRequest,
    BenchmarkResult,
    SuccessStoryRequest,
    SuccessStoryResult,
)

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.post("", response_model=BenchmarkResult)
async def run_benchmark(
    request: BenchmarkRequest,
) -> BenchmarkResult:
    """Benchmark venture metrics against peer cohort."""
    return benchmark_engine.rank(
        industry=request.industry,
        stage=request.stage,
        metrics=request.metrics,
    )


@router.post("/success-stories", response_model=SuccessStoryResult)
async def match_success_stories(
    request: SuccessStoryRequest,
) -> SuccessStoryResult:
    """Find similar successful startups."""
    return success_story_matcher.match(
        industry=request.industry,
        stage=request.stage,
        business_model=request.business_model,
        attributes=request.attributes,
    )
