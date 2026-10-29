"""Unit tests for PacketCapture service."""

import unittest
from collector.capture import PacketCapture, CaptureStats, InterfaceInfo


class TestPacketCapture(unittest.TestCase):
    def test_capture_stats_tracking(self):
        stats = CaptureStats()
        self.assertEqual(stats.packets_captured, 0)

        stats.record_packet(150, "TCP")
        stats.record_packet(200, "TCP")
        stats.record_packet(80, "UDP")
        stats.record_drop()
        stats.record_error()

        self.assertEqual(stats.packets_captured, 3)
        self.assertEqual(stats.bytes_captured, 430)
        self.assertEqual(stats.protocols["TCP"], 2)
        self.assertEqual(stats.protocols["UDP"], 1)
        self.assertEqual(stats.packets_dropped, 1)
        self.assertEqual(stats.errors, 1)

        copy_stats = stats.copy()
        self.assertEqual(copy_stats.packets_captured, 3)
        self.assertEqual(copy_stats.bytes_captured, 430)

    def test_packet_capture_initial_state(self):
        capture = PacketCapture()
        self.assertFalse(capture.is_running)
        self.assertIsNone(capture.current_interface)
        self.assertEqual(capture.stats.packets_captured, 0)

    def test_interface_enumeration(self):
        interfaces = PacketCapture.list_interfaces()
        self.assertIsInstance(interfaces, list)
        names = [iface.name for iface in interfaces]
        self.assertGreater(len(names), 0)

    def test_start_invalid_interface(self):
        capture = PacketCapture()
        with self.assertRaises((ValueError, RuntimeError)):
            capture.start("non_existent_dummy_iface_9999", lambda p: None)

    def test_metadata_extraction_fallback(self):
        capture = PacketCapture()
        res = capture._extract_packet_metadata(None)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
