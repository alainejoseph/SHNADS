"""Flow listing routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_flow_service
from app.schemas.flow import FlowFilters, FlowListResponse, FlowResponse
from app.services.flow_service import FlowService

router = APIRouter(prefix="/api/flows", tags=["flows"])


@router.get("", response_model=FlowListResponse)
async def list_flows(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    src_ip: Optional[str] = Query(None, description="Filter by source IP"),
    dst_ip: Optional[str] = Query(None, description="Filter by destination IP"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    session_id: Optional[str] = Query(None, description="Filter by capture session ID"),
    start_time: Optional[datetime] = Query(None, description="Filter flows with timestamp >= start_time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="Filter flows with timestamp <= end_time (ISO 8601)"),
    service: FlowService = Depends(get_flow_service),
) -> FlowListResponse:
    """List recent flows with optional filters and pagination.

    Results are sorted by timestamp in descending order.
    """
    filters = FlowFilters(
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=protocol,
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
    )
    from datetime import timezone

    flows, total = await service.list_flows(
        skip=skip, limit=limit, filters=filters
    )
    flow_responses = []
    for f in flows:
        doc = dict(f)
        ts = doc.get("timestamp")
        if isinstance(ts, __import__("datetime").datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            doc["timestamp"] = ts
        flow_responses.append(FlowResponse(**doc))
    return FlowListResponse(
        flows=flow_responses,
        total=total,
        skip=skip,
        limit=limit,
    )

