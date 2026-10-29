# Test Plan & Verification Runbook (40% Milestone)

**Project:** Smart Home Network Anomaly Detection System  
**Dataset:** N-BaIoT  
**Milestone:** 40% Foundation Platform  

---

## 1. Overview of Test Suites

The test plan exercises the software platform across:
1. **Collector Layer Unit Tests (`collector/tests/`):** Validates packet metadata extraction, bidirectional flow aggregation, timeout expiration, TCP connection termination, and device observation.
2. **Backend API Tests (`backend/tests/`):** Validates FastAPI endpoints, routing, CORS headers, parameter validation, error mapping, pagination, and MongoDB persistence.
3. **Frontend Production Build Verification (`frontend/`):** Type-checks TypeScript code and verifies the Vite bundling pipeline.

---

## 2. Test Execution Commands

### 2.1 Running Collector Unit Tests
```bash
# Using pytest
PYTHONPATH=. .venv/bin/pytest collector/tests -v

# Or using Python's built-in unittest (zero external test dependencies)
python3 -m unittest discover -s collector/tests -v
```
**Expected Result:** 12 passed unit tests.

### 2.2 Running Backend API Integration Tests
```bash
PYTHONPATH=backend:. .venv/bin/pytest backend/tests -v
```
**Expected Result:** 19 passed API tests:
- `test_health.py` (2 tests)
- `test_devices.py` (4 tests)
- `test_flows.py` (4 tests)
- `test_capture.py` (6 tests)
- `test_dashboard.py` (3 tests)

### 2.3 Running Frontend TypeScript Check & Build
```bash
cd frontend
npm run build
```
**Expected Result:** Clean compilation with 0 TypeScript errors producing assets in `frontend/dist/`.

---

## 3. End-to-End Acceptance Test Procedure

Follow this runbook to demonstrate the system live:

### Step 1: Start MongoDB
Ensure MongoDB Community Edition is running on `localhost:27017`:
```bash
# On systems with systemd / service:
sudo systemctl start mongod
# Or run mongod directly:
mongod --dbpath /var/lib/mongodb
```

### Step 2: (Optional) Seed Initial Demo Records
To populate the database with realistic smart home IoT traffic and device endpoints:
```bash
python3 data/fixtures/seed_demo_data.py
```

### Step 3: Launch the FastAPI Backend
```bash
cd backend
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Verify the API is active:
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","database":"connected",...}
```

### Step 4: Launch the React Frontend
In a second terminal window:
```bash
cd frontend
npm run dev
```
Open your browser to `http://localhost:5173`.

### Step 5: Test Live Packet Capture & Traffic Flow
1. Navigate to **Live Monitor** (`/live`).
2. Review the detected interfaces in the dropdown.
3. Select an active interface (e.g. `eth0` or `lo` for loopback).
4. Click **Start Packet Capture**. The status indicator turns green (RUNNING).
5. Generate sample network traffic (e.g., browse a website or run `ping 8.8.8.8` / `curl https://example.com` in another terminal).
6. Watch packet counters and flow counts increase in real time.
7. Click **Stop Capture**. The session safely concludes and finalizes all active flows into MongoDB.
8. Navigate to **Overview** and **Flow History** to verify that all observed flows and devices have persisted.

