"""
Device observation module for the Smart Home Network Anomaly Detection System.

Maintains an in-memory observation cache for devices identified via passive
packet inspection or active local ARP discovery, and prepares them for
persistence into MongoDB.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from collector.utils import format_mac, get_interface_subnet

logger = logging.getLogger(__name__)

# Scapy import for ARP discovery
try:
    from scapy.all import ARP, Ether, srp  # type: ignore[import-untyped]
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


@dataclass
class DeviceObservation:
    """Represents an observed network device endpoint."""

    ip_address: str
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    first_seen: float = 0.0
    last_seen: float = 0.0
    source: str = "passive_capture"  # e.g., "passive_capture", "arp_discovery"
    packet_count: int = 0

    @property
    def device_key(self) -> str:
        """Generate a deterministic unique key for the device."""
        if self.mac_address:
            return f"{self.ip_address}_{self.mac_address}"
        return self.ip_address

    def to_dict(self) -> dict:
        """Convert to dictionary matching backend device storage format."""
        return {
            "device_key": self.device_key,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "hostname": self.hostname,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "source": self.source,
            "metadata": {
                "packet_count": self.packet_count,
            },
        }


class DeviceObserver:
    """Observes devices from network traffic and ARP scanning in a thread-safe manner."""

    def __init__(
        self,
        flush_callback: Optional[Callable[[List[DeviceObservation]], None]] = None,
        flush_interval: float = 10.0,
    ) -> None:
        self._observed: Dict[str, DeviceObservation] = {}
        self._pending_updates: Dict[str, DeviceObservation] = {}
        self._lock: threading.Lock = threading.Lock()
        self._flush_callback = flush_callback
        self._flush_interval = flush_interval
        self._last_flush: float = time.time()

    def observe_packet(self, packet_meta: dict) -> None:
        """Record device observations from parsed packet metadata.

        Observes source and destination IP/MAC addresses.
        """
        now = packet_meta.get("timestamp") or time.time()

        src_ip = packet_meta.get("src_ip")
        src_mac = packet_meta.get("src_mac")
        if src_mac:
            try:
                src_mac = format_mac(src_mac)
            except ValueError:
                src_mac = None

        dst_ip = packet_meta.get("dst_ip")
        dst_mac = packet_meta.get("dst_mac")
        if dst_mac:
            try:
                dst_mac = format_mac(dst_mac)
            except ValueError:
                dst_mac = None

        with self._lock:
            if src_ip:
                self._update_endpoint(src_ip, src_mac, now, "passive_capture")
            if dst_ip:
                self._update_endpoint(dst_ip, dst_mac, now, "passive_capture")

            if self._flush_callback and (time.time() - self._last_flush >= self._flush_interval):
                self._trigger_flush()

    def _update_endpoint(
        self,
        ip: str,
        mac: Optional[str],
        timestamp: float,
        source: str,
        hostname: Optional[str] = None,
    ) -> None:
        """Internal helper to insert or update an endpoint (must hold self._lock)."""
        key = f"{ip}_{mac}" if mac else ip

        obs = self._observed.get(key)
        if obs is None:
            # Also check if we previously saw this IP without a MAC
            if mac and ip in self._observed:
                old_obs = self._observed.pop(ip)
                obs = DeviceObservation(
                    ip_address=ip,
                    mac_address=mac,
                    hostname=hostname or old_obs.hostname,
                    first_seen=old_obs.first_seen,
                    last_seen=timestamp,
                    source=source,
                    packet_count=old_obs.packet_count + 1,
                )
            else:
                obs = DeviceObservation(
                    ip_address=ip,
                    mac_address=mac,
                    hostname=hostname,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    source=source,
                    packet_count=1,
                )
            self._observed[key] = obs
        else:
            obs.last_seen = max(obs.last_seen, timestamp)
            obs.packet_count += 1
            if mac and not obs.mac_address:
                obs.mac_address = mac
            if hostname and not obs.hostname:
                obs.hostname = hostname

        self._pending_updates[key] = obs

    def get_pending_updates(self) -> List[DeviceObservation]:
        """Retrieve and clear pending device updates."""
        with self._lock:
            updates = list(self._pending_updates.values())
            self._pending_updates.clear()
            return updates

    def get_observed_devices(self) -> List[DeviceObservation]:
        """Retrieve a snapshot of all observed devices."""
        with self._lock:
            return list(self._observed.values())

    def _trigger_flush(self) -> None:
        """Trigger the configured flush callback with pending updates."""
        if not self._flush_callback or not self._pending_updates:
            return
        updates = list(self._pending_updates.values())
        self._pending_updates.clear()
        self._last_flush = time.time()
        try:
            self._flush_callback(updates)
        except Exception as exc:
            logger.error("Error in DeviceObserver flush callback: %s", exc)

    @staticmethod
    def discover_via_arp(
        interface: str, subnet: Optional[str] = None, timeout: float = 3.0
    ) -> List[DeviceObservation]:
        """Perform active ARP discovery on the given interface/subnet.

        Requires appropriate privileges (e.g. root/CAP_NET_RAW) and Scapy.
        """
        if not SCAPY_AVAILABLE:
            logger.warning("Scapy is not available; cannot perform ARP discovery.")
            return []

        target_subnet = subnet or get_interface_subnet(interface)
        if not target_subnet:
            logger.error("Could not determine subnet for interface '%s'.", interface)
            return []

        logger.info("Starting ARP scan on %s for subnet %s (timeout: %.1fs)", interface, target_subnet, timeout)
        discovered: List[DeviceObservation] = []
        now = time.time()

        try:
            # Craft broadcast ARP request
            arp_req = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_subnet)
            ans, _ = srp(arp_req, iface=interface, timeout=timeout, verbose=0, retry=1)

            for snd, rcv in ans:
                ip = rcv.psrc
                try:
                    mac = format_mac(rcv.hwsrc)
                except Exception:
                    mac = rcv.hwsrc

                # Attempt best-effort reverse DNS hostname lookup
                hostname = None
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except (socket.herror, socket.gaierror, OSError):
                    pass

                discovered.append(
                    DeviceObservation(
                        ip_address=ip,
                        mac_address=mac,
                        hostname=hostname,
                        first_seen=now,
                        last_seen=now,
                        source="arp_discovery",
                        packet_count=1,
                    )
                )

        except PermissionError:
            logger.error("Permission denied when sending raw ARP packets on '%s'.", interface)
        except Exception as exc:
            logger.error("Failed during ARP discovery on '%s': %s", interface, exc)

        return discovered

