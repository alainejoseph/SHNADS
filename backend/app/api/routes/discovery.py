"""Device discovery API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.db.mongodb import get_database
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


class DiscoveryRequest(BaseModel):
    interface: Optional[str] = Field(None, description="Network interface to use for ARP discovery")


@router.post("/arp")
async def trigger_arp_discovery(
    payload: Optional[DiscoveryRequest] = None,
    interface: Optional[str] = Query(None, description="Network interface to use"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Trigger ARP-based device discovery on the local network."""
    selected_iface = (payload.interface if payload and payload.interface else None) or interface
    service = DiscoveryService(db)
    try:
        result = await service.discover_devices(interface=selected_iface)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Discovery failed"))
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

