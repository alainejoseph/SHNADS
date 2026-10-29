"""Dashboard API response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.capture import CaptureSessionResponse
from app.schemas.flow import FlowResponse


class ProtocolCount(BaseModel):
    """Protocol name with its flow count."""

    protocol: str
    count: int


class TimelineBucket(BaseModel):
    """Flow count for a specific hour bucket."""

    hour: str  # ISO-formatted hour string
    count: int


class DashboardSummary(BaseModel):
    """Aggregated dashboard statistics."""

    total_devices: int
    total_flows: int
    total_sessions: int
    active_capture: bool
    current_session: Optional[CaptureSessionResponse] = None
    recent_flows: List[FlowResponse] = []
    protocol_distribution: List[ProtocolCount] = []
    traffic_timeline: List[TimelineBucket] = []

