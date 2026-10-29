"""Dashboard summary route."""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_capture_service, get_flow_service
from app.db.mongodb import get_database
from app.schemas.capture import CaptureSessionResponse
from app.schemas.dashboard import DashboardSummary, ProtocolCount, TimelineBucket
from app.schemas.flow import FlowResponse
from app.services.capture_service import CaptureService
from app.services.flow_service import FlowService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncIOMotorDatabase = Depends(get_database),
    flow_service: FlowService = Depends(get_flow_service),
    capture_service: CaptureService = Depends(get_capture_service),
) -> DashboardSummary:
    """Return aggregated dashboard statistics.

    Includes device/flow/session counts, the current capture state,
    recent flows, protocol distribution, and a 24-hour traffic timeline.
    """
    # Counts
    total_devices = await db["devices"].count_documents({})
    total_flows = await db["flows"].count_documents({})
    total_sessions = await db["capture_sessions"].count_documents({})

    # Current capture
    is_running = capture_service.is_running
    current_session_data = capture_service.current_session
    current_session = (
        CaptureSessionResponse(**current_session_data)
        if current_session_data
        else None
    )

    # Recent flows (last 10)
    recent_cursor = (
        db["flows"]
        .find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(10)
    )
    recent_flow_docs = await recent_cursor.to_list(length=10)
    recent_flows = [FlowResponse(**f) for f in recent_flow_docs]

    # Aggregation stats
    stats = await flow_service.get_flow_stats()
    protocol_distribution = [
        ProtocolCount(**p) for p in stats.get("protocol_distribution", [])
    ]
    traffic_timeline = [
        TimelineBucket(**t) for t in stats.get("traffic_timeline", [])
    ]

    return DashboardSummary(
        total_devices=total_devices,
        total_flows=total_flows,
        total_sessions=total_sessions,
        active_capture=is_running,
        current_session=current_session,
        recent_flows=recent_flows,
        protocol_distribution=protocol_distribution,
        traffic_timeline=traffic_timeline,
    )

