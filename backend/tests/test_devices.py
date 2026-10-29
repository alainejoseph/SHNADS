"""Tests for the /api/devices endpoints."""

from datetime import datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_devices_empty(client: AsyncClient) -> None:
    """Listing devices on a fresh database should return an empty list."""
    response = await client.get("/api/devices")
    assert response.status_code == 200

    data = response.json()
    assert data["devices"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 20


@pytest.mark.asyncio
async def test_list_devices_with_data(client: AsyncClient, test_db) -> None:
    """Listing devices should return inserted devices."""
    # Seed some devices.
    now = datetime.utcnow()
    devices = [
        {
            "device_key": "192.168.1.10_aa:bb:cc:dd:ee:01",
            "ip_address": "192.168.1.10",
            "mac_address": "aa:bb:cc:dd:ee:01",
            "hostname": "light-bulb",
            "first_seen": now,
            "last_seen": now,
            "source": "arp_discovery",
            "metadata": {},
        },
        {
            "device_key": "192.168.1.20_aa:bb:cc:dd:ee:02",
            "ip_address": "192.168.1.20",
            "mac_address": "aa:bb:cc:dd:ee:02",
            "hostname": "thermostat",
            "first_seen": now,
            "last_seen": now,
            "source": "passive_capture",
            "metadata": {},
        },
    ]
    await test_db["devices"].insert_many(devices)

    response = await client.get("/api/devices")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert len(data["devices"]) == 2


@pytest.mark.asyncio
async def test_search_devices(client: AsyncClient, test_db) -> None:
    """The search parameter should filter devices by IP, MAC, or hostname."""
    now = datetime.utcnow()
    await test_db["devices"].insert_many(
        [
            {
                "device_key": "10.0.0.1",
                "ip_address": "10.0.0.1",
                "mac_address": None,
                "hostname": "router",
                "first_seen": now,
                "last_seen": now,
                "source": "manual",
                "metadata": {},
            },
            {
                "device_key": "10.0.0.2",
                "ip_address": "10.0.0.2",
                "mac_address": None,
                "hostname": "camera",
                "first_seen": now,
                "last_seen": now,
                "source": "manual",
                "metadata": {},
            },
        ]
    )

    # Search by hostname
    response = await client.get("/api/devices", params={"search": "router"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["devices"][0]["hostname"] == "router"


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient, test_db) -> None:
    """Pagination parameters (skip, limit) should work correctly."""
    now = datetime.utcnow()
    docs = [
        {
            "device_key": f"192.168.1.{i}",
            "ip_address": f"192.168.1.{i}",
            "mac_address": None,
            "hostname": None,
            "first_seen": now,
            "last_seen": now,
            "source": "manual",
            "metadata": {},
        }
        for i in range(5)
    ]
    await test_db["devices"].insert_many(docs)

    response = await client.get("/api/devices", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["devices"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2

