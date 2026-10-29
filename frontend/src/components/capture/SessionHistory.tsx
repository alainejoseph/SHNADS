import React from 'react';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/StatusBadge';
import { EmptyState } from '../ui/EmptyState';
import { Layers } from 'lucide-react';
import type { CaptureSession } from '../../types';

interface SessionHistoryProps {
  sessions?: CaptureSession[];
  loading: boolean;
}

export const SessionHistory: React.FC<SessionHistoryProps> = ({ sessions = [], loading }) => {
  const sessionList = sessions || [];

  const formatDate = (val: string | null) => {
    if (!val) return '—';
    const d = new Date(val);
    return isNaN(d.getTime())
      ? val
      : d.toLocaleString('en-IN', {
          timeZone: 'Asia/Kolkata',
          day: '2-digit',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        });
  };

  return (
    <Card title="Past Capture Sessions">
      {sessionList.length === 0 && !loading ? (
        <EmptyState
          icon={<Layers className="w-5 h-5 text-slate-400" />}
          title="No previous sessions"
          description="Start a capture session above to record network traffic."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-medium">
                <th className="py-2.5 px-3">Session ID</th>
                <th className="py-2.5 px-3">Interface</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Packets</th>
                <th className="py-2.5 px-3 text-right">Flows</th>
                <th className="py-2.5 px-3">Started At</th>
                <th className="py-2.5 px-3">Stopped At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {sessionList.map((s) => (
                <tr key={s.session_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                    {s.session_id.substring(0, 8)}...
                  </td>
                  <td className="py-2.5 px-3 text-slate-200 font-semibold">{s.interface}</td>
                  <td className="py-2.5 px-3 font-sans">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300 font-bold">
                    {s.packets_seen.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300 font-bold">
                    {s.flows_created.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 text-slate-400 font-sans text-[11px]">
                    {formatDate(s.started_at)}
                  </td>
                  <td className="py-2.5 px-3 text-slate-400 font-sans text-[11px]">
                    {formatDate(s.stopped_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};

