"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import capture, dashboard, devices, discovery, flows, health
from app.config import get_settings
from app.db.indexes import create_indexes
from app.db.mongodb import get_database, mongodb_manager
from app.services.capture_service import CaptureService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await mongodb_manager.connect()
    try:
        await create_indexes()
    except Exception as exc:
        logger.warning("Failed to create indexes: %s", exc)
    try:
        db = await get_database()
        app.state.capture_service = CaptureService(db)
    except Exception as exc:
        logger.warning("Failed to initialize capture service: %s", exc)
    yield
    try:
        capture_svc = getattr(app.state, "capture_service", None)
        if capture_svc is not None:
            try:
                if getattr(capture_svc, "is_running", None) and capture_svc.is_running():
                    await capture_svc.stop_capture()
            except Exception:
                pass
    except Exception:
        pass
    try:
        await mongodb_manager.disconnect()
    except Exception as exc:
        logger.warning("Failed to disconnect from MongoDB: %s", exc)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart Home Network Anomaly Detection",
        version="0.1.0",
        description="Smart Home IoT Network Anomaly Detection - API",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(dashboard.router)
    app.include_router(devices.router)
    app.include_router(discovery.router)
    app.include_router(flows.router)
    app.include_router(capture.router)

    @app.get("/")
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": "Smart Home Network Anomaly Detection API",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
        }

    return app


app = create_app()
