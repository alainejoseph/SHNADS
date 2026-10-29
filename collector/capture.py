"""
Packet capture service using Scapy.

Provides :class:`PacketCapture` which runs Scapy's ``AsyncSniffer`` in a
background thread, extracts packet metadata (no payloads), and delivers
it to registered callbacks.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scapy import — deferred so the rest of the module can still be imported and
# tested even when Scapy is not installed.
# ---------------------------------------------------------------------------
try:
    from scapy.all import (  # type: ignore[import-untyped]
        ARP,
        Ether,
        ICMP,
        IP,
        TCP,
        UDP,
        AsyncSniffer,
        conf as scapy_conf,
    )

    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CaptureStats:
    """Running statistics for a packet capture session."""

    packets_captured: int = 0
    packets_dropped: int = 0
    bytes_captured: int = 0
    errors: int = 0
    start_time: Optional[float] = None
    last_packet_time: Optional[float] = None
    protocols: dict[str, int] = field(default_factory=dict)

    def record_packet(self, length: int, protocol: str) -> None:
        """Update counters after a successfully parsed packet."""
        self.packets_captured += 1
        self.bytes_captured += length
        self.last_packet_time = time.time()
        self.protocols[protocol] = self.protocols.get(protocol, 0) + 1

    def record_error(self) -> None:
        """Increment the error counter."""
        self.errors += 1

    def record_drop(self) -> None:
        """Increment the dropped-packet counter."""
        self.packets_dropped += 1

    def copy(self) -> "CaptureStats":
        """Return a snapshot copy."""
        return CaptureStats(
            packets_captured=self.packets_captured,
            packets_dropped=self.packets_dropped,
            bytes_captured=self.bytes_captured,
            errors=self.errors,
            start_time=self.start_time,
            last_packet_time=self.last_packet_time,
            protocols=dict(self.protocols),
        )


@dataclass
class InterfaceInfo:
    """Descriptive information about a network interface."""

    name: str
    addresses: list[str] = field(default_factory=list)
    mac_address: Optional[str] = None
    is_up: bool = False
    is_loopback: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# TCP flag helpers
# ---------------------------------------------------------------------------

_TCP_FLAG_MAP: dict[int, str] = {
    0x02: "SYN",
    0x12: "SYN-ACK",
    0x10: "ACK",
    0x01: "FIN",
    0x11: "FIN-ACK",
    0x04: "RST",
    0x08: "PSH",
    0x20: "URG",
}


def _decode_tcp_flags(flags_value: int) -> str:
    """Convert Scapy's integer flag field to a human-readable label."""
    label = _TCP_FLAG_MAP.get(flags_value)
    if label is not None:
        return label
    # Fall back to a generic hex representation for uncommon combos.
    parts: list[str] = []
    if flags_value & 0x20:
        parts.append("URG")
    if flags_value & 0x10:
        parts.append("ACK")
    if flags_value & 0x08:
        parts.append("PSH")
    if flags_value & 0x04:
        parts.append("RST")
    if flags_value & 0x02:
        parts.append("SYN")
    if flags_value & 0x01:
        parts.append("FIN")
    return "-".join(parts) if parts else f"0x{flags_value:02x}"


# ---------------------------------------------------------------------------
# PacketCapture
# ---------------------------------------------------------------------------

