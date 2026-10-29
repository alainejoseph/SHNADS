# Architecture & Design Document (40% Milestone)

**Project:** Smart Home Network Anomaly Detection System  
**Dataset:** N-BaIoT  
**Milestone:** 40% Foundation Platform  

---

## 1. System Overview

The 40% milestone establishes the end-to-end data acquisition, flow aggregation, persistence, API, and visualization foundation for the Smart Home Network Anomaly Detection System.

```
+-------------------------------------------------------------+
|                Authorized Home/Lab Network                  |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             Collector: Scapy Packet Sniffer                 |
|  - Minimal privileges (metadata only, no payload storage)   |
|  - Asynchronous background capture thread                   |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             Collector: Flow Builder & Observer              |
|  - Bidirectional canonical 5-tuple flow aggregation         |
|  - Idle timeouts (30s) & max duration expirations (120s)     |
|  - Passive device endpoint discovery & TCP flags analysis   |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     FastAPI Backend                         |
|  - RESTful endpoints for capture control, devices, flows    |
|  - Non-blocking async operations via Motor MongoDB driver   |
|  - Centralized error formatting & CORS protection           |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                  MongoDB Community Edition                  |
|  - Collections: devices, flows, capture_sessions, alerts    |
|  - Indexed on timestamps, endpoints, session IDs, keys      |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                    React + Vite Dashboard                   |
|  - Live monitor with interface selection & start/stop       |
|  - Observed device inventory with filter & ARP scan trigger |
|  - Real-time traffic summaries, protocol charts & timeline  |
+-------------------------------------------------------------+
```

---

## 2. Core Components

### 2.1 Collector Service (`collector/capture.py`)
- Uses Scapy's `AsyncSniffer` to run packet capture in a non-blocking background thread.
- Restricts collection to approved interfaces and extracts **metadata only**:
  - Timestamps, source/destination IP, source/destination ports, protocol (TCP, UDP, ICMP, ARP), packet length, and TCP control flags (SYN, ACK, FIN, RST, PSH, URG).
  - Explicitly avoids capturing or storing application payload data to protect user privacy.

### 2.2 Flow Aggregation Engine (`collector/flow_builder.py`)
- Aggregates packets into bidirectional flow sessions using a canonical flow key:
  `min(src_ip:port, dst_ip:port) <-> max(...) + protocol`.
- Manages flow lifecycle:
  - **Idle timeout:** Finalizes and flushes flows with no activity for > 30 seconds.
  - **Maximum duration:** Flushes flows active for > 120 seconds.
  - **TCP termination:** Flushes TCP sessions upon observing FIN, FIN-ACK, or RST flags.
  - **Resource bounds:** Imposes active flow count bounds to prevent memory bloat.

### 2.3 Device Observation (`collector/device_observer.py`)
- Passively monitors endpoints from observed flows to maintain a device inventory.
- Provides optional active ARP discovery (`srp`) within the local subnet to enumerate connected hosts and MAC addresses.
- Accurately tracks `first_seen`, `last_seen`, and observation method (`passive_capture` vs `arp_discovery`).

### 2.4 FastAPI Backend (`backend/app/`)
- Exposes API routes configured via environment variables.
- Asynchronously interacts with MongoDB using `motor`.
- Coordinates capture lifecycle through `CaptureService`.

### 2.5 React Web Dashboard (`frontend/src/`)
- Built with React 19, Vite, TypeScript, and Tailwind CSS.
- Organised into four primary views:
  1. **Overview:** System statistics, active session state, protocol distributions, and traffic timeline.
  2. **Devices:** Filterable, paginated inventory of discovered devices with IP, MAC, hostname, and last-seen timestamps.
  3. **Live Monitor:** Interface selector, capture start/stop controls, real-time counters, and recent session history.
  4. **Flows:** Paginated flow explorer with protocol and IP filtering.

---

## 3. Explicit Milestone Boundaries

- **No Machine Learning in 40% Milestone:** Machine learning inference (Autoencoders, Random Forest, SHAP, and N-BaIoT feature mapping) is deferred to subsequent milestones.
- **Terminology:** All records are labeled as "observed flows" or "observed devices", never as "ML-detected anomalies" or "attacks".

