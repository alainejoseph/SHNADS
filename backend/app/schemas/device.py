"""Device API request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class DeviceResponse(BaseModel):
    """Single device returned by the API."""

    device_key: str
    ip_address: str
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    first_seen: datetime
    last_seen: datetime
    source: str
    metadata: Dict[str, Any] = {}


class DeviceListResponse(BaseModel):
    """Paginated list of devices."""

    devices: List[DeviceResponse]
    items: List[DeviceResponse] = []
    total: int
    skip: int
    limit: int

    def __init__(self, **data: Any):
        if "items" not in data and "devices" in data:
            data["items"] = data["devices"]
        super().__init__(**data)


class DiscoveryResponse(BaseModel):
    """Response returned when network discovery is triggered."""

    status: str = "discovery_started"
    message: str = "ARP discovery has been started on the network."

