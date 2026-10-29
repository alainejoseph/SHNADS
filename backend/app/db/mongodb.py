"""MongoDB connection manager using Motor async driver."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages the MongoDB connection lifecycle.

    This class provides a singleton-like connection manager that handles
    connecting and disconnecting from MongoDB, and exposes the database
    instance for use throughout the application.
    """

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    @property
    def client(self) -> Optional[AsyncIOMotorClient]:
        """Return the current Motor client instance."""
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Return the database instance.

        Raises:
            RuntimeError: If the database connection has not been established.
        """
        if self._database is None:
            raise RuntimeError(
                "Database not initialised. Call connect() first."
            )
        return self._database

    async def connect(self) -> None:
        """Establish a connection to MongoDB.

        Reads connection parameters from the application settings and creates
        a Motor client.  Pings the server to verify connectivity.
        """
        settings = get_settings()
        logger.info("Connecting to MongoDB at %s …", settings.MONGODB_URL)

        self._client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
        )

        # Verify the connection is alive.
        try:
            await self._client.admin.command("ping")
            logger.info("MongoDB connection established successfully.")
        except Exception as exc:
            logger.error("Failed to connect to MongoDB: %s", exc)
            self._client = None
            raise

        self._database = self._client[settings.MONGODB_DB_NAME]

    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed.")

    async def is_connected(self) -> bool:
        """Check whether the database connection is alive.

        Returns:
            True if the connection is healthy, False otherwise.
        """
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False


# Module-level singleton used across the application.
mongodb_manager = MongoDBManager()


async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency that provides the database instance.

    Returns:
        The Motor database object for the configured database name.
    """
    return mongodb_manager.database

