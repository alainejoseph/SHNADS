import React from 'react';
import { StatsCards } from '../components/dashboard/StatsCards';
import { CaptureStatusCard } from '../components/dashboard/CaptureStatusCard';
import { ProtocolChart } from '../components/dashboard/ProtocolChart';
import { TrafficTimeline } from '../components/dashboard/TrafficTimeline';
import { RecentFlowsCard } from '../components/dashboard/RecentFlowsCard';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { usePolling } from '../hooks/usePolling';
import { getDashboardSummary } from '../services/api';

export const OverviewPage: React.FC = () => {
  const { data: summary, loading, error, refresh } = usePolling(getDashboardSummary, {
    intervalMs: 4000,
  });

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">System Overview</h2>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={refresh} />}

      {loading && !summary ? (
        <LoadingSpinner message="Connecting to monitoring backend..." />
      ) : (
        <>
          {/* Stat Cards */}
          <StatsCards summary={summary} />

          {/* Active Capture Banner */}
          <CaptureStatusCard
            session={summary?.current_session ?? null}
            isRunning={summary?.active_capture ?? false}
          />

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ProtocolChart distribution={summary?.protocol_distribution} />
            <TrafficTimeline timeline={summary?.traffic_timeline} />
          </div>

          {/* Recent Flows Table */}
          <RecentFlowsCard flows={summary?.recent_flows ?? []} />
        </>
      )}
    </div>
  );
};