class PacketCapture:
    """Manages network packet capture using Scapy's ``AsyncSniffer``.

    Usage::

        cap = PacketCapture()
        cap.start("eth0", my_callback)
        ...
        stats = cap.stop()

    The *packet_callback* receives a ``dict`` of extracted metadata for
    every successfully parsed packet.  See
    :meth:`_extract_packet_metadata` for the dict schema.
    """

    # Timeout when joining the capture thread during stop().
    _THREAD_JOIN_TIMEOUT: float = 5.0

    def __init__(self) -> None:
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._sniffer: Optional[object] = None  # AsyncSniffer when Scapy loaded
        self._stats: CaptureStats = CaptureStats()
        self._callbacks: list[Callable[[dict], None]] = []
        self._interface: Optional[str] = None
        self._stop_event: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()
        self._last_error: Optional[str] = None

    # -- public interface ---------------------------------------------------

    @staticmethod
    def list_interfaces() -> list[InterfaceInfo]:
        """List available network interfaces with details.

        Includes physical/virtual interfaces and a dedicated 'demo' simulator interface.
        """
        demo_iface = InterfaceInfo(
            name="demo",
            addresses=["192.168.1.0/24"],
            is_up=True,
            is_loopback=False,
            description="Demo IoT traffic simulator (No root required)",
        )
        interfaces = _list_via_psutil()
        if interfaces is None:
            interfaces = _list_via_netifaces()
        if interfaces is None:
            interfaces = _list_via_socket()

        cleaned = [i for i in (interfaces or []) if i.name != "demo"]
        return [demo_iface] + cleaned

    @staticmethod
    def validate_interface(name: str) -> bool:
        """Return ``True`` if *name* refers to an existing, usable interface."""
        if name.lower() in ("demo", "virtual-iot-net", "simulated", "demo-iot-network"):
            return True
        try:
            socket.if_nametoindex(name)
            return True
        except (OSError, ValueError):
            return False

    def start(
        self,
        interface: str,
        packet_callback: Optional[Callable[[dict], None]] = None,
        callback: Optional[Callable[[dict], None]] = None,
    ) -> None:
        """Start capturing packets on *interface*.

        Args:
            interface: OS interface name (e.g. ``"eth0"``).
            packet_callback: Called with a metadata ``dict`` for each packet.
            callback: Alias for *packet_callback*.

        Raises:
            RuntimeError: If Scapy is not available, capture is already
                running, or the interface is invalid.
        """
        cb = packet_callback or callback
        if cb is None:
            raise ValueError("A packet callback must be provided to start()")
        self._packet_callback = cb
        if not SCAPY_AVAILABLE:
            raise RuntimeError(
                "Scapy is not installed. Install it with: pip install scapy"
            )

        with self._lock:
            if self._running:
                raise RuntimeError("Capture is already running")

            if not self.validate_interface(interface):
                raise RuntimeError(f"Interface {interface!r} is not available")

            self._interface = interface
            self._callbacks = [cb]
            self._stats = CaptureStats(start_time=time.time())
            self._stop_event.clear()
            self._running = True

        thread = threading.Thread(
            target=self._capture_thread,
            args=(interface,),
            name=f"PacketCapture-{interface}",
            daemon=True,
        )
        self._thread = thread
        self._last_error = None
        thread.start()
        logger.info("Capture started on interface %s", interface)

        # Allow the capture thread a brief moment to initialize and catch immediate raw socket errors
        time.sleep(0.2)
        if not self._running and self._last_error:
            raise RuntimeError(self._last_error)

    def stop(self) -> CaptureStats:
        """Stop the active capture and return final :class:`CaptureStats`.

        Blocks until the capture thread finishes (with a timeout).

        Returns:
            A *copy* of the final capture statistics.

        Raises:
            RuntimeError: If no capture is currently running.
        """
        with self._lock:
            if not self._running:
                raise RuntimeError("No capture is currently running")
            self._stop_event.set()

        # Ask the sniffer to stop.
        sniffer = self._sniffer
        if sniffer is not None:
            try:
                sniffer.stop()  # type: ignore[union-attr]
            except Exception:
                # Sniffer may already have stopped; that's fine.
                pass

        # Wait for the capture thread.
        thread = self._thread
        if thread is not None:
            thread.join(timeout=self._THREAD_JOIN_TIMEOUT)
            if thread.is_alive():
                logger.warning(
                    "Capture thread did not terminate within %.1f s",
                    self._THREAD_JOIN_TIMEOUT,
                )

        with self._lock:
            self._running = False
            self._sniffer = None
            self._thread = None
            final_stats = self._stats.copy()
            self._interface = None

        logger.info(
            "Capture stopped — %d packets, %d bytes, %d errors",
            final_stats.packets_captured,
            final_stats.bytes_captured,
            final_stats.errors,
        )
        return final_stats

    # -- properties ---------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """Whether capture is currently active."""
        return self._running

    @property
    def stats(self) -> CaptureStats:
        """Current capture statistics (snapshot copy)."""
        return self._stats.copy()

    @property
    def current_interface(self) -> Optional[str]:
        """The interface currently being captured on, or ``None``."""
        return self._interface

    # -- internals ----------------------------------------------------------

    def _extract_packet_metadata(self, packet: object) -> Optional[dict]:
        """Extract metadata from a Scapy packet object.

        Returns ``None`` for packets that cannot be meaningfully parsed
        (e.g. no IP / ARP layer).

        The returned dict contains:

        - ``timestamp`` – packet arrival time (``float``).
        - ``src_ip``, ``dst_ip`` – IP addresses as strings.
        - ``src_port``, ``dst_port`` – transport ports or ``None``.
        - ``protocol`` – ``"TCP"``, ``"UDP"``, ``"ICMP"``, ``"ARP"``, or ``"Other"``.
        - ``length`` – total packet length in bytes.
        - ``tcp_flags`` – human-readable flag string or ``None``.
        - ``src_mac``, ``dst_mac`` – MAC addresses or ``None``.
        """
        if not SCAPY_AVAILABLE:
            return None

        try:
            meta: dict = {
                "timestamp": float(packet.time),  # type: ignore[union-attr]
                "src_ip": None,
                "dst_ip": None,
                "src_port": None,
                "dst_port": None,
                "protocol": "Other",
                "length": len(packet),  # type: ignore[arg-type]
                "tcp_flags": None,
                "src_mac": None,
                "dst_mac": None,
            }

            # Ethernet MACs
            if packet.haslayer(Ether):  # type: ignore[union-attr]
                ether = packet[Ether]  # type: ignore[index]
                meta["src_mac"] = ether.src
                meta["dst_mac"] = ether.dst

            # ARP
            if packet.haslayer(ARP):  # type: ignore[union-attr]
                arp = packet[ARP]  # type: ignore[index]
                meta["src_ip"] = arp.psrc
                meta["dst_ip"] = arp.pdst
                meta["protocol"] = "ARP"
                if not meta["src_mac"]:
                    meta["src_mac"] = arp.hwsrc
                if not meta["dst_mac"]:
                    meta["dst_mac"] = arp.hwdst
                return meta

            # IP layer
            if not packet.haslayer(IP):  # type: ignore[union-attr]
                return None  # Non-IP, non-ARP — skip

            ip_layer = packet[IP]  # type: ignore[index]
            meta["src_ip"] = ip_layer.src
            meta["dst_ip"] = ip_layer.dst

            # Transport layer
            if packet.haslayer(TCP):  # type: ignore[union-attr]
                tcp = packet[TCP]  # type: ignore[index]
                meta["protocol"] = "TCP"
                meta["src_port"] = tcp.sport
                meta["dst_port"] = tcp.dport
                meta["tcp_flags"] = _decode_tcp_flags(int(tcp.flags))
            elif packet.haslayer(UDP):  # type: ignore[union-attr]
                udp = packet[UDP]  # type: ignore[index]
                meta["protocol"] = "UDP"
                meta["src_port"] = udp.sport
                meta["dst_port"] = udp.dport
            elif packet.haslayer(ICMP):  # type: ignore[union-attr]
                meta["protocol"] = "ICMP"

            return meta

        except Exception as exc:
            logger.debug("Failed to extract packet metadata: %s", exc)
            return None

    def _capture_thread(self, interface: str) -> None:
        """Thread target — runs the Scapy sniffer or demo generator until stopped."""
        # Demo simulation mode (allows full E2E testing when raw socket privileges are unavailable)
        if interface.lower() in ("demo", "virtual-iot-net", "simulated", "demo-iot-network"):
            self._run_demo_generator()
            return

        if not SCAPY_AVAILABLE:
            self._last_error = "Scapy is not installed in the current environment"
            with self._lock:
                self._running = False
            return

        def _on_packet(packet: object) -> None:
            """Per-packet callback invoked by Scapy."""
            meta = self._extract_packet_metadata(packet)
            if meta is None:
                self._stats.record_drop()
                return

            self._stats.record_packet(meta["length"], meta["protocol"])

            for cb in self._callbacks:
                try:
                    cb(meta)
                except Exception as exc:
                    logger.warning("Packet callback error: %s", exc)
                    self._stats.record_error()

        try:
            sniffer = AsyncSniffer(
                iface=interface,
                prn=_on_packet,
                store=False,
                stop_filter=lambda _pkt: self._stop_event.is_set(),
            )
            self._sniffer = sniffer
            sniffer.start()

            # Verify that the sniffer thread started without throwing an unhandled exception
            time.sleep(0.15)
            if getattr(sniffer, "thread", None) and not sniffer.thread.is_alive():
                exc = getattr(sniffer, "exception", None)
                if exc:
                    raise exc
                raise RuntimeError(f"Capture thread terminated immediately on interface '{interface}'.")

            while not self._stop_event.is_set():
                if getattr(sniffer, "thread", None) and not sniffer.thread.is_alive():
                    exc = getattr(sniffer, "exception", None)
                    if exc:
                        raise exc
                    break
                self._stop_event.wait(timeout=0.5)

            try:
                sniffer.stop()
            except Exception:
                pass
        except PermissionError as exc:
            err_msg = (
                f"Permission denied on '{interface}': raw packet capture requires "
                "root privileges (sudo) or Linux CAP_NET_RAW capability. "
                "Tip: You can select the 'demo' interface to test live traffic without root."
            )
            logger.error(err_msg)
            self._last_error = err_msg
            self._stats.record_error()
        except Exception as exc:
            err_msg = (
                f"Capture error on '{interface}': {exc}. "
                "Tip: You can select the 'demo' interface to test live traffic without root."
            )
            logger.error(err_msg)
            self._last_error = err_msg
            self._stats.record_error()
        finally:
            with self._lock:
                self._running = False

    def _run_demo_generator(self) -> None:
        """Generate realistic synthetic smart home traffic for demo / lab testing."""
        import random

        logger.info("Starting demo IoT traffic generator (no root required)...")
        traffic_templates = [
            # Smart Camera RTSP stream
            ("192.168.1.105", "AA:BB:CC:DD:EE:05", "192.168.1.1", "AA:BB:CC:DD:EE:01", 554, 49152, "TCP", 1400, "ACK,PSH"),
            # Smart Thermostat DNS & NTP queries
            ("192.168.1.120", "AA:BB:CC:DD:EE:20", "8.8.8.8", None, 52140, 53, "UDP", 84, None),
            # Smart Plug MQTT TLS telemetry
            ("192.168.1.142", "AA:BB:CC:DD:EE:42", "54.210.12.34", None, 41200, 8883, "TCP", 220, "ACK"),
            # Laptop HTTPS Web browsing
            ("192.168.1.200", "AA:BB:CC:DD:EE:99", "142.250.190.46", None, 58210, 443, "TCP", 890, "ACK,PSH"),
            # Gateway ARP broadcast
            ("192.168.1.1", "AA:BB:CC:DD:EE:01", "192.168.1.255", "FF:FF:FF:FF:FF:FF", None, None, "ARP", 42, None),
        ]

        try:
            while not self._stop_event.is_set():
                tpl = random.choice(traffic_templates)
                meta = {
                    "timestamp": time.time(),
                    "src_ip": tpl[0],
                    "src_mac": tpl[1],
                    "dst_ip": tpl[2],
                    "dst_mac": tpl[3],
                    "src_port": tpl[4],
                    "dst_port": tpl[5],
                    "protocol": tpl[6],
                    "length": tpl[7] + random.randint(-15, 30),
                    "tcp_flags": tpl[8],
                }

                self._stats.record_packet(meta["length"], meta["protocol"])

                for cb in self._callbacks:
                    try:
                        cb(meta)
                    except Exception as exc:
                        logger.warning("Packet callback error in demo generator: %s", exc)
                        self._stats.record_error()

                # Pace packet arrival between 100ms and 300ms
                self._stop_event.wait(timeout=random.uniform(0.12, 0.28))
        finally:
            with self._lock:
                self._running = False
            logger.info("Demo IoT traffic generator stopped.")


