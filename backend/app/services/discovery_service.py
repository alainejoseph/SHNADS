"""Discovery service — ARP-based network device discovery."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.services.device_service import DeviceService

logger = logging.getLogger(__name__)

# Optional imports — scapy and netifaces may not be available in all
# environments (e.g. CI without root privileges).
try:
    from scapy.all import ARP, Ether, srp, conf as scapy_conf

    _SCAPY_AVAILABLE = True
except ImportError:
    _SCAPY_AVAILABLE = False
    logger.warning("scapy is not available — ARP discovery will be disabled.")

try:
    import netifaces

    _NETIFACES_AVAILABLE = True
except ImportError:
    _NETIFACES_AVAILABLE = False
    logger.warning("netifaces is not available — subnet detection will be limited.")


class DiscoveryService:
    """Performs ARP-based network device discovery."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._device_service = DeviceService(db)

    async def discover_devices(
        self, interface: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run ARP discovery on the local subnet.

        The discovery runs in a background thread to avoid blocking the
        event loop.  Discovered hosts are upserted into the devices
        collection.

        Args:
            interface: Network interface to use.  If ``None``, the default
                interface is used.

        Returns:
            A summary dict with the number of devices discovered.
        """
        if not _SCAPY_AVAILABLE:
            return {
                "status": "error",
                "message": "scapy is not installed — ARP discovery unavailable.",
                "devices_found": 0,
            }

        subnet = self._detect_subnet(interface)
        if not subnet:
            return {
                "status": "error",
                "message": "Could not determine subnet for discovery.",
                "devices_found": 0,
            }

        logger.info(
            "Starting ARP discovery on subnet %s (interface=%s) …",
            subnet,
            interface or "default",
        )

        # Run the blocking ARP scan in a thread.
        loop = asyncio.get_event_loop()
        discovered = await loop.run_in_executor(
            None, self._arp_scan, subnet, interface
        )

        # Upsert every discovered device.
        for entry in discovered:
            await self._device_service.upsert_device(
                ip=entry["ip"],
                mac=entry.get("mac"),
                source="arp_discovery",
            )

        logger.info("ARP discovery complete — %d devices found.", len(discovered))
        return {
            "status": "discovery_complete",
            "message": f"Discovered {len(discovered)} device(s) on {subnet}.",
            "devices_found": len(discovered),
        }

    # ----- internal helpers -------------------------------------------------

    @staticmethod
    def _arp_scan(
        subnet: str, interface: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Perform a synchronous ARP scan using scapy.

        Args:
            subnet: Target subnet in CIDR notation (e.g. ``192.168.1.0/24``).
            interface: Optional network interface name.

        Returns:
            A list of dicts with ``ip`` and ``mac`` keys.
        """
        results: List[Dict[str, str]] = []
        try:
            arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
            kwargs: Dict[str, Any] = {"timeout": 3, "verbose": False}
            if interface:
                kwargs["iface"] = interface

            answered, _ = srp(arp_request, **kwargs)

            for _sent, received in answered:
                results.append(
                    {
                        "ip": received.psrc,
                        "mac": received.hwsrc,
                    }
                )
        except Exception as exc:
            logger.error("ARP scan failed: %s", exc)

        return results

    @staticmethod
    def _detect_subnet(interface: Optional[str] = None) -> Optional[str]:
        """Attempt to detect the local subnet for the given interface.

        Uses configured ``DISCOVERY_SUBNET`` first, then falls back to
        netifaces-based detection.

        Args:
            interface: Optional network interface name.

        Returns:
            A CIDR subnet string, or ``None`` if detection fails.
        """
        settings = get_settings()
        if settings.DISCOVERY_SUBNET:
            return settings.DISCOVERY_SUBNET

        if not _NETIFACES_AVAILABLE:
            # Fallback: try common private subnets.
            return "192.168.1.0/24"

        try:
            target_iface = interface or netifaces.gateways()["default"].get(
                netifaces.AF_INET, [None, None]
            )[1]

            if not target_iface:
                return "192.168.1.0/24"

            addrs = netifaces.ifaddresses(target_iface)
            ipv4_info = addrs.get(netifaces.AF_INET, [{}])[0]
            ip_addr = ipv4_info.get("addr")
            netmask = ipv4_info.get("netmask")

            if not ip_addr or not netmask:
                return "192.168.1.0/24"

            # Simple CIDR calculation
            prefix_len = sum(
                bin(int(octet)).count("1") for octet in netmask.split(".")
            )
            octets = ip_addr.split(".")
            # Zero out host bits (rough but sufficient for /24, /16, etc.)
            network_octets = []
            remaining = prefix_len
            for octet in octets:
                if remaining >= 8:
                    network_octets.append(octet)
                    remaining -= 8
                elif remaining > 0:
                    mask = (0xFF << (8 - remaining)) & 0xFF
                    network_octets.append(str(int(octet) & mask))
                    remaining = 0
                else:
                    network_octets.append("0")

            return f"{'.'.join(network_octets)}/{prefix_len}"
        except Exception as exc:
            logger.error("Subnet detection failed: %s", exc)
            return "192.168.1.0/24"

