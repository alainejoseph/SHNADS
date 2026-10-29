"""Shared API dependencies."""

from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_database
from app.services.capture_service import CaptureService
from app.services.device_service import DeviceService
from app.services.discovery_service import DiscoveryService
from app.services.flow_service import FlowService


async def get_device_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> DeviceService:
    """Provide a DeviceService instance."""
    return DeviceService(db)


async def get_flow_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> FlowService:
    """Provide a FlowService instance."""
    return FlowService(db)


async def get_discovery_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> DiscoveryService:
    """Provide a DiscoveryService instance."""
    return DiscoveryService(db)


def get_capture_service(request: Request) -> CaptureService:
    """Retrieve the CaptureService singleton stored on the app state.

    The CaptureService is created once during app startup and stored
    on ``app.state.capture_service``.
    """
    return request.app.state.capture_service

