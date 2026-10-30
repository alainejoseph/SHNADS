"""Capture service — manages the packet capture lifecycle.

This service orchestrates starting/stopping captures, creating session
documents, and coordinating with the collector module (built separately
under ``/home/alain/programing/project/collector/``).
"""

import asyncio
import inspect
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psutil
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.services.device_service import DeviceService
from app.services.flow_service import FlowService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import the collector module.  If it is not available yet we
# provide lightweight stubs so the backend can start independently.
# ---------------------------------------------------------------------------
try:
    from collector.capture import PacketCapture
    from collector.flow_builder import FlowBuilder

    _COLLECTOR_AVAILABLE = True
except ImportError:
    _COLLECTOR_AVAILABLE = False
    logger.warning(
        "Collector module not available. Capture functionality will be "
        "limited until the collector package is installed."
    )

    class PacketCapture:  # type: ignore[no-redef]
        """Stub PacketCapture used when the collector module is absent."""

        def __init__(self) -> None:
            self._running = False
            self.stats: Dict[str, int] = {"packets": 0, "bytes": 0}

        async def start(self, interface: str, callback: Any = None) -> None:
            """Stub start — marks capture as running."""
            self._running = True

        async def stop(self) -> None:
            """Stub stop — marks capture as stopped."""
            self._running = False

        @property
        def is_running(self) -> bool:
            return self._running

    class FlowBuilder:  # type: ignore[no-redef]
        """Stub FlowBuilder used when the collector module is absent."""

        def process_packet(self, packet_meta: Dict[str, Any]) -> None:
            """No-op."""

        def get_completed_flows(self) -> List[Dict[str, Any]]:
            """Return an empty list."""
            return []

        def flush(self) -> List[Dict[str, Any]]:
            """Return an empty list."""
            return []


