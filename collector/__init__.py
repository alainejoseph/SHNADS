"""
Collector package — Smart Home Network Anomaly Detection System.

Provides packet capture, flow aggregation, and device observation
using Scapy for network traffic analysis.
"""

from collector.capture import PacketCapture, CaptureStats, InterfaceInfo
from collector.flow_builder import FlowBuilder, FlowRecord
from collector.device_observer import DeviceObserver, DeviceObservation

__all__ = [
    "PacketCapture",
    "CaptureStats",
    "InterfaceInfo",
    "FlowBuilder",
    "FlowRecord",
    "DeviceObserver",
    "DeviceObservation",
]
