"""Device management routes."""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_device_service, get_discovery_service
from app.schemas.device import DeviceListResponse, DeviceResponse, DiscoveryResponse
from app.services.device_service import DeviceService
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=200, description="Max records to return"),
    search: Optional[str] = Query(
        None, description="Search by IP, MAC, or hostname"
    ),
    service: DeviceService = Depends(get_device_service),
) -> DeviceListResponse:
    """List all discovered devices with optional search and pagination."""
    devices, total = await service.list_devices(
        skip=skip, limit=limit, search=search
    )
    return DeviceListResponse(
        devices=[DeviceResponse(**d) for d in devices],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{device_key}", response_model=DeviceResponse)
async def get_device(
    device_key: str,
    service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    """Get a single device by its device key."""
    device = await service.get_device(device_key)
    if device is None:
        raise HTTPException(
            status_code=404,
            detail={"detail": f"Device '{device_key}' not found.", "error_code": "DEVICE_NOT_FOUND"},
        )
    return DeviceResponse(**device)


@router.post("/discover", response_model=DiscoveryResponse)
async def discover_devices(
    interface: Optional[str] = Query(None, description="Network interface to use"),
    discovery: DiscoveryService = Depends(get_discovery_service),
) -> DiscoveryResponse:
    """Trigger ARP-based network device discovery.

    The discovery runs asynchronously.  This endpoint returns immediately
    with a confirmation that the scan has been initiated.
    """
    # Fire and forget — run discovery in the background.
    asyncio.create_task(discovery.discover_devices(interface))
    return DiscoveryResponse(
        status="discovery_started",
        message="ARP discovery has been started on the network.",
    )

