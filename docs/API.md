# API Documentation (40% Foundation Platform)

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc`

---

## 1. System Health

### `GET /health`
Returns backend service and database connectivity health.
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-10-28T19:00:00Z"
}
```

---

## 2. Dashboard

### `GET /api/dashboard/summary`
Returns high-level statistics, current capture state, recent flows, protocol distributions, and activity timeline.
```json
{
  "total_devices": 12,
  "total_flows": 1420,
  "total_sessions": 3,
  "active_capture": true,
  "current_session": {
    "session_id": "c1f7b82e-...",
    "interface": "eth0",
    "started_at": "2026-10-28T18:50:00Z",
    "status": "running",
    "packets_seen": 4200,
    "flows_created": 310
  },
  "recent_flows": [...],
  "protocol_distribution": {
    "TCP": 950,
    "UDP": 420,
    "ICMP": 30,
    "ARP": 20
  },
  "traffic_timeline": [
    { "hour": "18:00", "count": 210 },
    { "hour": "19:00", "count": 1210 }
  ]
}
```

---

## 3. Devices

### `GET /api/devices`
List observed or discovered network devices with optional pagination and filtering.

**Query Parameters:**
- `skip` (integer, default: 0): Records to skip.
- `limit` (integer, default: 50): Max records to return.
- `search` (string, optional): Search query matching IP, MAC, or hostname.

**Response:**
```json
{
  "items": [
    {
      "device_key": "192.168.1.105_AA:BB:CC:DD:EE:05",
      "ip_address": "192.168.1.105",
      "mac_address": "AA:BB:CC:DD:EE:05",
      "hostname": "smart-cam-01",
      "first_seen": "2026-10-28T18:00:00Z",
      "last_seen": "2026-10-28T18:54:12Z",
      "source": "passive_capture",
      "metadata": { "packet_count": 52 }
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

### `POST /api/devices/discover`
Triggers an asynchronous local ARP discovery scan across the authorized network subnet.

**Request Body (optional):**
```json
{
  "interface": "eth0",
  "subnet": "192.168.1.0/24"
}
```

**Response:**
```json
{
  "status": "discovery_started",
  "message": "ARP discovery initiated on interface eth0"
}
```

---

## 4. Flows

### `GET /api/flows`
Returns paginated aggregated flow summaries with optional filters.

**Query Parameters:**
- `skip` (integer, default: 0)
- `limit` (integer, default: 50)
- `src_ip` (string, optional)
- `dst_ip` (string, optional)
- `protocol` (string, optional: TCP, UDP, ICMP, ARP)
- `session_id` (string, optional)

**Response:**
```json
{
  "items": [
    {
      "flow_key": "192.168.1.105:554_192.168.1.1:49152_TCP",
      "timestamp": "2026-10-28T18:50:00Z",
      "src_ip": "192.168.1.105",
      "dst_ip": "192.168.1.1",
      "src_port": 554,
      "dst_port": 49152,
      "protocol": "TCP",
      "packet_count": 482,
      "byte_count": 524288,
      "duration_seconds": 32.4,
      "tcp_flags_summary": "SYN,ACK,PSH",
      "interface": "eth0",
      "capture_session_id": "seed-session-001"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

---

## 5. Packet Capture Control

### `GET /api/capture/status`
Returns current capture status, active session details, and available network interfaces.
```json
{
  "is_running": true,
  "current_session": {
    "session_id": "c1f7b82e-...",
    "interface": "eth0",
    "started_at": "2026-10-28T18:50:00Z",
    "stopped_at": null,
    "status": "running",
    "packets_seen": 4200,
    "flows_created": 310,
    "last_error": null
  },
  "available_interfaces": [
    {
      "name": "eth0",
      "addresses": ["192.168.1.50"],
      "mac_address": "00:15:5D:...",
      "is_up": true,
      "is_loopback": false,
      "description": "Ethernet interface"
    }
  ]
}
```

### `POST /api/capture/start`
Starts packet capture on an authorized interface.
```json
{
  "interface": "eth0"
}
```
*Returns 409 Conflict if capture is already running; 422 Unprocessable Entity if interface does not exist or is unauthorized.*

### `POST /api/capture/stop`
Safely terminates the active packet capture worker, flushes pending flows to MongoDB, and returns final statistics.

*Returns 409 Conflict if no capture session is currently active.*

### `GET /api/capture/sessions`
Returns paginated list of past and active capture sessions.
```json
{
  "items": [...],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

