import axios from 'axios';
import type {
  HealthStatus,
  DashboardSummary,
  Device,
  Flow,
  CaptureStatus,
  CaptureSession,
  PaginatedResponse,
  DiscoveryResponse,
} from '../types';

const apiClient = axios.create({
  baseURL: '',
  timeout: 10000,
});

// Health
export const getHealth = async (): Promise<HealthStatus> => {
  const res = await apiClient.get<HealthStatus>('/health');
  return res.data;
};

// Dashboard
export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const res = await apiClient.get<DashboardSummary>('/api/dashboard/summary');
  return res.data;
};

// Devices
export const getDevices = async (params?: {
  skip?: number;
  limit?: number;
  search?: string;
}): Promise<PaginatedResponse<Device>> => {
  const res = await apiClient.get<PaginatedResponse<Device>>('/api/devices', { params });
  return res.data;
};

export const discoverDevices = async (iface?: string): Promise<DiscoveryResponse> => {
  const res = await apiClient.post<DiscoveryResponse>(
    '/api/discovery/arp',
    iface ? { interface: iface } : null,
    { params: iface ? { interface: iface } : {}, timeout: 40000 }
  );
  return res.data;
};

// Flows
export const getFlows = async (params?: {
  skip?: number;
  limit?: number;
  src_ip?: string;
  dst_ip?: string;
  protocol?: string;
  session_id?: string;
  start_time?: string;
  end_time?: string;
}): Promise<PaginatedResponse<Flow>> => {
  const res = await apiClient.get<PaginatedResponse<Flow>>('/api/flows', { params });
  return res.data;
};

// Capture
export const getCaptureStatus = async (): Promise<CaptureStatus> => {
  const res = await apiClient.get<CaptureStatus>('/api/capture/status');
  return res.data;
};

export const startCapture = async (interfaceName: string): Promise<CaptureSession> => {
  const res = await apiClient.post<CaptureSession>('/api/capture/start', {
    interface: interfaceName,
  });
  return res.data;
};

export const stopCapture = async (): Promise<CaptureSession> => {
  const res = await apiClient.post<CaptureSession>('/api/capture/stop');
  return res.data;
};

export const getCaptureSessions = async (params?: {
  skip?: number;
  limit?: number;
}): Promise<PaginatedResponse<CaptureSession>> => {
  const res = await apiClient.get<PaginatedResponse<CaptureSession>>('/api/capture/sessions', {
    params,
  });
  return res.data;
};

