"""Alert MongoDB document model (reserved for future anomaly detection)."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AlertDocument(BaseModel):
    """Represents a network anomaly alert.

    In this milestone all alerts are test fixtures (``is_test_fixture=True``).
    Future milestones will populate real alerts from the anomaly detection
    engine.
    """

    alert_id: str = Field(..., description="Unique identifier for this alert")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the alert was generated",
    )
    device_key: Optional[str] = Field(
        default=None,
        description="Device key the alert is associated with, if any",
    )
    alert_type: str = Field(
        ..., description="Category of the alert, e.g. 'port_scan', 'new_device'"
    )
    severity: str = Field(
        ..., description="Severity level: 'info', 'warning', or 'critical'"
    )
    message: str = Field(..., description="Human-readable alert description")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured details about the alert",
    )
    is_test_fixture: bool = Field(
        default=True,
        description="Whether this alert is a test fixture (always True in this milestone)",
    )

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to a dict suitable for MongoDB insertion."""
        return self.model_dump()

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "AlertDocument":
        """Construct an AlertDocument from a MongoDB document."""
        data.pop("_id", None)
        return cls(**data)