# ---------------------------------------------------------------------------
# Interface enumeration helpers
# ---------------------------------------------------------------------------

def _list_via_psutil() -> Optional[list[InterfaceInfo]]:
    """Enumerate interfaces using *psutil*."""
    try:
        import psutil  # type: ignore[import-untyped]
    except ImportError:
        return None

    result: list[InterfaceInfo] = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for name, addr_list in addrs.items():
        info = InterfaceInfo(name=name)
        st = stats.get(name)
        if st:
            info.is_up = st.isup
        for addr in addr_list:
            if addr.family == socket.AF_INET:
                info.addresses.append(addr.address)
            elif addr.family == socket.AF_INET6:
                info.addresses.append(addr.address)
            elif addr.family == psutil.AF_LINK:
                info.mac_address = addr.address
        info.is_loopback = name == "lo" or any(
            a.startswith("127.") for a in info.addresses
        )
        result.append(info)

    return result


def _list_via_netifaces() -> Optional[list[InterfaceInfo]]:
    """Enumerate interfaces using *netifaces2* (or *netifaces*)."""
    try:
        import netifaces2 as netifaces  # type: ignore[import-untyped]
    except ImportError:
        try:
            import netifaces  # type: ignore[import-untyped]
        except ImportError:
            return None

    AF_INET = netifaces.AF_INET  # type: ignore[attr-defined]
    AF_INET6 = netifaces.AF_INET6  # type: ignore[attr-defined]
    AF_LINK = netifaces.AF_LINK  # type: ignore[attr-defined]

    result: list[InterfaceInfo] = []
    for name in netifaces.interfaces():  # type: ignore[attr-defined]
        info = InterfaceInfo(name=name)
        try:
            iface_addrs = netifaces.ifaddresses(name)  # type: ignore[attr-defined]
        except ValueError:
            result.append(info)
            continue

        for entry in iface_addrs.get(AF_INET, []):
            addr = entry.get("addr")
            if addr:
                info.addresses.append(addr)
        for entry in iface_addrs.get(AF_INET6, []):
            addr = entry.get("addr")
            if addr:
                info.addresses.append(addr)
        for entry in iface_addrs.get(AF_LINK, []):
            addr = entry.get("addr")
            if addr:
                info.mac_address = addr

        info.is_loopback = name == "lo" or any(
            a.startswith("127.") for a in info.addresses
        )
        # netifaces doesn't report link state; assume up if addresses exist.
        info.is_up = bool(info.addresses)
        result.append(info)

    return result


def _list_via_socket() -> list[InterfaceInfo]:
    """Minimal fallback using only the standard library.

    Returns at most the loopback interface and whatever ``socket`` can
    resolve for the host.
    """
    result: list[InterfaceInfo] = []

    # Loopback is almost always present.
    try:
        socket.if_nametoindex("lo")
        result.append(
            InterfaceInfo(
                name="lo",
                addresses=["127.0.0.1"],
                is_up=True,
                is_loopback=True,
            )
        )
    except OSError:
        pass

    # Try to detect the default outbound interface.
    try:
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
        if host_ip and not host_ip.startswith("127."):
            result.append(
                InterfaceInfo(
                    name="unknown",
                    addresses=[host_ip],
                    is_up=True,
                    is_loopback=False,
                    description="Detected via gethostname()",
                )
            )
    except OSError:
        pass

    return result
