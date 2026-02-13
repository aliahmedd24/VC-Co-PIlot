import pytest

from app.core.benchmarks.benchmark_engine import BenchmarkEngine


@pytest.fixture
def engine() -> BenchmarkEngine:
    return BenchmarkEngine()


def test_percentile_ranking_known_value(engine: BenchmarkEngine) -> None:
    """A known metric value is ranked correctly against the dataset."""
    result = engine.rank(
        industry="saas",
        stage="seed",
        metrics={"mrr_growth": 25},  # Should be top quartile for seed SaaS
    )

    assert result.cohort_size > 0
    assert result.peer_cohort == "Seed SaaS"

    mrr_metric = next(m for m in result.metrics if m.metric_name == "mrr_growth")
    assert mrr_metric.venture_value == 25
    assert mrr_metric.percentile > 50  # Above median
    assert mrr_metric.peer_median > 0


def test_peer_cohort_filtering_industry_stage(engine: BenchmarkEngine) -> None:
    """Only matching industry + stage companies are included."""
    saas_seed = engine.rank("saas", "seed", {})
    fintech_seed = engine.rank("fintech", "seed", {})

    # Different cohorts
    assert saas_seed.peer_cohort != fintech_seed.peer_cohort
    assert saas_seed.cohort_size != fintech_seed.cohort_size

    # Non-existent cohort
    empty = engine.rank("quantum", "pre_ipo", {})
    assert empty.cohort_size == 0


def test_strength_weakness_classification(engine: BenchmarkEngine) -> None:
    """Top quartile = 'strong', bottom quartile = 'weak'."""
    # Very high MRR growth + very low burn rate (inverted — low is bad for burn_rate context)
    result = engine.rank(
        industry="saas",
        stage="seed",
        metrics={"mrr_growth": 50, "burn_rate": 25000},
    )

    mrr_metric = next(m for m in result.metrics if m.metric_name == "mrr_growth")
    assert mrr_metric.status == "strong"  # 50% growth is well above seed SaaS median

    # Check that strengths/weaknesses lists populated
    assert len(result.strengths) > 0 or len(result.weaknesses) > 0
