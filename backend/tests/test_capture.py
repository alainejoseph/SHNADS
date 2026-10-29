"""Tests for the /api/capture endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from app.services.capture_service import CaptureService, PacketCapture


@pytest.mark.asyncio
async def test_capture_status_not_running(client: AsyncClient) -> None:
    """When no capture is active, status should report is_running=false."""
    response = await client.get("/api/capture/status")
    assert response.status_code == 200

    data = response.json()
    assert data["is_running"] is False
    assert data["current_session"] is None


@pytest.mark.asyncio
async def test_start_capture_invalid_interface(client: AsyncClient) -> None:
    """Starting capture on a non-existent interface should fail."""
    response = await client.post(
        "/api/capture/start",
        json={"interface": "nonexistent_iface_xyz"},
    )
    # Should be a 400 for invalid interface
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_start_and_stop_capture(client: AsyncClient) -> None:
    """Starting and stopping a capture should complete the lifecycle."""
    # Patch interface validation and the real PacketCapture so no raw
    # socket is opened (raw sockets are not available in the test sandbox).
    with (
        patch.object(CaptureService, "_validate_interface"),
        patch.object(PacketCapture, "start", new_callable=AsyncMock),
        patch.object(PacketCapture, "stop", new_callable=AsyncMock),
    ):
        # Start
        start_resp = await client.post(
            "/api/capture/start",
            json={"interface": "lo"},
        )
        assert start_resp.status_code == 200
        session = start_resp.json()
        assert session["status"] == "running"
        assert "session_id" in session

        # Status should now be running
        status_resp = await client.get("/api/capture/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["is_running"] is True

        # Stop
        stop_resp = await client.post("/api/capture/stop")
        assert stop_resp.status_code == 200
        stopped = stop_resp.json()
        assert stopped["status"] == "stopped"
        assert stopped["session_id"] == session["session_id"]


@pytest.mark.asyncio
async def test_duplicate_start_prevention(client: AsyncClient) -> None:
    """Starting a second capture while one is running should return 409."""
    with (
        patch.object(CaptureService, "_validate_interface"),
        patch.object(PacketCapture, "start", new_callable=AsyncMock),
        patch.object(PacketCapture, "stop", new_callable=AsyncMock),
    ):
        # Start first capture
        resp1 = await client.post(
            "/api/capture/start",
            json={"interface": "lo"},
        )
        assert resp1.status_code == 200

        # Attempt second start
        resp2 = await client.post(
            "/api/capture/start",
            json={"interface": "lo"},
        )
        assert resp2.status_code == 409

        # Clean up
        await client.post("/api/capture/stop")


@pytest.mark.asyncio
async def test_stop_when_not_running(client: AsyncClient) -> None:
    """Stopping a capture when none is running should return 409."""
    response = await client.post("/api/capture/stop")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_sessions_empty(client: AsyncClient) -> None:
    """Listing sessions when none exist should return an empty list."""
    response = await client.get("/api/capture/sessions")
    assert response.status_code == 200

    data = response.json()
    assert data["sessions"] == []
    assert data["total"] == 0

