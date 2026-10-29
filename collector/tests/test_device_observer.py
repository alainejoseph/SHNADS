"""Unit tests for DeviceObserver."""

import unittest
from collector.device_observer import DeviceObservation, DeviceObserver


class TestDeviceObserver(unittest.TestCase):
    def test_device_observation_key(self):
        obs1 = DeviceObservation(ip_address="192.168.1.50", mac_address="AA:BB:CC:DD:EE:FF")
        self.assertEqual(obs1.device_key, "192.168.1.50_AA:BB:CC:DD:EE:FF")

        obs2 = DeviceObservation(ip_address="192.168.1.51")
        self.assertEqual(obs2.device_key, "192.168.1.51")

    def test_device_observer_passive_packet(self):
        observer = DeviceObserver()

        packet_meta = {
            "src_ip": "192.168.1.100",
            "src_mac": "00:11:22:33:44:55",
            "dst_ip": "192.168.1.1",
            "dst_mac": "66:77:88:99:AA:BB",
            "timestamp": 1000.0,
        }

        observer.observe_packet(packet_meta)
        devices = observer.get_observed_devices()

        self.assertEqual(len(devices), 2)
        ips = {d.ip_address for d in devices}
        self.assertIn("192.168.1.100", ips)
        self.assertIn("192.168.1.1", ips)

        # Check pending updates
        updates = observer.get_pending_updates()
        self.assertEqual(len(updates), 2)

        # Second fetch should be empty because it clears pending
        self.assertEqual(len(observer.get_pending_updates()), 0)

    def test_device_observer_packet_count_and_timing(self):
        observer = DeviceObserver()

        p1 = {
            "src_ip": "10.0.0.5",
            "src_mac": "11:22:33:44:55:66",
            "timestamp": 500.0,
        }
        p2 = {
            "src_ip": "10.0.0.5",
            "src_mac": "11:22:33:44:55:66",
            "timestamp": 505.0,
        }

        observer.observe_packet(p1)
        observer.observe_packet(p2)

        devices = observer.get_observed_devices()
        self.assertEqual(len(devices), 1)
        dev = devices[0]
        self.assertEqual(dev.packet_count, 2)
        self.assertEqual(dev.first_seen, 500.0)
        self.assertEqual(dev.last_seen, 505.0)


if __name__ == "__main__":
    unittest.main()
