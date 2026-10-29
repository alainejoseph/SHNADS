import React from 'react';
import { StatusBadge } from '../ui/StatusBadge';
import type { Flow } from '../../types';

interface FlowRowProps {
  flow: Flow;
}

export const FlowRow: React.FC<FlowRowProps> = ({ flow }) => {
  const formatTime = (ts: string | number) => {
    if (!ts) return '—';
    const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts);
    return isNaN(d.getTime())
      ? String(ts)
      : d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true, timeZone: 'Asia/Kolkata' });
  };

  const formatBytes = (bytes: number) => {
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(2)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  return (
    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors font-mono">
      <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400 font-sans text-xs">{formatTime(flow.timestamp)}</td>
      <td className="py-2.5 px-3">
        <StatusBadge status={flow.protocol} type="protocol" />
      </td>
      <td className="py-2.5 px-3 text-slate-900 dark:text-slate-200">
        {flow.src_ip}
        {flow.src_port ? <span className="text-slate-500">:{flow.src_port}</span> : ''}
      </td>
      <td className="py-2.5 px-3 text-slate-900 dark:text-slate-200">
        {flow.dst_ip}
        {flow.dst_port ? <span className="text-slate-500">:{flow.dst_port}</span> : ''}
      </td>
      <td className="py-2.5 px-3 text-right font-bold text-slate-900 dark:text-slate-100">{flow.packet_count}</td>
      <td className="py-2.5 px-3 text-right text-slate-700 dark:text-slate-300">{formatBytes(flow.byte_count)}</td>
      <td className="py-2.5 px-3 text-right text-slate-600 dark:text-slate-400">{flow.duration_seconds.toFixed(2)}s</td>
      <td className="py-2.5 px-3 font-sans">
        {flow.tcp_flags_summary ? (
          <span className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] border border-slate-200 dark:bg-slate-800/90 dark:text-slate-300 dark:border-slate-700/60">
            {flow.tcp_flags_summary}
          </span>
        ) : (
          <span className="text-slate-400 dark:text-slate-600">—</span>
        )}
      </td>
    </tr>
  );
};

