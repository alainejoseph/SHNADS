import React, { useState, useEffect, useCallback } from 'react';
import { CaptureControls } from '../components/capture/CaptureControls';
import { CaptureStats } from '../components/capture/CaptureStats';
import { SessionHistory } from '../components/capture/SessionHistory';
import { FlowTable } from '../components/flows/FlowTable';
import { Card } from '../components/ui/Card';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { usePolling } from '../hooks/usePolling';
import {
  getCaptureStatus,
  startCapture,
  stopCapture,
  getCaptureSessions,
  getFlows,
} from '../services/api';
import type { CaptureSession, Flow } from '../types';

export const LiveMonitorPage: React.FC = () => {
  // Capture status polling
  const {
    data: status,
    error: statusError,
    refresh: refreshStatus,
  } = usePolling(getCaptureStatus, { intervalMs: 2500 });

  const isRunning = status?.is_running ?? false;

  // Live flows during capture
  const [liveFlows, setLiveFlows] = useState<Flow[]>([]);
  const [flowsLoading, setFlowsLoading] = useState(false);

  // Sessions history
  const [sessions, setSessions] = useState<CaptureSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const [actionError, setActionError] = useState<string | null>(null);

  const fetchLiveFlows = useCallback(async () => {
    try {
      const res = await getFlows({ limit: 15 });
      setLiveFlows(res.flows || res.items || []);
    } catch {
      // Ignore background poll errors
    } finally {
      setFlowsLoading(false);
    }
  }, []);

  const fetchSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const res = await getCaptureSessions({ limit: 10 });
      setSessions(res.sessions || res.items || []);
    } catch {
      // Ignore background poll errors
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(() => {
    fetchLiveFlows();
    const interval = setInterval(fetchLiveFlows, isRunning ? 2000 : 8000);
    return () => clearInterval(interval);
  }, [fetchLiveFlows, isRunning]);

  const handleStartCapture = async (iface: string) => {
    setActionError(null);
    try {
      await startCapture(iface);
      await refreshStatus();
      await fetchSessions();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to start packet capture');
    }
  };

  const handleStopCapture = async () => {
    setActionError(null);
    try {
      await stopCapture();
      await refreshStatus();
      await fetchSessions();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to stop packet capture');
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-slate-800/80 pb-4">
        <h2 className="text-xl font-bold text-slate-100 tracking-tight">Live Network Monitor</h2>
      </div>

      {(statusError || actionError) && (
        <ErrorMessage
          message={actionError || statusError || 'An error occurred'}
          onRetry={refreshStatus}
        />
      )}

      {/* Capture Controls */}
      <CaptureControls
        status={status}
        onStart={handleStartCapture}
        onStop={handleStopCapture}
      />

      {/* Real-time counters */}
      <CaptureStats
        session={status?.current_session ?? null}
        isRunning={isRunning}
      />

      {/* Recent live flow activity */}
      <Card title="Real-Time Flow Activity (Last 15 Summaries)">
        <FlowTable flows={liveFlows} loading={flowsLoading} />
      </Card>

      {/* Session History */}
      <SessionHistory sessions={sessions} loading={sessionsLoading} />
    </div>
  );
};