class CaptureService:
    """Singleton-style service that manages the packet capture lifecycle.

    Only one capture session may be active at any given time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._sessions = db["capture_sessions"]
        self._device_service = DeviceService(db)
        self._flow_service = FlowService(db)
        self._capture: Optional[PacketCapture] = None
        self._flow_builder: Optional[FlowBuilder] = None
        self._current_session: Optional[Dict[str, Any]] = None
        self._flush_task: Optional[asyncio.Task[None]] = None

    # ----- public properties ------------------------------------------------

    @property
    def is_running(self) -> bool:
        """Return whether a capture is currently active."""
        return self._current_session is not None and self._current_session.get("status") in (
            "starting",
            "running",
        )

    @property
    def current_session(self) -> Optional[Dict[str, Any]]:
        """Return the current session document (if any)."""
        return self._current_session

    # ----- lifecycle --------------------------------------------------------

    async def start_capture(self, interface: str) -> Dict[str, Any]:
        """Start a new packet capture session.

        Args:
            interface: The network interface to capture on.

        Returns:
            The newly created session document.

        Raises:
            ValueError: If a capture is already running or the interface
                is not valid/allowed.
        """
        if self.is_running:
            raise ValueError("A capture session is already running.")

        # Validate interface
        self._validate_interface(interface)

        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        session: Dict[str, Any] = {
            "session_id": session_id,
            "interface": interface,
            "started_at": now,
            "stopped_at": None,
            "status": "starting",
            "packets_seen": 0,
            "flows_created": 0,
            "last_error": None,
        }

        await self._sessions.insert_one(session.copy())
        # Remove the MongoDB-generated _id
        session.pop("_id", None)
        self._current_session = session

        # Initialise capture & flow builder
        self._capture = PacketCapture()
        self._flow_builder = FlowBuilder()

        try:
            if _COLLECTOR_AVAILABLE:
                res = self._capture.start(interface, callback=self._on_packet)
            else:
                res = self._capture.start(interface)
            if inspect.isawaitable(res):
                await res

            session["status"] = "running"
            self._current_session = session
            await self._sessions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "running"}},
            )

            # Start background flow-flushing task
            self._flush_task = asyncio.create_task(
                self._periodic_flush(session_id)
            )

            logger.info("Capture started on %s (session %s).", interface, session_id)
        except Exception as exc:
            session["status"] = "error"
            session["last_error"] = str(exc)
            self._current_session = session
            await self._sessions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "error", "last_error": str(exc)}},
            )
            logger.error("Failed to start capture: %s", exc)
            raise

        return session

    async def stop_capture(self) -> Dict[str, Any]:
        """Stop the currently running capture session.

        Returns:
            The finalised session document.

        Raises:
            ValueError: If no capture session is running.
        """
        if not self.is_running or self._current_session is None:
            raise ValueError("No capture session is currently running.")

        session_id = self._current_session["session_id"]

        # Cancel the flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Stop the capture engine
        if self._capture is not None:
            try:
                res = self._capture.stop()
                if inspect.isawaitable(res):
                    await res
            except Exception as exc:
                logger.error("Error stopping capture engine: %s", exc)

        # Final flush
        if self._flow_builder is not None:
            await self._flush_flows(session_id, is_final=True)

        now = datetime.utcnow()
        self._current_session["status"] = "stopped"
        self._current_session["stopped_at"] = now

        await self._sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": "stopped",
                    "stopped_at": now,
                    "packets_seen": self._current_session.get("packets_seen", 0),
                    "flows_created": self._current_session.get("flows_created", 0),
                }
            },
        )

        final_session = dict(self._current_session)
        self._current_session = None
        self._capture = None
        self._flow_builder = None

        logger.info("Capture stopped (session %s).", session_id)
        return final_session

    async def get_status(self) -> Dict[str, Any]:
        """Return the current capture status."""
        session_copy = dict(self._current_session) if self._current_session else None
        if session_copy and self._capture:
            stats = getattr(self._capture, "stats", None)
            if stats is not None:
                # Handle both CaptureStats dataclass and plain dict (stub)
                if hasattr(stats, "packets_captured"):
                    packets = stats.packets_captured
                elif isinstance(stats, dict):
                    packets = stats.get("packets_captured", stats.get("packets", 0))
                else:
                    packets = 0
                session_copy["packets_seen"] = max(
                    session_copy.get("packets_seen", 0), packets
                )
        return {
            "is_running": self.is_running,
            "current_session": session_copy,
        }

    async def list_sessions(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List capture sessions with pagination.

        Args:
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            A tuple of (list of session dicts, total count).
        """
        total = await self._sessions.count_documents({})
        cursor = (
            self._sessions.find({}, {"_id": 0})
            .sort("started_at", -1)
            .skip(skip)
            .limit(limit)
        )
        sessions = await cursor.to_list(length=limit)
        return sessions, total

    # ----- internal helpers -------------------------------------------------

    def _validate_interface(self, interface: str) -> None:
        """Ensure the requested interface exists and is allowed.

        Raises:
            ValueError: If the interface is unknown or not allowed.
        """
        available = self._get_available_interfaces()
        if interface not in available:
            raise ValueError(
                f"Interface '{interface}' is not available. "
                f"Available interfaces: {', '.join(available)}"
            )

        settings = get_settings()
        if settings.CAPTURE_INTERFACES_ALLOWED:
            if interface not in settings.CAPTURE_INTERFACES_ALLOWED:
                raise ValueError(
                    f"Interface '{interface}' is not in the allowed list: "
                    f"{', '.join(settings.CAPTURE_INTERFACES_ALLOWED)}"
                )

    @staticmethod
    def _get_available_interfaces() -> List[str]:
        """Return a list of network interface names on this system."""
        interfaces = list(psutil.net_if_addrs().keys())
        if "demo" not in interfaces:
            interfaces.insert(0, "demo")
        return interfaces

    @staticmethod
    def get_interface_details() -> List[Dict[str, Any]]:
        """Return detailed information for available network interfaces."""
        details = [
            {
                "name": "demo",
                "addresses": ["192.168.1.0/24"],
                "mac_address": "AA:BB:CC:DD:EE:00",
                "is_up": True,
                "is_loopback": False,
                "description": "Demo IoT Traffic Simulator (No root required)",
            }
        ]
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for name, snic_list in addrs.items():
                if name == "demo":
                    continue
                ip_list = []
                mac = None
                for snic in snic_list:
                    family_name = getattr(snic.family, "name", str(snic.family))
                    if "INET" in family_name:
                        ip_list.append(snic.address)
                    elif "PACKET" in family_name or "LINK" in family_name:
                        mac = snic.address
                stat = stats.get(name)
                is_up = stat.isup if stat else True
                is_loop = (
                    name == "lo"
                    or name.startswith("loopback")
                    or any(ip.startswith("127.") for ip in ip_list)
                )
                details.append({
                    "name": name,
                    "addresses": ip_list,
                    "mac_address": mac,
                    "is_up": is_up,
                    "is_loopback": is_loop,
                    "description": f"{name} ({'UP' if is_up else 'DOWN'})",
                })
        except Exception as exc:
            logger.error("Failed to query interface details: %s", exc)
        return details

    def _on_packet(self, packet_meta: Dict[str, Any]) -> None:
        """Callback invoked by the collector for each captured packet.

        This feeds the packet metadata into the FlowBuilder and
        updates the running packet counter.
        """
        if self._flow_builder is not None:
            self._flow_builder.process_packet(packet_meta)
        if self._current_session is not None:
            self._current_session["packets_seen"] = (
                self._current_session.get("packets_seen", 0) + 1
            )

    async def _flush_flows(self, session_id: str, is_final: bool = False) -> None:
        """Flush completed flows from the FlowBuilder into MongoDB.

        Args:
            session_id: The current capture session identifier.
            is_final: When True, calls ``flush()`` to drain all active flows.
                      When False, calls ``get_completed_flows()`` for only
                      timed-out / finished flows.
        """
        if self._flow_builder is None:
            return

        if is_final:
            completed = self._flow_builder.flush()
        else:
            completed = self._flow_builder.get_completed_flows()

        if not completed:
            return

        # Convert FlowRecord dataclasses (or plain dicts) to plain dicts and
        # annotate with session info before persisting.
        flow_dicts: List[Dict[str, Any]] = []
        for flow in completed:
            if hasattr(flow, "to_dict"):
                fd: Dict[str, Any] = flow.to_dict()
            elif isinstance(flow, dict):
                fd = dict(flow)
            else:
                logger.warning("Unexpected flow type %s — skipping.", type(flow))
                continue
            fd["capture_session_id"] = session_id
            if self._current_session:
                fd.setdefault("interface", self._current_session.get("interface", ""))
            flow_dicts.append(fd)

        if not flow_dicts:
            return

        count = await self._flow_service.store_flows(flow_dicts)

        if self._current_session is not None:
            self._current_session["flows_created"] = (
                self._current_session.get("flows_created", 0) + count
            )
            await self._sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "flows_created": self._current_session["flows_created"],
                        "packets_seen": self._current_session.get("packets_seen", 0),
                    }
                },
            )

        # Upsert devices observed in the flushed flows - only local/monitored network devices
        from app.utils.network import get_local_networks, is_ip_in_monitored_network
        try:
            networks = get_local_networks(self._current_session.get("interface") if self._current_session else None)
            seen_ips: set[str] = set()
            for fd in flow_dicts:
                seen_ips.add(fd.get("src_ip", ""))
                seen_ips.add(fd.get("dst_ip", ""))
            for ip in seen_ips:
                if ip and is_ip_in_monitored_network(ip, networks):
                    await self._device_service.upsert_device(
                        ip=ip, mac=None, source="passive_capture"
                    )
        except Exception as exc:
            logger.error("Error upserting devices from flows: %s", exc)

    async def _periodic_flush(self, session_id: str) -> None:
        """Background task that flushes completed flows every 10 seconds."""
        try:
            while True:
                await asyncio.sleep(10)
                await self._flush_flows(session_id, is_final=False)
        except asyncio.CancelledError:
            pass

    async def force_stop(self) -> None:
        """Forcefully stop any running capture (used during shutdown)."""
        if self.is_running:
            try:
                await self.stop_capture()
            except Exception as exc:
                logger.error("Error force-stopping capture: %s", exc)

