"""CaptureSession MongoDB document model."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CaptureSessionDocument(BaseModel):
    """Represents a packet capture session.

    Tracks the lifecycle of a capture — from start to stop — including
    running counters for packets and flows.
    """

    session_id: str = Field(..., description="Unique UUID for this session")
    interface: str = Field(
        ..., description="Network interface being captured"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the capture was started",
    )
    stopped_at: Optional[datetime] = Field(
        default=None, description="When the capture was stopped"
    )
    status: str = Field(
        default="starting",
        description="Current status: 'starting', 'running', 'stopping', 'stopped', 'error'",
    )
    packets_seen: int = Field(
        default=0, description="Total packets observed so far"
    )
    flows_created: int = Field(
        default=0, description="Total flows created so far"
    )
    last_error: Optional[str] = Field(
        default=None, description="Last error message, if any"
    )

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to a dict suitable for MongoDB insertion."""
        return self.model_dump()

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "CaptureSessionDocument":
        """Construct a CaptureSessionDocument from a MongoDB document."""
        data.pop("_id", None)
        return cls(**data)

