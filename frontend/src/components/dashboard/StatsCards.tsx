import React from 'react';
import { Laptop, Activity, Layers, Radio } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import type { DashboardSummary } from '../../types';

interface StatsCardsProps {
  summary: DashboardSummary | null;
}

export const StatsCards: React.FC<StatsCardsProps> = ({ summary }) => {
  const cards = [
    {
      label: 'Observed Devices',
      value: summary?.total_devices ?? 0,
      icon: Laptop,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      description: 'Active IP/MAC endpoints',
    },
    {
      label: 'Aggregated Flows',
      value: summary?.total_flows ?? 0,
      icon: Activity,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      description: 'Bidirectional sessions',
    },
    {
      label: 'Capture Sessions',
      value: summary?.total_sessions ?? 0,
      icon: Layers,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      description: 'Recorded capture runs',
    },
    {
      label: 'Collector Engine',
      value: summary?.active_capture ? 'RUNNING' : 'STOPPED',
      icon: Radio,
      color: summary?.active_capture
        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
        : 'text-slate-400 bg-slate-800/40 border-slate-700/40',
      isBadge: true,
      status: summary?.active_capture ? 'running' : 'stopped',
      description: summary?.current_session ? `Interface: ${summary.current_session.interface}` : 'Idle',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400">{c.label}</span>
              <div className={`p-2 rounded-lg border ${c.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div>
              {c.isBadge ? (
                <div className="py-1">
                  <StatusBadge status={c.status || 'stopped'} />
                </div>
              ) : (
                <div className="text-2xl font-bold text-slate-100 font-mono">
                  {typeof c.value === 'number' ? c.value.toLocaleString() : c.value}
                </div>
              )}
              <p className="text-[11px] text-slate-500 mt-1">{c.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

