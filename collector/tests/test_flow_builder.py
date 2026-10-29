"""Unit tests for FlowBuilder and FlowRecord."""

import unittest
from collector.flow_builder import FlowBuilder, FlowRecord


class TestFlowBuilder(unittest.TestCase):
    def test_flow_record_lifecycle(self):
        rec = FlowRecord(
            flow_key="10.0.0.1:80_10.0.0.2:45000_TCP",
            src_ip="10.0.0.1",
            dst_ip="10.0.0.2",
            src_port=80,
            dst_port=45000,
            protocol="TCP",
            interface="eth0",
            capture_session_id="test-session-123",
        )

        t0 = 1000.0
        rec.update({"length": 150, "timestamp": t0, "tcp_flags": "SYN"})
        rec.update({"length": 250, "timestamp": t0 + 2.5, "tcp_flags": "ACK"})
        rec.finalize()

        self.assertEqual(rec.packet_count, 2)
        self.assertEqual(rec.byte_count, 400)
        self.assertEqual(rec.duration_seconds, 2.5)
        self.assertIn("SYN", rec.tcp_flags)
        self.assertIn("ACK", rec.tcp_flags)
        self.assertIsNotNone(rec.tcp_flags_summary)
        data = rec.to_dict()
        self.assertEqual(data["packet_count"], 2)
        self.assertEqual(data["src_ip"], "10.0.0.1")

    def test_flow_builder_bidirectional_aggregation(self):
        fb = FlowBuilder(idle_timeout=10.0, max_duration=60.0)

        p1 = {
            "src_ip": "192.168.1.10",
            "dst_ip": "8.8.8.8",
            "src_port": 54321,
            "dst_port": 53,
            "protocol": "UDP",
            "length": 60,
            "timestamp": 100.0,
        }

        p2 = {
            "src_ip": "8.8.8.8",
            "dst_ip": "192.168.1.10",
            "src_port": 53,
            "dst_port": 54321,
            "protocol": "UDP",
            "length": 120,
            "timestamp": 100.1,
        }

        res1 = fb.process_packet(p1)
        self.assertIsNone(res1)
        self.assertEqual(fb.active_flow_count, 1)

        res2 = fb.process_packet(p2)
        self.assertIsNone(res2)
        self.assertEqual(fb.active_flow_count, 1)

        flushed = fb.flush()
        self.assertEqual(len(flushed), 1)
        flow = flushed[0]
        self.assertEqual(flow.packet_count, 2)
        self.assertEqual(flow.byte_count, 180)
        self.assertEqual(flow.protocol, "UDP")
        self.assertEqual(fb.active_flow_count, 0)

    def test_flow_builder_idle_timeout(self):
        fb = FlowBuilder(idle_timeout=5.0, max_duration=60.0)

        p1 = {
            "src_ip": "10.0.0.1",
            "dst_ip": "10.0.0.2",
            "src_port": 1234,
            "dst_port": 80,
            "protocol": "TCP",
            "length": 100,
            "timestamp": 100.0,
        }

        fb.process_packet(p1)
        self.assertEqual(fb.active_flow_count, 1)

        timeouts = fb.check_timeouts(now=104.0)
        self.assertEqual(len(timeouts), 0)

        timeouts = fb.check_timeouts(now=106.0)
        self.assertEqual(len(timeouts), 1)
        self.assertEqual(timeouts[0].packet_count, 1)
        self.assertEqual(fb.active_flow_count, 0)

    def test_flow_builder_tcp_termination(self):
        fb = FlowBuilder()

        p_syn = {
            "src_ip": "10.0.0.1",
            "dst_ip": "10.0.0.2",
            "src_port": 5000,
            "dst_port": 80,
            "protocol": "TCP",
            "length": 60,
            "tcp_flags": "SYN",
            "timestamp": 10.0,
        }
        p_fin = {
            "src_ip": "10.0.0.1",
            "dst_ip": "10.0.0.2",
            "src_port": 5000,
            "dst_port": 80,
            "protocol": "TCP",
            "length": 60,
            "tcp_flags": "FIN",
            "timestamp": 11.0,
        }

        fb.process_packet(p_syn)
        completed = fb.process_packet(p_fin)

        self.assertIsNotNone(completed)
        self.assertEqual(completed.packet_count, 2)
        self.assertEqual(completed.duration_seconds, 1.0)
        self.assertEqual(fb.active_flow_count, 0)


if __name__ == "__main__":
    unittest.main()
