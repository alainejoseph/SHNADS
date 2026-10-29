"""Flow API request/response schemas."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator


class FlowResponse(BaseModel):
    """Single flow returned by the API."""

    timestamp: Optional[datetime] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    packet_count: Optional[int] = 0
    byte_count: Optional[int] = 0
    duration_seconds: Optional[float] = 0.0
    tcp_flags_summary: Optional[str] = None
    interface: Optional[str] = None
    capture_session_id: Optional[str] = None
    flow_key: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    model_config = {"from_attributes": True}

    @model_validator(mode='before')
    @classmethod
    def map_timestamp(cls, values):
        if isinstance(values, dict):
            if values.get('timestamp') is None:
                st = values.get('start_time') or values.get('end_time')
                if st is not None:
                    try:
                        if isinstance(st, datetime):
                            values['timestamp'] = st
                        else:
                            values['timestamp'] = datetime.utcfromtimestamp(float(st))
                    except Exception:
                        pass
                elif values.get('time') is not None:
                    try:
                        t = values.get('time')
                        values['timestamp'] = datetime.utcfromtimestamp(float(t))
                    except Exception:
                        pass
            if values.get('capture_session_id') is None and values.get('session_id') is not None:
                values['capture_session_id'] = values['session_id']
        return values


class FlowListResponse(BaseModel):
    """Paginated list of flows."""

    flows: List[FlowResponse]
    items: List[FlowResponse] = []
    total: int
    skip: int
    limit: int

    def __init__(self, **data: Any):
        if "items" not in data and "flows" in data:
            data["items"] = data["flows"]
        super().__init__(**data)


class FlowFilters(BaseModel):
    """Query filters for flow listing."""

    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    protocol: Optional[str] = None
    session_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
