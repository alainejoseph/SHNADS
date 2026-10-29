"""Shared test fixtures and configuration."""

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings
from app.db.mongodb import mongodb_manager
from app.services.capture_service import CaptureService


# ---------------------------------------------------------------------------
# Test settings
# ---------------------------------------------------------------------------

TEST_MONGODB_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "smart_home_anomaly_test"


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Provide a clean test database and drop it after the test.

    Attempts to connect to a running MongoDB server; if none is available,
    falls back cleanly to an in-memory mongomock_motor database.
    """
    is_mock = False
    try:
        real_client: AsyncIOMotorClient = AsyncIOMotorClient(
            TEST_MONGODB_URL, serverSelectionTimeoutMS=500
        )
        await real_client.admin.command("ping")
        db = real_client[TEST_DB_NAME]
        client = real_client
    except Exception:
        from mongomock_motor import AsyncMongoMockClient

        mock_client = AsyncMongoMockClient()
        db = mock_client[TEST_DB_NAME]
        client = mock_client
        is_mock = True

    # Clean collections before the test
    collections = await db.list_collection_names()
    for col_name in collections:
        await db[col_name].delete_many({})

    yield db

    # Clean up after test
    if not is_mock:
        await client.drop_database(TEST_DB_NAME)
    client.close()


# ---------------------------------------------------------------------------
# Application fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def client(test_db: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the test app.

    The test app is configured with a test database and a mock
    CaptureService that does not need real network interfaces.
    """
    # Patch settings so the app uses the test DB.
    test_settings = Settings(
        MONGODB_URL=TEST_MONGODB_URL,
        MONGODB_DB_NAME=TEST_DB_NAME,
        CORS_ORIGINS=["*"],
        CAPTURE_INTERFACES_ALLOWED=[],
    )

    with patch("app.config.get_settings", return_value=test_settings), \
         patch("app.db.mongodb.get_settings", return_value=test_settings), \
         patch("app.db.indexes.create_indexes", new_callable=AsyncMock), \
         patch.object(mongodb_manager, "connect", new_callable=AsyncMock), \
         patch.object(mongodb_manager, "disconnect", new_callable=AsyncMock):

        from app.main import create_app

        app = create_app()

        # Override the database dependency so routes use the test DB.
        async def override_get_database() -> AsyncIOMotorDatabase:
            return test_db

        from app.db.mongodb import get_database

        app.dependency_overrides[get_database] = override_get_database

        # Manually set the capture service on app state before tests run.
        capture_service = CaptureService(test_db)
        app.state.capture_service = capture_service

        # Patch the mongodb_manager so the health endpoint works.
        with patch.object(
            mongodb_manager, "is_connected", new_callable=AsyncMock, return_value=True
        ):
            transport = ASGITransport(app=app)  # type: ignore[arg-type]
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                yield ac
