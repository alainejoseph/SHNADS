import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'status' | 'protocol';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'status' }) => {
  const norm = (status || '').toLowerCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  if (type === 'protocol') {
    switch (norm) {
      case 'tcp':
        colorClasses = 'bg-blue-950/70 text-blue-400 border-blue-800/60';
        break;
      case 'udp':
        colorClasses = 'bg-emerald-950/70 text-emerald-400 border-emerald-800/60';
        break;
      case 'icmp':
        colorClasses = 'bg-amber-950/70 text-amber-400 border-amber-800/60';
        break;
      case 'arp':
        colorClasses = 'bg-purple-950/70 text-purple-400 border-purple-800/60';
        break;
      case 'http':
        colorClasses = 'bg-cyan-950/70 text-cyan-400 border-cyan-800/60';
        break;
      case 'https':
        colorClasses = 'bg-sky-950/70 text-sky-400 border-sky-800/60';
        break;
      default:
        colorClasses = 'bg-slate-800 text-slate-400 border-slate-700';
    }
  } else {
    switch (norm) {
      case 'running':
      case 'active':
      case 'healthy':
      case 'connected':
        colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60';
        break;
      case 'starting':
      case 'stopping':
        colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-700/60';
        break;
      case 'stopped':
      case 'disconnected':
        colorClasses = 'bg-slate-800/90 text-slate-400 border-slate-700';
        break;
      case 'error':
      case 'unhealthy':
        colorClasses = 'bg-rose-950/80 text-rose-300 border-rose-700/60';
        break;
      default:
        colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
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

