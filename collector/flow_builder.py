"""
Flow aggregation engine.

Groups individual packet metadata dicts into bidirectional
:class:`FlowRecord` objects keyed by the 5-tuple
``(src_ip, dst_ip, src_port, dst_port, protocol)``.

Flows are completed on idle timeout, maximum duration, TCP
termination, or a per-flow packet limit.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from collector.utils import format_tcp_flags

logger = logging.getLogger(__name__)

# TCP flags that signal connection termination.
_TCP_TERMINATION_FLAGS: frozenset[str] = frozenset({"FIN", "FIN-ACK", "RST"})


# ---------------------------------------------------------------------------
# FlowRecord
# ---------------------------------------------------------------------------

@dataclass
class FlowRecord:
    """A single aggregated network flow."""

    flow_key: str = ""
    src_ip: str = ""
    dst_ip: str = ""
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: str = ""
    packet_count: int = 0
    byte_count: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    duration_seconds: float = 0.0
    tcp_flags: list[str] = field(default_factory=list)
    tcp_flags_summary: Optional[str] = None
    interface: str = ""
    capture_session_id: str = ""

    # -- mutators -----------------------------------------------------------

    def update(self, packet_meta: dict) -> None:
        """Incorporate a new packet into this flow.

        Args:
            packet_meta: Packet metadata dict as produced by
                :meth:`PacketCapture._extract_packet_metadata`.
        """
        self.packet_count += 1
        self.byte_count += packet_meta.get("length", 0)

        ts = packet_meta.get("timestamp", time.time())
        if self.start_time == 0.0:
            self.start_time = ts
        self.end_time = ts

        tcp_flag = packet_meta.get("tcp_flags")
        if tcp_flag and tcp_flag not in self.tcp_flags:
            self.tcp_flags.append(tcp_flag)

    def finalize(self) -> None:
        """Calculate derived values when the flow is completed."""
        if self.end_time and self.start_time:
            self.duration_seconds = max(0.0, self.end_time - self.start_time)
        if self.tcp_flags:
            self.tcp_flags_summary = format_tcp_flags(self.tcp_flags)

    # -- serialisation ------------------------------------------------------

    def to_dict(self) -> dict:
        """Convert to a plain dict suitable for MongoDB storage."""
        ts = self.end_time if self.end_time else (self.start_time if self.start_time else time.time())
        return {
            "timestamp": ts,
            "flow_key": self.flow_key,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
            "packet_count": self.packet_count,
            "byte_count": self.byte_count,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "tcp_flags": list(self.tcp_flags),
            "tcp_flags_summary": self.tcp_flags_summary,
            "interface": self.interface,
            "capture_session_id": self.capture_session_id,
        }


# ---------------------------------------------------------------------------
# FlowBuilder
# ---------------------------------------------------------------------------

class FlowBuilder:
    """Aggregates packet metadata dicts into :class:`FlowRecord` objects.

    All public methods are **thread-safe**.

    Configuration is supplied at construction time:

    Args:
        idle_timeout: Seconds of inactivity before a flow is completed.
        max_duration: Maximum flow lifetime in seconds.
        max_active_flows: Upper bound on simultaneously tracked flows.
        max_packets_per_flow: Per-flow packet limit.
    """

    # Class-level defaults (documentation / reference).
    IDLE_TIMEOUT: float = 30.0
    MAX_FLOW_DURATION: float = 120.0
    MAX_ACTIVE_FLOWS: int = 50_000
    MAX_PACKETS_PER_FLOW: int = 10_000

    def __init__(
        self,
        idle_timeout: float = 30.0,
        max_duration: float = 120.0,
        max_active_flows: int = 50_000,
        max_packets_per_flow: int = 10_000,
    ) -> None:
        self._idle_timeout = idle_timeout
        self._max_duration = max_duration
        self._max_active_flows = max_active_flows
        self._max_packets_per_flow = max_packets_per_flow

        self._active_flows: dict[str, FlowRecord] = {}
        self._completed_flows: list[FlowRecord] = []
        self._lock: threading.Lock = threading.Lock()

        self._session_id: str = uuid.uuid4().hex[:12]

    # -- public API ---------------------------------------------------------

    def process_packet(self, packet_meta: dict) -> Optional[FlowRecord]:
        """Process a single packet and update or create its flow.

        Returns the :class:`FlowRecord` if this packet triggered flow
        completion, otherwise ``None``.
        """
        key = self._make_flow_key(packet_meta)

        with self._lock:
            flow = self._active_flows.get(key)

            if flow is None:
                # Enforce max-active-flows limit.
                if len(self._active_flows) >= self._max_active_flows:
                    logger.warning(
                        "Max active flows (%d) reached — dropping packet",
                        self._max_active_flows,
                    )
                    return None

                flow = self._create_flow(key, packet_meta)
                self._active_flows[key] = flow

            flow.update(packet_meta)

            # Check completion criteria.
            if self._is_complete(flow, packet_meta):
                return self._complete_flow(key, flow)

        return None

    def get_completed_flows(self) -> list[FlowRecord]:
        """Retrieve and clear the completed-flow buffer.

        Returns:
            A list of :class:`FlowRecord` objects that have been finalised
            since the last call.
        """
        with self._lock:
            flows = self._completed_flows
            self._completed_flows = []
            return flows

    def flush(self) -> list[FlowRecord]:
        """Force-complete **all** active flows and return them.

        Typically called when packet capture stops.
        """
        with self._lock:
            flushed: list[FlowRecord] = []
            for _key, flow in self._active_flows.items():
                flow.finalize()
                flushed.append(flow)
            self._active_flows.clear()

            # Also drain anything already in the completed buffer.
            flushed.extend(self._completed_flows)
            self._completed_flows = []

            return flushed

    def check_timeouts(self, now: Optional[float] = None) -> list[FlowRecord]:
        """Expire flows that have timed out (idle or max-duration).

        Should be called periodically (e.g. every few seconds).

        Args:
            now: Optional current timestamp (for testing/deterministic replay).

        Returns:
            Newly completed flows.
        """
        if now is None:
            now = time.time()
        completed: list[FlowRecord] = []

        with self._lock:
            keys_to_remove: list[str] = []
            for key, flow in self._active_flows.items():
                idle = now - flow.end_time if flow.end_time else now - flow.start_time
                age = now - flow.start_time if flow.start_time else 0.0

                if idle >= self._idle_timeout or age >= self._max_duration:
                    flow.finalize()
                    completed.append(flow)
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._active_flows[key]

            self._completed_flows.extend(completed)

        return completed

    # -- properties ---------------------------------------------------------

    @property
    def active_flow_count(self) -> int:
        """Number of currently active flows."""
        with self._lock:
            return len(self._active_flows)

    @property
    def stats(self) -> dict:
        """Snapshot of flow-builder statistics."""
        with self._lock:
            return {
                "active_flows": len(self._active_flows),
                "completed_flows_pending": len(self._completed_flows),
                "session_id": self._session_id,
                "idle_timeout": self._idle_timeout,
                "max_duration": self._max_duration,
                "max_active_flows": self._max_active_flows,
                "max_packets_per_flow": self._max_packets_per_flow,
            }

    # -- internals ----------------------------------------------------------

    def _make_flow_key(self, packet_meta: dict) -> str:
        """Generate a canonical bidirectional flow key.

        The two endpoints are sorted so that packets in either direction
        produce the same key.
        """
        src_ip = packet_meta.get("src_ip", "")
        dst_ip = packet_meta.get("dst_ip", "")
        src_port = packet_meta.get("src_port")
        dst_port = packet_meta.get("dst_port")
        protocol = packet_meta.get("protocol", "Other")

        # Normalise port values for protocols without ports.
        src_port_str = str(src_port) if src_port is not None else "0"
        dst_port_str = str(dst_port) if dst_port is not None else "0"

        ep_a = (src_ip, src_port_str)
        ep_b = (dst_ip, dst_port_str)

        # Sort to make the key direction-independent.
        if ep_a > ep_b:
            ep_a, ep_b = ep_b, ep_a

        return f"{ep_a[0]}:{ep_a[1]}-{ep_b[0]}:{ep_b[1]}-{protocol}"

    def _classify_protocol(self, packet_meta: dict) -> str:
        protocol = (packet_meta.get("protocol") or "").upper()
        src_port = packet_meta.get("src_port")
        dst_port = packet_meta.get("dst_port")
        try:
            sp = int(src_port) if src_port is not None else None
            dp = int(dst_port) if dst_port is not None else None
        except Exception:
            sp, dp = None, None
        # Classify HTTP/HTTPS if TCP
        if protocol in ("TCP",):
            if sp == 443 or dp == 443:
                return "HTTPS"
            if sp == 80 or dp == 80:
                return "HTTP"
        return protocol or "Other"

    def _create_flow(self, key: str, packet_meta: dict) -> FlowRecord:
        """Instantiate a new :class:`FlowRecord` from the first packet."""
        return FlowRecord(
            flow_key=key,
            src_ip=packet_meta.get("src_ip", ""),
            dst_ip=packet_meta.get("dst_ip", ""),
            src_port=packet_meta.get("src_port"),
            dst_port=packet_meta.get("dst_port"),
            protocol=self._classify_protocol(packet_meta),
            interface=packet_meta.get("interface", ""),
            capture_session_id=self._session_id,
        )

    def _is_complete(self, flow: FlowRecord, packet_meta: dict) -> bool:
        """Determine whether *flow* should be completed now."""
        # 1. Packet-count limit
        if flow.packet_count >= self._max_packets_per_flow:
            return True

        # 2. TCP termination (FIN / RST)
        tcp_flag = packet_meta.get("tcp_flags")
        if tcp_flag and tcp_flag in _TCP_TERMINATION_FLAGS:
            return True

        # 3. Max duration
        if flow.start_time and (flow.end_time - flow.start_time) >= self._max_duration:
            return True

        return False

    def _complete_flow(self, key: str, flow: FlowRecord) -> FlowRecord:
        """Finalise and move a flow from active to completed.

        Caller must hold ``self._lock``.
        """
        flow.finalize()
        del self._active_flows[key]
        self._completed_flows.append(flow)
        return flow
