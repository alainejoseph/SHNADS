"""Devices API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_database
from app.services.device_service import DeviceService
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """List all discovered devices."""
    service = DeviceService(db)
    devices, total = await service.list_devices(skip=skip, limit=limit, search=search)
    return {"devices": devices, "total": total, "skip": skip, "limit": limit}


@router.get("/discover")
async def discover_devices_compat_get(
    interface: Optional[str] = Query(None, description="Network interface to use"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Trigger ARP-based device discovery (backward-compatible GET route)."""
    service = DiscoveryService(db)
    result = await service.discover_devices(interface=interface)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.post("/discover")
async def discover_devices_compat_post(
    interface: Optional[str] = Query(None, description="Network interface to use"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Trigger ARP-based device discovery (backward-compatible POST route)."""
    service = DiscoveryService(db)
    result = await service.discover_devices(interface=interface)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.get("/{device_key}")
async def get_device(
    device_key: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get details for a specific device."""
    service = DeviceService(db)
    device = await service.get_device(device_key)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
