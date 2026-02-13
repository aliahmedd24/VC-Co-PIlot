import pytest

from app.core.valuation.valuation_engine import ValuationEngine
from app.schemas.valuation import ValuationRequest


@pytest.fixture
def engine() -> ValuationEngine:
    return ValuationEngine()


def test_revenue_multiple_method_produces_range(engine: ValuationEngine) -> None:
    """Revenue multiple method returns low < mid < high for valid input."""
    req = ValuationRequest(
        revenue=1_000_000, growth_rate=1.0, industry="saas", stage="seed",
    )
    result = engine.valuate(req)

    rev_method = next(m for m in result.methods if m.method == "revenue_multiple")
    assert rev_method.low > 0
    assert rev_method.low < rev_method.mid < rev_method.high

    # SaaS seed multiples: low=10, mid=15, high=25, growth 1.0 → bracket [1.0, 2.0) → multiplier 1.3
    # Expected: 13M, 19.5M, 32.5M
    assert rev_method.low == pytest.approx(13_000_000, rel=0.01)
    assert rev_method.mid == pytest.approx(19_500_000, rel=0.01)
    assert rev_method.high == pytest.approx(32_500_000, rel=0.01)


def test_dcf_method_produces_positive_values(engine: ValuationEngine) -> None:
    """DCF method returns positive valuations for valid revenue + growth."""
    req = ValuationRequest(
        revenue=500_000, growth_rate=0.5, discount_rate=0.25, projection_years=5,
    )
    result = engine.valuate(req)

    dcf_method = next(m for m in result.methods if m.method == "dcf_simplified")
    assert dcf_method.low > 0
    assert dcf_method.mid > dcf_method.low
    assert dcf_method.high > dcf_method.mid

    # Verify details
    assert dcf_method.details["discount_rate"] == 0.25
    assert dcf_method.details["projection_years"] == 5


def test_comparable_analysis_uses_percentiles(engine: ValuationEngine) -> None:
    """Comparable analysis returns p25/p50/p75 of provided exits."""
    exits = [5_000_000, 8_000_000, 10_000_000, 15_000_000, 20_000_000]
    req = ValuationRequest(comparable_exits=exits)
    result = engine.valuate(req)

    comp_method = next(m for m in result.methods if m.method == "comparable_analysis")
    assert comp_method.low == pytest.approx(8_000_000, rel=0.01)   # p25
    assert comp_method.mid == pytest.approx(10_000_000, rel=0.01)  # median
    assert comp_method.high == pytest.approx(15_000_000, rel=0.01) # p75

    # Few comparables warning
    req_few = ValuationRequest(comparable_exits=[5_000_000, 10_000_000])
    result_few = engine.valuate(req_few)
    comp_few = next(m for m in result_few.methods if m.method == "comparable_analysis")
    assert any("unreliable" in w for w in comp_few.warnings)


def test_missing_inputs_returns_partial_with_warnings(engine: ValuationEngine) -> None:
    """Missing revenue/exits produces warnings and only available methods."""
    req = ValuationRequest()  # No revenue, no comparables
    result = engine.valuate(req)

    assert len(result.methods) == 0
    assert len(result.warnings) >= 3
    assert result.low == 0
    assert result.mid == 0

    # Partial: only comparable exits
    req2 = ValuationRequest(comparable_exits=[10_000_000, 20_000_000])
    result2 = engine.valuate(req2)
    assert len(result2.methods) == 1
    assert result2.methods[0].method == "comparable_analysis"
    assert any("Revenue multiple skipped" in w for w in result2.warnings)
