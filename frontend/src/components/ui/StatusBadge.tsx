import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'status' | 'protocol';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'status' }) => {
  const norm = (status || '').toLowerCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';

  if (type === 'protocol') {
    switch (norm) {
      case 'tcp':
        colorClasses = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/70 dark:text-blue-400 dark:border-blue-800/60';
        break;
      case 'udp':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/70 dark:text-emerald-400 dark:border-emerald-800/60';
        break;
      case 'icmp':
        colorClasses = 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/70 dark:text-amber-400 dark:border-amber-800/60';
        break;
      case 'arp':
        colorClasses = 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/70 dark:text-purple-400 dark:border-purple-800/60';
        break;
      case 'http':
        colorClasses = 'bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/70 dark:text-cyan-400 dark:border-cyan-800/60';
        break;
      case 'https':
        colorClasses = 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/70 dark:text-sky-400 dark:border-sky-800/60';
        break;
      default:
        colorClasses = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700';
    }
  } else {
    switch (norm) {
      case 'running':
      case 'active':
      case 'healthy':
      case 'connected':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-700/60';
        break;
      case 'starting':
      case 'stopping':
        colorClasses = 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-700/60';
        break;
      case 'stopped':
      case 'disconnected':
        colorClasses = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800/90 dark:text-slate-400 dark:border-slate-700';
        break;
      case 'error':
      case 'unhealthy':
        colorClasses = 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/80 dark:text-rose-300 dark:border-rose-700/60';
        break;
      default:
        colorClasses = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
    }
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClasses}`}
    >
      {type === 'status' && (
        <span
          className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
            norm === 'running' || norm === 'connected'
              ? 'bg-emerald-400 animate-pulse'
              : norm === 'error'
              ? 'bg-rose-400'
              : norm === 'starting' || norm === 'stopping'
              ? 'bg-amber-400 animate-bounce'
              : 'bg-slate-400'
          }`}
        />
      )}
      {status}
    </span>
  );
};

