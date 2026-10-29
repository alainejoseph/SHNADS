"""Create MongoDB indexes on application startup."""

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

logger = logging.getLogger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create all required indexes for the application collections.

    This function is idempotent — calling it multiple times will not
    duplicate indexes.

    Args:
        db: The Motor database instance.
    """
    logger.info("Creating database indexes …")

    # ----- devices -----
    devices = db["devices"]
    await devices.create_indexes(
        [
            IndexModel([("device_key", ASCENDING)], unique=True),
            IndexModel([("last_seen", DESCENDING)]),
        ]
    )
    logger.info("Indexes created for 'devices' collection.")

    # ----- flows -----
    flows = db["flows"]
    await flows.create_indexes(
        [
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("capture_session_id", ASCENDING)]),
            IndexModel([("src_ip", ASCENDING), ("dst_ip", ASCENDING)]),
        ]
    )
    logger.info("Indexes created for 'flows' collection.")

    # ----- capture_sessions -----
    sessions = db["capture_sessions"]
    await sessions.create_indexes(
        [
            IndexModel([("started_at", DESCENDING)]),
            IndexModel([("status", ASCENDING)]),
        ]
    )
    logger.info("Indexes created for 'capture_sessions' collection.")

    # ----- alerts -----
    alerts = db["alerts"]
    await alerts.create_indexes(
        [
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("severity", ASCENDING)]),
        ]
    )
    logger.info("Indexes created for 'alerts' collection.")

    logger.info("All database indexes created successfully.")

