"""Discovery service — ARP-based network device discovery."""

import asyncio
import ipaddress
import logging
import re
import time
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
    _SCAPY_IMPORT_ERROR: Optional[str] = None
except Exception as exc:
    _SCAPY_AVAILABLE = False
    _SCAPY_IMPORT_ERROR = str(exc)
    ARP = Ether = srp = scapy_conf = None  # type: ignore[assignment,misc]
    logger.warning("Scapy could not initialize — ARP discovery will be disabled: %s", exc)

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
            raise RuntimeError(f"Scapy could not initialize; ARP discovery is unavailable: {_SCAPY_IMPORT_ERROR}")

        if interface and not self._interface_exists(interface):
            raise ValueError(f"Network interface '{interface}' does not exist or has no IPv4 address.")

        subnet = self._detect_subnet(interface)
        if not subnet:
            raise ValueError(
                "Could not determine a usable monitored IPv4 subnet. A /32 host route "
                "cannot be scanned; configure DISCOVERY_SUBNET or select an interface "
                "connected to the monitored LAN."
            )
        try:
            network = ipaddress.ip_network(subnet, strict=False)
            if network.version != 4 or network.prefixlen in (0, 32):
                raise ValueError
        except ValueError as exc:
            raise ValueError(f"Invalid discovery subnet '{subnet}'. Provide a valid IPv4 CIDR subnet.") from exc

        logger.info(
            "Starting ARP discovery on subnet %s (interface=%s) …",
            subnet,
            interface or "default",
        )

        # Run the blocking ARP scan in a thread.
        loop = asyncio.get_running_loop()
        discovered = await loop.run_in_executor(None, self._arp_scan, subnet, interface)

        # Validate responses again before persistence; only hosts in this scan's
        # monitored network can become discovered devices.
        unique = self._unique_valid_responses(discovered, network)
        for entry in unique.values():
            await self._device_service.upsert_device(
                ip=entry["ip"],
                mac=entry.get("mac"),
                source="arp_discovery",
                skip_validation=True,
            )

        logger.info("ARP discovery complete — %d devices found.", len(unique))
        return {
            "status": "discovery_complete",
            "message": (
                f"Discovered {len(unique)} device(s) on {subnet}."
                if unique else f"No devices responded to ARP discovery on {subnet}."
            ),
            "devices_found": len(unique),
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
        settings = get_settings()
        network = ipaddress.ip_network(subnet, strict=False)
        if network.version != 4 or network.prefixlen in (0, 32):
            raise ValueError(f"Invalid discovery subnet '{subnet}'. Provide a valid IPv4 CIDR subnet.")
        if network.num_addresses > 65536:
            raise ValueError(f"Discovery subnet '{subnet}' is too large to scan safely; narrow the subnet to at most 65,536 addresses.")
        if interface and not DiscoveryService._interface_exists(interface):
            raise ValueError(f"Network interface '{interface}' does not exist or has no IPv4 address.")
        if not _SCAPY_AVAILABLE:
            raise RuntimeError(f"Scapy could not initialize; ARP discovery is unavailable: {_SCAPY_IMPORT_ERROR}")

        pending = [str(host) for host in network.hosts()]
        results: Dict[str, Dict[str, str]] = {}
        deadline = time.monotonic() + settings.DISCOVERY_MAX_DURATION
        attempts = max(1, settings.ARP_RETRIES + 1)
        for attempt in range(attempts):
            remaining = pending
            if not remaining or time.monotonic() >= deadline:
                break
            packets = [Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip) for ip in remaining]
            kwargs: Dict[str, Any] = {
                "timeout": min(settings.ARP_TIMEOUT, max(0.01, deadline - time.monotonic())),
                "verbose": False,
            }
            if interface:
                kwargs["iface"] = interface
            try:
                answered, unanswered = srp(packets, **kwargs)
            except Exception as exc:
                raise RuntimeError(f"ARP scan failed on interface '{interface or 'default'}' for {subnet}: {exc}") from exc
            for _sent, received in answered:
                ip, mac = getattr(received, "psrc", ""), getattr(received, "hwsrc", "")
                if DiscoveryService._valid_response(ip, mac, network):
                    results[ip] = {"ip": ip, "mac": mac.lower()}
            pending = []
            # Scapy returns unanswered packets directly (unlike its answered
            # list, which contains (sent, received) pairs).
            for sent in unanswered:
                target = getattr(getattr(sent, "payload", None), "pdst", None)
                try:
                    target_ip = ipaddress.ip_address(target)
                except (ValueError, TypeError):
                    continue
                if target_ip in network and str(target_ip) not in results:
                    pending.append(str(target_ip))
            if attempt + 1 < attempts and pending and time.monotonic() < deadline:
                time.sleep(min(settings.ARP_INTER_RETRY_DELAY, max(0, deadline - time.monotonic())))
        return list(results.values())

    @staticmethod
    def _interface_exists(interface: str) -> bool:
        from app.utils.network import get_interface_info
        return get_interface_info(interface) is not None

    @staticmethod
    def _valid_response(ip: str, mac: str, network: Any) -> bool:
        try:
            address = ipaddress.ip_address(ip)
            valid_mac = re.fullmatch(r"(?i)(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", mac)
            first_octet = int(mac[:2], 16) if valid_mac else 0xff
            return (address.version == 4 and address in network and not address.is_unspecified
                    and not address.is_multicast and not address.is_loopback and not address.is_reserved
                    and bool(valid_mac) and not (first_octet & 1) and mac.lower() != "00:00:00:00:00:00")
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _unique_valid_responses(
        responses: List[Dict[str, str]], network: Any
    ) -> Dict[str, Dict[str, str]]:
        unique: Dict[str, Dict[str, str]] = {}
        for entry in responses:
            ip, mac = entry.get("ip", ""), entry.get("mac", "")
            if DiscoveryService._valid_response(ip, mac, network):
                unique[ip] = {"ip": ip, "mac": mac.lower()}
        return unique

    @staticmethod
    def _detect_subnet(interface: Optional[str] = None) -> Optional[str]:
        """Attempt to detect the local subnet for the given interface.

        Uses the selected interface if given, then configured ``DISCOVERY_SUBNET``,
        the default gateway network, and finally a detected local network.

        Args:
            interface: Optional network interface name.

        Returns:
            A CIDR subnet string, or ``None`` if detection fails.
        """
        from app.utils.network import get_interface_info, get_local_networks

        # 1. If an interface is specified, use only that interface.
        if interface:
            info = get_interface_info(interface)
            if info and info.get("network"):
                network = ipaddress.ip_network(info["network"], strict=False)
                return str(network) if network.prefixlen < 32 else None

            if _NETIFACES_AVAILABLE:
                try:
                    addrs = netifaces.ifaddresses(interface)
                    ipv4_info = addrs.get(netifaces.AF_INET, [{}])[0]
                    ip_addr = ipv4_info.get("addr")
                    netmask = ipv4_info.get("netmask")
                    if ip_addr and netmask:
                        prefix_len = sum(
                            bin(int(octet)).count("1") for octet in netmask.split(".")
                        )
                        network = ipaddress.IPv4Network(f"{ip_addr}/{prefix_len}", strict=False)
                        return str(network) if network.prefixlen < 32 else None
                except Exception as exc:
                    logger.debug("Failed getting interface info via netifaces for %s: %s", interface, exc)

            return None

        # 2. Use configured DISCOVERY_SUBNET if provided
        settings = get_settings()
        if settings.DISCOVERY_SUBNET:
            return settings.DISCOVERY_SUBNET

        # 3. Prefer the interface attached to the default route when available.
        if _NETIFACES_AVAILABLE:
            try:
                gateways = netifaces.gateways()
                target_iface = gateways.get("default", {}).get(netifaces.AF_INET, [None, None])[1]
                if target_iface:
                    info = get_interface_info(target_iface)
                    if info and info.get("network"):
                        network = ipaddress.ip_network(info["network"], strict=False)
                        if network.prefixlen < 32:
                            return str(network)
                        logger.warning(
                            "Default route interface %s has only a /32 address; refusing to scan an unrelated network.",
                            target_iface,
                        )
                        return None
            except Exception as exc:
                logger.debug("Subnet detection failed via netifaces gateway: %s", exc)

        # 4. Last resort: first detected local network.
        try:
            local_nets = get_local_networks()
            candidates = [net for net in local_nets if not net.is_loopback and net.prefixlen < 32]
            if len(candidates) == 1:
                return str(candidates[0])
            if len(candidates) > 1:
                logger.warning("Multiple local subnets found; configure DISCOVERY_SUBNET or select an interface.")
        except Exception as exc:
            logger.debug("Failed getting local networks: %s", exc)

        return None

