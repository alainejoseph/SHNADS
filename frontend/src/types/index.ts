export interface Device {
  device_key: string;
  ip_address: string;
  mac_address: string | null;
  hostname: string | null;
  first_seen: string | number;
  last_seen: string | number;
  source: string;
  metadata?: Record<string, unknown>;
}

export interface Flow {
  _id?: string;
  flow_key?: string;
  timestamp: string | number;
  src_ip: string;
  dst_ip: string;
  src_port: number | null;
  dst_port: number | null;
  protocol: string;
  packet_count: number;
  byte_count: number;
  duration_seconds: number;
  tcp_flags_summary: string | null;
  interface: string;
  capture_session_id: string;
}

export interface CaptureSession {
  session_id: string;
  interface: string;
  started_at: string;
  stopped_at: string | null;
  status: 'starting' | 'running' | 'stopping' | 'stopped' | 'error';
  packets_seen: number;
  flows_created: number;
  last_error: string | null;
}

export interface InterfaceInfo {
  name: string;
  addresses: string[];
  mac_address: string | null;
  is_up: boolean;
  is_loopback: boolean;
  description: string;
}

export interface CaptureStatus {
  is_running: boolean;
  current_session: CaptureSession | null;
  available_interfaces: InterfaceInfo[];
}

export interface DashboardSummary {
  total_devices: number;
  total_flows: number;
  total_sessions: number;
  active_capture: boolean;
  current_session: CaptureSession | null;
  recent_flows: Flow[];
  protocol_distribution: Array<{ protocol: string; count: number }>;
  traffic_timeline: Array<{ hour: string; count: number }>;
}

export interface PaginatedResponse<T> {
  items?: T[];
  devices?: T[];
  flows?: T[];
  sessions?: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface HealthStatus {
  status: string;
  database: string;
  timestamp: string;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}

export interface DiscoveryResponse {
  status: string;
  message: string;
  devices_found?: number;
}

