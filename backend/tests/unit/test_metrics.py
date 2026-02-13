import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_prometheus_endpoint_returns_metrics(client: AsyncClient) -> None:
    """GET /metrics returns Prometheus text format."""
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Prometheus metrics contain HELP and TYPE lines
    assert "http_request" in body or "HELP" in body or "TYPE" in body


@pytest.mark.asyncio
async def test_health_endpoint_still_works(client: AsyncClient) -> None:
    """GET /health returns healthy status (not broken by metrics middleware)."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}
