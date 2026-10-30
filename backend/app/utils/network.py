"""Network utilities for validating local network membership."""
import ipaddress
import logging
import socket
from typing import List, Optional, Set

import psutil

logger = logging.getLogger(__name__)


def get_interface_info(interface: str) -> Optional[dict]:
    """Get interface IP and netmask information."""
    try:
        addrs = psutil.net_if_addrs()
        iface_addrs = addrs.get(interface)
        if not iface_addrs:
            return None
        for addr in iface_addrs:
            if addr.family == socket.AF_INET and addr.address and addr.netmask:
                try:
                    network = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
                    return {
                        "ip": addr.address,
                        "netmask": addr.netmask,
                        "network": str(network),
                    }
                except Exception:
                    continue
    except Exception as exc:
        logger.error("Failed to get interface info for %s: %s", interface, exc)
    return None


def get_local_networks(interface: Optional[str] = None) -> Set[ipaddress.IPv4Network]:
    """Get all local IPv4 networks from the system or specified interface."""
    networks = set()
    try:
        if interface:
            info = get_interface_info(interface)
            if info:
                try:
                    networks.add(ipaddress.IPv4Network(info["network"], strict=False))
                except Exception:
                    pass
        else:
            addrs = psutil.net_if_addrs()
            for iface_name, iface_addrs in addrs.items():
                for addr in iface_addrs:
                    if addr.family == socket.AF_INET and addr.address and addr.netmask:
                        try:
                            # Skip loopback
                            if addr.address.startswith("127."):
                                continue
                            networks.add(ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False))
                        except Exception:
                            continue
    except Exception as exc:
        logger.error("Failed to get local networks: %s", exc)
    return networks


def is_ip_in_monitored_network(ip_str: str, networks: Set[ipaddress.IPv4Network]) -> bool:
    """Check if an IP belongs to any monitored network."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_loopback or ip.is_unspecified or ip.is_multicast or ip.is_reserved:
            return False
        if isinstance(ip, ipaddress.IPv4Address):
            for net in networks:
                if ip in net:
                    return True
            return False
        # For IPv6, be more restrictive - only if explicitly in configured networks
        return False
    except Exception:
        return False


def is_likely_external(ip_str: str) -> bool:
    """Basic check if IP is likely external (not private/local)."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
            return False
        if isinstance(ip, ipaddress.IPv4Address):
            # RFC1918 private
            if ip in ipaddress.IPv4Network("10.0.0.0/8") or \
               ip in ipaddress.IPv4Network("172.16.0.0/12") or \
               ip in ipaddress.IPv4Network("192.168.0.0/16"):
                return False
            # CGNAT
            if ip in ipaddress.IPv4Network("100.64.0.0/10"):
                return False
        return True
    except Exception:
        return True
