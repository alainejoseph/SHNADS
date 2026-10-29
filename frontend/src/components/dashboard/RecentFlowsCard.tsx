import React from 'react';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/StatusBadge';
import type { Flow } from '../../types';

interface RecentFlowsCardProps {
  flows?: Flow[];
}

export const RecentFlowsCard: React.FC<RecentFlowsCardProps> = ({ flows = [] }) => {
  const flowList = flows || [];

  return (
    <Card title="Recent Observed Flows">
      {flowList.length === 0 ? (
        <p className="text-xs text-slate-500 py-6 text-center">No network flows recorded yet</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-medium">
                <th className="py-2.5 px-3">Protocol</th>
                <th className="py-2.5 px-3">Source</th>
                <th className="py-2.5 px-3">Destination</th>
                <th className="py-2.5 px-3 text-right">Packets</th>
                <th className="py-2.5 px-3 text-right">Bytes</th>
                <th className="py-2.5 px-3 text-right">Duration</th>
                <th className="py-2.5 px-3">TCP Flags</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {flowList.slice(0, 8).map((f, i) => (
                <tr key={f._id || i} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 px-3">
                    <StatusBadge status={f.protocol} type="protocol" />
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">
                    {f.src_ip}
                    {f.src_port ? <span className="text-slate-500">:{f.src_port}</span> : ''}
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">
                    {f.dst_ip}
                    {f.dst_port ? <span className="text-slate-500">:{f.dst_port}</span> : ''}
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300 font-bold">{f.packet_count}</td>
                  <td className="py-2.5 px-3 text-right text-slate-400">
                    {f.byte_count >= 1024
                      ? `${(f.byte_count / 1024).toFixed(1)} KB`
                      : `${f.byte_count} B`}
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-400">
                    {f.duration_seconds.toFixed(2)}s
                  </td>
                  <td className="py-2.5 px-3 text-slate-400 font-sans">
                    {f.tcp_flags_summary ? (
                      <span className="px-1.5 py-0.5 bg-slate-800 text-slate-300 rounded text-[10px]">
                        {f.tcp_flags_summary}
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
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

