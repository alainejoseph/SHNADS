"""Capture session API request/response schemas."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator


class CaptureStartRequest(BaseModel):
    """Request body to start a packet capture session."""

    interface: str = Field(..., description="Network interface to capture on")


class CaptureSessionResponse(BaseModel):
    """Single capture session returned by the API."""

    session_id: Optional[str] = None
    interface: Optional[str] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    status: Optional[str] = None
    packets_seen: int = 0
    flows_created: int = 0
    last_error: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def map_session_id(cls, values):
        if isinstance(values, dict):
            if values.get('session_id') is None and values.get('capture_session_id') is not None:
                values['session_id'] = values['capture_session_id']
            # Some sources might have different naming
        return values


class InterfaceInfo(BaseModel):
    """Network interface details."""

    name: str
    addresses: List[str] = []
    mac_address: Optional[str] = None
    is_up: bool = True
    is_loopback: bool = False
    description: str = ""


class CaptureStatusResponse(BaseModel):
    """Current capture engine status."""

    is_running: bool
    current_session: Optional[CaptureSessionResponse] = None
    available_interfaces: List[InterfaceInfo] = []


class CaptureSessionListResponse(BaseModel):
    """Paginated list of capture sessions."""

    sessions: List[CaptureSessionResponse]
    items: List[CaptureSessionResponse] = []
    total: int
    skip: int
    limit: int

    def __init__(self, **data: Any):
        if "items" not in data and "sessions" in data:
            data["items"] = data["sessions"]
        super().__init__(**data)
