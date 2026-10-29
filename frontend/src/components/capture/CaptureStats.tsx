import React from 'react';
import { Activity, ShieldCheck, Clock, Hash } from 'lucide-react';
import type { CaptureSession } from '../../types';

interface CaptureStatsProps {
  session: CaptureSession | null;
  isRunning: boolean;
}

export const CaptureStats: React.FC<CaptureStatsProps> = ({ session, isRunning }) => {
  if (!isRunning && !session) {
    return null;
  }

  const calculateDuration = () => {
    if (!session?.started_at) return '0s';
    const start = new Date(session.started_at).getTime();
    const end = session.stopped_at ? new Date(session.stopped_at).getTime() : Date.now();
    const diffSec = Math.max(0, Math.floor((end - start) / 1000));
    const mins = Math.floor(diffSec / 60);
    const secs = diffSec % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const statItems = [
    {
      label: 'Packets Observed',
      value: session?.packets_seen.toLocaleString() || '0',
      icon: Activity,
      color: 'text-blue-400',
    },
    {
      label: 'Flows Generated',
      value: session?.flows_created.toLocaleString() || '0',
      icon: Hash,
      color: 'text-emerald-400',
    },
    {
      label: 'Session Duration',
      value: calculateDuration(),
      icon: Clock,
      color: 'text-amber-400',
    },
    {
      label: 'Session State',
      value: session?.status?.toUpperCase() || (isRunning ? 'RUNNING' : 'IDLE'),
      icon: ShieldCheck,
      color: isRunning ? 'text-emerald-400' : 'text-slate-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statItems.map((item, i) => {
        const Icon = item.icon;
        return (
          <div
            key={i}
            className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center space-x-3.5"
          >
            <div className={`p-2.5 rounded-lg bg-slate-800/80 ${item.color}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium">{item.label}</p>
              <p className="text-base font-bold text-slate-100 font-mono mt-0.5">{item.value}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

