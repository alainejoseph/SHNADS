import React from 'react';
import { FlowRow } from './FlowRow';
import { EmptyState } from '../ui/EmptyState';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { Activity } from 'lucide-react';
import type { Flow } from '../../types';

interface FlowTableProps {
  flows?: Flow[];
  loading: boolean;
}

export const FlowTable: React.FC<FlowTableProps> = ({ flows = [], loading }) => {
  if (loading) {
    return <LoadingSpinner message="Loading network flows..." />;
  }

  const flowList = flows || [];

  if (flowList.length === 0) {
    return (
      <EmptyState
        icon={<Activity className="w-6 h-6 text-slate-400" />}
        title="No flow records match query"
        description="Try adjusting your filter criteria or start capturing packets in Live Monitor."
      />
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-950/40">
            <th className="py-3 px-3">Time</th>
            <th className="py-3 px-3">Protocol</th>
            <th className="py-3 px-3">Source Endpoint</th>
            <th className="py-3 px-3">Destination Endpoint</th>
            <th className="py-3 px-3 text-right">Packets</th>
            <th className="py-3 px-3 text-right">Total Bytes</th>
            <th className="py-3 px-3 text-right">Duration</th>
            <th className="py-3 px-3">TCP Flags</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {flowList.map((flow, index) => (
            <FlowRow key={flow._id || flow.flow_key || index} flow={flow} />
          ))}
        </tbody>
      </table>
    </div>
  );
};

