#!/usr/bin/env python3
"""
List available network interfaces for capture.

Reports interface name, description, addresses, and whether it can be opened.
"""
import argparse
import platform
import socket
import sys

from collector.capture import PacketCapture


def main() -> int:
    parser = argparse.ArgumentParser(description="List network interfaces for capture")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version.split()[0]}")
    print()

    try:
        interfaces = PacketCapture.list_interfaces()
    except Exception as e:
        print(f"Error listing interfaces: {e}", file=sys.stderr)
        return 1

    if args.json:
        import json

        data = []
        for iface in interfaces:
            data.append(
                {
                    "name": iface.name,
                    "addresses": iface.addresses,
                    "mac_address": iface.mac_address,
                    "is_up": iface.is_up,
                    "is_loopback": iface.is_loopback,
                    "description": iface.description,
                }
            )
        print(json.dumps(data, indent=2))
        return 0

    print(f"Found {len(interfaces)} interface(s):\n")
    for idx, iface in enumerate(interfaces):
        print(f"{idx + 1}. {iface.name}")
        print(f"   Description: {iface.description or 'N/A'}")
        print(f"   Addresses: {', '.join(iface.addresses) if iface.addresses else 'N/A'}")
        print(f"   MAC: {iface.mac_address or 'N/A'}")
        print(f"   Up: {iface.is_up}, Loopback: {iface.is_loopback}")
        try:
            can_open = PacketCapture.validate_interface(iface.name)
            print(f"   Can open for capture: {can_open}")
        except Exception as e:
            print(f"   Can open for capture: Error - {e}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
