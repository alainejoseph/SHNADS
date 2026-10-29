"""Capture management routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_capture_service
from app.schemas.capture import (
    CaptureSessionListResponse,
    CaptureSessionResponse,
    CaptureStartRequest,
    CaptureStatusResponse,
)
from app.services.capture_service import CaptureService

router = APIRouter(prefix="/api/capture", tags=["capture"])


@router.get("/status", response_model=CaptureStatusResponse)
async def capture_status(
    service: CaptureService = Depends(get_capture_service),
) -> CaptureStatusResponse:
    """Return the current capture engine status."""
    status = await service.get_status()
    current = status.get("current_session")
    interfaces = service.get_interface_details()
    return CaptureStatusResponse(
        is_running=status["is_running"],
        current_session=CaptureSessionResponse(**current) if current else None,
        available_interfaces=interfaces,
    )


@router.post("/start", response_model=CaptureSessionResponse)
async def start_capture(
    body: CaptureStartRequest,
    service: CaptureService = Depends(get_capture_service),
) -> CaptureSessionResponse:
    """Start a new packet capture session.

    Returns a 409 Conflict if a capture is already running, or a 400 if
    the requested interface is invalid or not allowed.
    """
    try:
        session = await service.start_capture(body.interface)
    except ValueError as exc:
        error_msg = str(exc)
        if "already running" in error_msg.lower():
            raise HTTPException(
                status_code=409,
                detail={"detail": error_msg, "error_code": "CAPTURE_ALREADY_RUNNING"},
            )
        raise HTTPException(
            status_code=400,
            detail={"detail": error_msg, "error_code": "INVALID_INTERFACE"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"detail": str(exc), "error_code": "CAPTURE_START_FAILED"},
        )

    return CaptureSessionResponse(**session)


@router.post("/stop", response_model=CaptureSessionResponse)
async def stop_capture(
    service: CaptureService = Depends(get_capture_service),
) -> CaptureSessionResponse:
    """Stop the currently running capture session.

    Returns a 409 Conflict if no capture is running.
    """
    try:
        session = await service.stop_capture()
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={"detail": str(exc), "error_code": "NO_ACTIVE_CAPTURE"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"detail": str(exc), "error_code": "CAPTURE_STOP_FAILED"},
        )

    return CaptureSessionResponse(**session)


@router.get("/sessions", response_model=CaptureSessionListResponse)
async def list_sessions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    service: CaptureService = Depends(get_capture_service),
) -> CaptureSessionListResponse:
    """List recent capture sessions with pagination."""
    sessions, total = await service.list_sessions(skip=skip, limit=limit)
    return CaptureSessionListResponse(
        sessions=[CaptureSessionResponse(**s) for s in sessions],
        total=total,
        skip=skip,
        limit=limit,
    )

