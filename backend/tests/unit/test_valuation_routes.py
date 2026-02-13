import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_valuation_endpoint_returns_result(client: AsyncClient) -> None:
    """POST /valuation returns valuation result with methods."""
    resp = await client.post(
        "/api/v1/valuation",
        json={
            "revenue": 1_000_000,
            "growth_rate": 0.5,
            "industry": "saas",
            "stage": "seed",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["low"] > 0
    assert data["mid"] > data["low"]
    assert data["high"] > data["mid"]
    assert len(data["methods"]) >= 2  # revenue_multiple + dcf


@pytest.mark.asyncio
async def test_valuation_endpoint_empty_request(client: AsyncClient) -> None:
    """POST /valuation with no inputs returns warnings and zero values."""
    resp = await client.post("/api/v1/valuation", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["warnings"]) >= 3
    assert data["low"] == 0


@pytest.mark.asyncio
async def test_scenario_endpoint_returns_result(client: AsyncClient) -> None:
    """POST /scenarios returns funding scenarios and exit analysis."""
    resp = await client.post(
        "/api/v1/scenarios",
        json={
            "workspace_id": "00000000-0000-0000-0000-000000000001",
            "rounds": [
                {"raise_amount": 2_000_000, "pre_money_valuation": 8_000_000},
            ],
            "exit_multiples": [1.0, 5.0, 10.0],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["scenarios"]) == 1
    assert data["scenarios"][0]["dilution_pct"] == pytest.approx(20.0, rel=0.01)
    assert len(data["exit_scenarios"]) == 3


@pytest.mark.asyncio
async def test_benchmark_endpoint_returns_result(client: AsyncClient) -> None:
    """POST /benchmarks returns peer cohort metrics."""
    resp = await client.post(
        "/api/v1/benchmarks",
        json={
            "workspace_id": "00000000-0000-0000-0000-000000000001",
            "industry": "saas",
            "stage": "seed",
            "metrics": {"mrr_growth": 20},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cohort_size"] > 0
    assert data["peer_cohort"] == "Seed SaaS"
    assert len(data["metrics"]) > 0


@pytest.mark.asyncio
async def test_success_stories_endpoint_returns_matches(client: AsyncClient) -> None:
    """POST /benchmarks/success-stories returns top matches."""
    resp = await client.post(
        "/api/v1/benchmarks/success-stories",
        json={
            "workspace_id": "00000000-0000-0000-0000-000000000001",
            "industry": "saas",
            "stage": "seed",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["matches"]) == 5
    assert data["matches"][0]["similarity_score"] > 0
