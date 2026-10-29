"""Tests for the /api/dashboard/summary endpoint."""

from datetime import datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary_structure(client: AsyncClient) -> None:
    """The summary endpoint should return the expected JSON shape."""
    response = await client.get("/api/dashboard/summary")
    assert response.status_code == 200

    data = response.json()

    # Required top-level keys
    assert "total_devices" in data
    assert "total_flows" in data
    assert "total_sessions" in data
    assert "active_capture" in data
    assert "current_session" in data
    assert "recent_flows" in data
    assert "protocol_distribution" in data
    assert "traffic_timeline" in data

    # Types
    assert isinstance(data["total_devices"], int)
    assert isinstance(data["total_flows"], int)
    assert isinstance(data["total_sessions"], int)
    assert isinstance(data["active_capture"], bool)
    assert isinstance(data["recent_flows"], list)
    assert isinstance(data["protocol_distribution"], list)
    assert isinstance(data["traffic_timeline"], list)


@pytest.mark.asyncio
async def test_dashboard_summary_counts(client: AsyncClient, test_db) -> None:
    """Counts should reflect the data in the database."""
    now = datetime.utcnow()

    # Seed devices
    await test_db["devices"].insert_many(
        [
            {
                "device_key": f"10.0.0.{i}",
                "ip_address": f"10.0.0.{i}",
                "first_seen": now,
                "last_seen": now,
                "source": "manual",
                "metadata": {},
            }
            for i in range(3)
        ]
    )

    # Seed flows
    await test_db["flows"].insert_many(
        [
            {
                "timestamp": now,
                "src_ip": "10.0.0.1",
                "dst_ip": "10.0.0.2",
                "protocol": "TCP",
                "packet_count": 1,
                "byte_count": 100,
                "duration_seconds": 0.1,
                "interface": "eth0",
                "capture_session_id": "s1",
            }
            for _ in range(5)
        ]
    )

    response = await client.get("/api/dashboard/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["total_devices"] == 3
    assert data["total_flows"] == 5
    assert data["active_capture"] is False
    assert data["current_session"] is None


@pytest.mark.asyncio
async def test_dashboard_recent_flows_limited(client: AsyncClient, test_db) -> None:
    """recent_flows should contain at most 10 entries."""
    now = datetime.utcnow()
    await test_db["flows"].insert_many(
        [
            {
                "timestamp": now,
                "src_ip": "10.0.0.1",
                "dst_ip": f"10.0.0.{i}",
                "protocol": "UDP",
                "packet_count": 1,
                "byte_count": 50,
                "duration_seconds": 0.05,
                "interface": "eth0",
                "capture_session_id": "s1",
            }
            for i in range(15)
        ]
    )

    response = await client.get("/api/dashboard/summary")
    data = response.json()
    assert len(data["recent_flows"]) <= 10

