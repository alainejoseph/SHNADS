"""
Shared utilities for the collector package.

Provides helper functions for MAC address formatting, TCP flag
summarization, network interface inspection, and IP classification.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import struct
from typing import Optional


def format_mac(mac: str) -> str:
    """Normalize a MAC address to upper-case ``XX:XX:XX:XX:XX:XX`` format.

    Accepts colon-separated, dash-separated, or bare hex strings.

    Args:
        mac: Raw MAC address string.

    Returns:
        Normalized MAC address.

    Raises:
        ValueError: If *mac* is not a valid MAC address.
    """
    # Strip whitespace
    mac = mac.strip()

    # Remove common separators
    raw = re.sub(r"[:\-.]", "", mac)

    if len(raw) != 12 or not re.fullmatch(r"[0-9a-fA-F]{12}", raw):
        raise ValueError(f"Invalid MAC address: {mac!r}")

    upper = raw.upper()
    return ":".join(upper[i : i + 2] for i in range(0, 12, 2))


# Canonical flag ordering for deterministic summaries.
_TCP_FLAG_ORDER = ["SYN", "SYN-ACK", "ACK", "PSH", "URG", "FIN", "FIN-ACK", "RST"]


def format_tcp_flags(flags: list[str]) -> str:
    """Produce a compact summary of TCP flags observed in a flow.

    Flags are de-duplicated and returned in canonical order.

    Args:
        flags: List of flag strings such as ``["SYN", "ACK", "FIN"]``.

    Returns:
        Comma-separated summary, e.g. ``"SYN,ACK,FIN"``.
    """
    if not flags:
        return ""

    seen: set[str] = set(flags)
    ordered = [f for f in _TCP_FLAG_ORDER if f in seen]
    # Append any flags not in the canonical list (shouldn't happen, but safe).
    extras = sorted(seen - set(_TCP_FLAG_ORDER))
    ordered.extend(extras)
    return ",".join(ordered)


def get_interface_subnet(interface: str) -> Optional[str]:
    """Return the first IPv4 subnet in CIDR notation for *interface*.

    Tries ``netifaces2`` first, then ``psutil``, and finally falls back
    to a low-level ``ioctl`` approach on Linux.

    Args:
        interface: OS network interface name (e.g. ``"eth0"``).

    Returns:
        CIDR string such as ``"192.168.1.0/24"``, or ``None`` if the
        subnet cannot be determined.
    """
    subnet = _get_subnet_netifaces(interface)
    if subnet is not None:
        return subnet

    subnet = _get_subnet_psutil(interface)
    if subnet is not None:
        return subnet

    return _get_subnet_ioctl(interface)


def _get_subnet_netifaces(interface: str) -> Optional[str]:
    """Attempt to determine the subnet via *netifaces2*."""
    try:
        import netifaces2 as netifaces  # type: ignore[import-untyped]
    except ImportError:
        try:
            import netifaces  # type: ignore[import-untyped]
        except ImportError:
            return None

    AF_INET = netifaces.AF_INET  # type: ignore[attr-defined]
    try:
        addrs = netifaces.ifaddresses(interface)  # type: ignore[attr-defined]
    except ValueError:
        return None

    inet = addrs.get(AF_INET)
    if not inet:
        return None

    entry = inet[0]
    ip_str = entry.get("addr")
    mask_str = entry.get("netmask")
    if not ip_str or not mask_str:
        return None

    try:
        network = ipaddress.IPv4Network(f"{ip_str}/{mask_str}", strict=False)
        return str(network)
    except (ValueError, TypeError):
        return None


def _get_subnet_psutil(interface: str) -> Optional[str]:
    """Attempt to determine the subnet via *psutil*."""
    try:
        import psutil  # type: ignore[import-untyped]
    except ImportError:
        return None

    addrs = psutil.net_if_addrs()
    iface_addrs = addrs.get(interface)
    if not iface_addrs:
        return None

    for addr in iface_addrs:
        if addr.family == socket.AF_INET and addr.address and addr.netmask:
            try:
                network = ipaddress.IPv4Network(
                    f"{addr.address}/{addr.netmask}", strict=False
                )
                return str(network)
            except (ValueError, TypeError):
                continue

    return None


def _get_subnet_ioctl(interface: str) -> Optional[str]:
    """Linux-only fallback using ``ioctl`` to read interface address."""
    try:
        import fcntl

        SIOCGIFADDR = 0x8915
        SIOCGIFNETMASK = 0x891B

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            iface_bytes = interface.encode("utf-8")[:15]
            ip_bytes = fcntl.ioctl(
                sock.fileno(), SIOCGIFADDR, struct.pack("256s", iface_bytes)
            )
            ip_str = socket.inet_ntoa(ip_bytes[20:24])

            mask_bytes = fcntl.ioctl(
                sock.fileno(), SIOCGIFNETMASK, struct.pack("256s", iface_bytes)
            )
            mask_str = socket.inet_ntoa(mask_bytes[20:24])
        finally:
            sock.close()

        network = ipaddress.IPv4Network(f"{ip_str}/{mask_str}", strict=False)
        return str(network)
    except Exception:
        return None


def is_private_ip(ip: str) -> bool:
    """Return ``True`` if *ip* belongs to an RFC-1918 private range.

    Also returns ``True`` for link-local (169.254.x.x) and loopback
    addresses.

    Args:
        ip: IPv4 or IPv6 address string.

    Returns:
        ``True`` if the address is private / reserved, ``False`` otherwise.
        Returns ``False`` for malformed input instead of raising.
    """
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return False
