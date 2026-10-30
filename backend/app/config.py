"""Application configuration loaded from environment variables."""

from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "smart_home_anomaly"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Capture
    CAPTURE_INTERFACES_ALLOWED: List[str] = []

    # Discovery
    DISCOVERY_SUBNET: str = ""
    ARP_TIMEOUT: float = 5
    ARP_RETRIES: int = 2
    ARP_INTER_RETRY_DELAY: float = 1
    DISCOVERY_MAX_DURATION: float = 30

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v  # type: ignore[return-value]

    @field_validator("CAPTURE_INTERFACES_ALLOWED", mode="before")
    @classmethod
    def parse_interfaces(cls, v: object) -> List[str]:
        """Parse allowed interfaces from comma-separated string or list."""
        if isinstance(v, str):
            return [iface.strip() for iface in v.split(",") if iface.strip()]
        return v  # type: ignore[return-value]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

