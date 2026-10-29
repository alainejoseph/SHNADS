"""Flow MongoDB document model."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class FlowDocument(BaseModel):
    """Represents a network flow — an aggregation of related packets.

    Each flow is associated with a capture session and records basic
    5-tuple information along with traffic statistics.
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp marking the start of the flow",
    )
    src_ip: str = Field(..., description="Source IP address")
    dst_ip: str = Field(..., description="Destination IP address")
    src_port: Optional[int] = Field(
        default=None, description="Source port (if applicable)"
    )
    dst_port: Optional[int] = Field(
        default=None, description="Destination port (if applicable)"
    )
    protocol: str = Field(
        ..., description="Protocol name, e.g. 'TCP', 'UDP', 'ICMP'"
    )
    packet_count: int = Field(
        default=1, description="Number of packets in this flow"
    )
    byte_count: int = Field(
        default=0, description="Total bytes transferred in this flow"
    )
    duration_seconds: float = Field(
        default=0.0, description="Duration of the flow in seconds"
    )
    tcp_flags_summary: Optional[str] = Field(
        default=None, description="Summary of TCP flags seen, e.g. 'SYN,ACK'"
    )
    interface: str = Field(
        ..., description="Network interface the flow was captured on"
    )
    capture_session_id: str = Field(
        ..., description="ID of the capture session this flow belongs to"
    )

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to a dict suitable for MongoDB insertion."""
        return self.model_dump()

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "FlowDocument":
        """Construct a FlowDocument from a MongoDB document."""
        data.pop("_id", None)
        return cls(**data)

