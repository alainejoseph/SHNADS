"""Tests for the /health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_healthy(client: AsyncClient) -> None:
    """The health endpoint should return status 'healthy'."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_reports_database_connected(client: AsyncClient) -> None:
    """The health endpoint should report database as 'connected'."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["database"] == "connected"

