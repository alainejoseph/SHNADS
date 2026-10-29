"""Tests for the /api/flows endpoints."""

from datetime import datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_flows_empty(client: AsyncClient) -> None:
    """Listing flows on a fresh database should return an empty list."""
    response = await client.get("/api/flows")
    assert response.status_code == 200

    data = response.json()
    assert data["flows"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_flows_with_data(client: AsyncClient, test_db) -> None:
    """Listing flows should return inserted flow documents."""
    now = datetime.utcnow()
    flows = [
        {
            "timestamp": now,
            "src_ip": "192.168.1.10",
            "dst_ip": "8.8.8.8",
            "src_port": 54321,
            "dst_port": 443,
            "protocol": "TCP",
            "packet_count": 12,
            "byte_count": 1500,
            "duration_seconds": 1.2,
            "tcp_flags_summary": "SYN,ACK",
            "interface": "eth0",
            "capture_session_id": "session-001",
        },
        {
            "timestamp": now,
            "src_ip": "192.168.1.20",
            "dst_ip": "1.1.1.1",
            "src_port": 12345,
            "dst_port": 53,
            "protocol": "UDP",
            "packet_count": 2,
            "byte_count": 200,
            "duration_seconds": 0.1,
            "tcp_flags_summary": None,
            "interface": "eth0",
            "capture_session_id": "session-001",
        },
    ]
    await test_db["flows"].insert_many(flows)

    response = await client.get("/api/flows")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert len(data["flows"]) == 2


@pytest.mark.asyncio
async def test_filter_by_protocol(client: AsyncClient, test_db) -> None:
    """Filtering by protocol should return only matching flows."""
    now = datetime.utcnow()
    await test_db["flows"].insert_many(
        [
            {
                "timestamp": now,
                "src_ip": "10.0.0.1",
                "dst_ip": "10.0.0.2",
                "protocol": "TCP",
                "packet_count": 1,
                "byte_count": 100,
                "duration_seconds": 0.5,
                "interface": "eth0",
                "capture_session_id": "s1",
            },
            {
                "timestamp": now,
                "src_ip": "10.0.0.3",
                "dst_ip": "10.0.0.4",
                "protocol": "UDP",
                "packet_count": 1,
                "byte_count": 50,
                "duration_seconds": 0.1,
                "interface": "eth0",
                "capture_session_id": "s1",
            },
        ]
    )

    response = await client.get("/api/flows", params={"protocol": "TCP"})
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["flows"][0]["protocol"] == "TCP"


@pytest.mark.asyncio
async def test_flow_pagination(client: AsyncClient, test_db) -> None:
    """Pagination should work for flows."""
    now = datetime.utcnow()
    docs = [
        {
            "timestamp": now,
            "src_ip": f"10.0.0.{i}",
            "dst_ip": "10.0.0.100",
            "protocol": "TCP",
            "packet_count": 1,
            "byte_count": 100,
            "duration_seconds": 0.1,
            "interface": "eth0",
            "capture_session_id": "s1",
        }
        for i in range(10)
    ]
    await test_db["flows"].insert_many(docs)

    response = await client.get("/api/flows", params={"skip": 3, "limit": 4})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 10
    assert len(data["flows"]) == 4

