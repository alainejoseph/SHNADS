# Frontend & Backend Report - Smart Home Network Anomaly Detection

Generated: $(date)

## Backend (FastAPI)

### Structure
- **Entry**: `backend/app/main.py` - FastAPI app with lifespan, CORS, routers
- **Config**: `backend/app/config.py` - Environment/settings
- **API Routes**: `backend/app/api/routes/`
  - `health.py` - Health check
  - `dashboard.py` - Dashboard summary (counts, protocol distribution, timeline, recent flows)
  - `devices.py` - Device inventory, discovery
  - `flows.py` - Flow listing with filters/pagination
  - `capture.py` - Capture start/stop/status/sessions
- **Services**: `backend/app/services/`
  - `capture_service.py` - Manages capture lifecycle, integrates collector
  - `flow_service.py` - Flow storage/aggregation
  - `device_service.py` - Device tracking
  - `discovery_service.py` - ARP discovery
- **Schemas/Models**: `backend/app/schemas/`, `backend/app/models/` - Pydantic/MongoDB models
- **DB**: `backend/app/db/mongodb.py`, `backend/app/db/indexes.py`

### Key Features
- RESTful API with async endpoints
- MongoDB integration via Motor
- Protocol distribution aggregation (normalized HTTP/HTTPS)
- Flow filtering by IP, protocol, session, date/time range
- UTC timestamp normalization in responses
- Capture session management
- CORS configured for frontend

### API Endpoints (main)
- `GET /health`
- `GET /api/dashboard/summary`
- `GET /api/devices` (with pagination/search)
- `POST /api/devices/discover`
- `GET /api/flows` (filters: src_ip, dst_ip, protocol, session_id, start_time, end_time)
- `GET /api/capture/status`, `POST /api/capture/start`, `POST /api/capture/stop`, `GET /api/capture/sessions`

## Frontend (React + TypeScript + Vite)

### Structure
- **Entry**: `frontend/src/main.tsx`, `frontend/src/App.tsx`
- **Pages**: `frontend/src/pages/`
  - `OverviewPage.tsx` - Dashboard overview
  - `DevicesPage.tsx` - Device inventory
  - `FlowsPage.tsx` - Flow explorer with filters
  - `LiveMonitorPage.tsx` - Live capture control
- **Components**: `frontend/src/components/`
  - `dashboard/` - StatsCards, ProtocolChart, TrafficTimeline, RecentFlowsCard, CaptureStatusCard
  - `flows/` - FlowTable, FlowRow, FlowFilters
  - `devices/` - DeviceTable, DeviceRow
  - `capture/` - CaptureControls, SessionHistory, CaptureStats
  - `ui/` - Reusable UI components
- **Services**: `frontend/src/services/api.ts` - Axios API client
- **Types**: `frontend/src/types/index.ts` - TypeScript interfaces
- **Utils**: `frontend/src/utils/time.ts` - IST timezone formatting

### Key Features
- Real-time dashboard with polling
- Protocol distribution chart (handles array/object shapes)
- Traffic timeline visualization
- Flow explorer with IP/protocol/date-time filters and calendar pickers
- IST timezone formatting for all timestamps
- HTTP/HTTPS protocol badges/colors
- Responsive dark theme UI
- Pagination support

### Tech Stack
- React 19, TypeScript, Vite 6
- Tailwind CSS
- Axios, React Router
- Lucide React icons

## Integration
- Frontend calls backend via `/api/*` endpoints
- Backend serves API on port 8000, frontend dev on port 5173
- MongoDB for persistence
- Collector feeds flows to backend via service integration

## Recent Updates
- Fixed protocol distribution data handling
- Added IST timezone conversion
- Added HTTP/HTTPS classification
- Added date/time filtering to flows
- Fixed timestamp serialization (UTC with Z)
- Improved capture service initialization

## Frontend Theme Report

### Theme System
- **Base Theme**: Dark mode (slate color palette)
- **Primary Colors**: Slate backgrounds (`bg-slate-950`, `bg-slate-900`), cyan/blue accents
- **Typography**: System fonts, monospace for IPs/ports/timestamps
- **Components**: Card-based layout with borders, rounded corners, subtle shadows

### Color Palette
- Background: `slate-950` (main), `slate-900` (cards), `slate-800` (borders)
- Text: `slate-100` (primary), `slate-300/400` (secondary), `slate-500/600` (muted)
- Accents: Cyan (`cyan-400/500`), Blue (`blue-400/500`), Emerald (`emerald-400/500`)
- Protocol Colors: TCP (blue), UDP (emerald), ICMP (amber), ARP (purple), HTTP (cyan), HTTPS (sky)
- Status: Running/Active (emerald), Starting (amber), Stopped (slate), Error (rose)

### UI Patterns
- Cards with `rounded-xl`, `border border-slate-800`
- Hover states with `hover:bg-slate-800/30`
- Transitions on interactive elements
- Badges for status/protocol
- Tables with striped/divided rows
- Loading spinners and empty states
- Consistent spacing (gap-3, gap-4, gap-6)

### Responsive Design
- Grid layouts adapt to screen sizes (md:, lg: breakpoints)
- Tables scroll horizontally on mobile
- Filters stack vertically on small screens
