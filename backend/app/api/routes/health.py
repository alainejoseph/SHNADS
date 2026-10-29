"""Health check route."""

from datetime import datetime

from fastapi import APIRouter

from app.db.mongodb import mongodb_manager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Return application health status.

    Pings MongoDB to verify connectivity and returns the current
    status along with a timestamp.
    """
    db_connected = await mongodb_manager.is_connected()
    return {
        "status": "healthy",
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }

