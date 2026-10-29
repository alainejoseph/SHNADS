import React from 'react';
import { Radio, AlertCircle, Clock, Zap } from 'lucide-react';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/StatusBadge';
import type { CaptureSession } from '../../types';

interface CaptureStatusCardProps {
  session: CaptureSession | null;
  isRunning: boolean;
}

export const CaptureStatusCard: React.FC<CaptureStatusCardProps> = ({ session, isRunning }) => {
  return (
    <Card title="Packet Capture Status">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-2">
        <div className="flex items-start space-x-4">
          <div
            className={`p-3 rounded-xl border ${
              isRunning
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800/60'
                : 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800/40 dark:text-slate-400 dark:border-slate-700/60'
            }`}
          >
            <Radio className={`w-6 h-6 ${isRunning ? 'animate-pulse text-emerald-700 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400'}`} />
          </div>
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <h4 className="text-base font-semibold text-slate-900 dark:text-slate-200">
                {isRunning ? 'Active Live Capture' : 'Capture Inactive'}
              </h4>
              <StatusBadge status={isRunning ? 'running' : 'stopped'} />
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {isRunning
                ? `Actively listening on network interface: ${session?.interface ?? 'unknown'}`
                : 'No capture worker currently running. Start one from Live Monitor.'}
            </p>
          </div>
        </div>

        {isRunning && session && (
          <div className="flex items-center space-x-6 bg-slate-50 border border-slate-200 dark:bg-slate-950/60 dark:border-slate-800/80 rounded-xl px-4 py-2.5">
            <div>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Packets</span>
              <span className="text-sm font-bold text-slate-900 dark:text-slate-200 font-mono flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-blue-700 dark:text-blue-400" />
                {session.packets_seen.toLocaleString()}
              </span>
            </div>
            <div className="h-6 w-px bg-slate-200 dark:bg-slate-800" />
            <div>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Flows</span>
              <span className="text-sm font-bold text-slate-900 dark:text-slate-200 font-mono">
                {session.flows_created.toLocaleString()}
              </span>
            </div>
            <div className="h-6 w-px bg-slate-200 dark:bg-slate-800" />
            <div>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Started</span>
              <span className="text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-500 dark:text-slate-400" />
                {new Date(session.started_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true, timeZone: 'Asia/Kolkata' })}
              </span>
            </div>
          </div>
        )}

        {session?.last_error && (
          <div className="flex items-center space-x-2 text-rose-700 dark:text-rose-400 text-xs bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 px-3 py-2 rounded-lg">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Error: {session.last_error}</span>
          </div>
        )}
      </div>
    </Card>
  );
};

