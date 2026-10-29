#!/usr/bin/env python3
"""
Standalone capture diagnostic - verify real packet capture without FastAPI/MongoDB.

This MUST prove packets are actually received before integrating.
"""
import argparse
import signal
import sys
import time
from collections import Counter

from collector.capture import PacketCapture, SCAPY_AVAILABLE


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose live packet capture")
    parser.add_argument("--interface", "-i", required=True, help="Interface to capture on")
    parser.add_argument("--duration", "-d", type=int, default=15, help="Capture duration in seconds")
    args = parser.parse_args()

    print("=" * 60)
    print("PACKET CAPTURE DIAGNOSTIC")
    print("=" * 60)
    print(f"Interface: {args.interface}")
    print(f"Duration: {args.duration} seconds")
    print(f"Scapy available: {SCAPY_AVAILABLE}")
    print("=" * 60)
    print()

    # Validate interface
    if args.interface.lower() not in ("demo", "virtual-iot-net", "simulated", "demo-iot-network"):
        try:
            import socket

            socket.if_nametoindex(args.interface)
            print(f"[OK] Interface {args.interface} exists")
        except Exception as e:
            print(f"[FAIL] Interface {args.interface} not found: {e}", file=sys.stderr)
            print("\nRun 'python3 collector/list_interfaces.py' to see available interfaces")
            return 1
    else:
        print(f"[OK] Interface {args.interface} is valid (demo/simulator)")

    # Stats
    packet_count = 0
    protocol_counts = Counter()
    last_packet_time = None
    samples = []
    errors = []

    def on_packet(meta: dict) -> None:
        nonlocal packet_count, last_packet_time
        packet_count += 1
        last_packet_time = time.time()
        proto = meta.get("protocol", "Other")
        protocol_counts[proto] += 1

        if len(samples) < 10:
            samples.append(
                {
                    "time": meta.get("timestamp"),
                    "src_ip": meta.get("src_ip"),
                    "dst_ip": meta.get("dst_ip"),
                    "src_port": meta.get("src_port"),
                    "dst_port": meta.get("dst_port"),
                    "protocol": proto,
                    "length": meta.get("length"),
                }
            )

    cap = PacketCapture()
    try:
        print(f"\nStarting capture...")
        cap.start(args.interface, packet_callback=on_packet)
        print(f"[OK] Capture started")
        print(f"\nCapturing for {args.duration} seconds... (generate traffic on this interface)")
        print()

        for i in range(args.duration):
            time.sleep(1)
            if (i + 1) % 3 == 0:
                print(f"  [{i + 1}s] Packets: {packet_count}, Last: {last_packet_time or 'None'}")

        print("\nStopping capture...")
        stats = cap.stop()
        print("[OK] Capture stopped")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        try:
            stats = cap.stop()
        except Exception:
            stats = cap.stats
    except PermissionError as e:
        print(f"[FAIL] Permission denied: {e}", file=sys.stderr)
        print("\nTry running with sudo: sudo python3 collector/diagnose_capture.py ...", file=sys.stderr)
        print("Or use the 'demo' interface which doesn't require root.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[FAIL] Capture error: {e}", file=sys.stderr)
        errors.append(str(e))
        return 1

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Packets received: {packet_count}")
    print(f"Packets captured (from stats): {getattr(stats, 'packets_captured', packet_count)}")
    print(f"Last packet time: {last_packet_time}")
    print(f"Errors: {len(errors)}")
    print("\nProtocol breakdown:")
    for proto, cnt in protocol_counts.most_common():
        print(f"  {proto}: {cnt}")
    print("\nSample packets (first 10):")
    for i, s in enumerate(samples):
        print(f"  {i + 1}. {s['src_ip']}:{s['src_port']} -> {s['dst_ip']}:{s['dst_port']} [{s['protocol']}] len={s['length']}")

    print("\n" + "=" * 60)
    if packet_count == 0:
        print("VERDICT: NO PACKETS RECEIVED")
        print("- Is traffic actually flowing on this interface?")
        print("- Are you running with sufficient privileges (sudo)?")
        print("- For WSL/VMs, is traffic delivered to this environment?")
        print("- Try: sudo tcpdump -ni <interface> -c 20 to verify independently")
        print("- Try the 'demo' interface for testing without real traffic")
        return 2
    else:
        print("VERDICT: PACKETS RECEIVED SUCCESSFULLY")
        print(f"- Successfully captured {packet_count} real packets")
        print("- Capture is working correctly on this interface")
        return 0


if __name__ == "__main__":
    sys.exit(main())
