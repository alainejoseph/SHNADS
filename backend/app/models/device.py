"""Device MongoDB document model."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DeviceDocument(BaseModel):
    """Represents a network device observed on the local network.

    The ``device_key`` field acts as a composite unique identifier,
    typically formatted as ``"{ip}_{mac}"`` or just ``"{ip}"`` when the
    MAC address is unknown.
    """

    device_key: str = Field(
        ..., description="Composite key, e.g. '{ip}_{mac}' or '{ip}'"
    )
    ip_address: str = Field(..., description="IP address of the device")
    mac_address: Optional[str] = Field(
        default=None, description="MAC address if known"
    )
    hostname: Optional[str] = Field(
        default=None, description="Hostname if resolved"
    )
    first_seen: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the device was first observed",
    )
    last_seen: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the device was last observed",
    )
    source: str = Field(
        ...,
        description="How the device was discovered: 'passive_capture', 'arp_discovery', or 'manual'",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata about the device",
    )

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to a dict suitable for MongoDB insertion."""
        return self.model_dump()

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "DeviceDocument":
        """Construct a DeviceDocument from a MongoDB document."""
        data.pop("_id", None)
        return cls(**data)

