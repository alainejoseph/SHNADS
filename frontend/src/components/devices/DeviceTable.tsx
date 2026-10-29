import React from 'react';
import { DeviceRow } from './DeviceRow';
import { EmptyState } from '../ui/EmptyState';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { Laptop } from 'lucide-react';
import type { Device } from '../../types';

interface DeviceTableProps {
  devices?: Device[];
  loading: boolean;
}

export const DeviceTable: React.FC<DeviceTableProps> = ({ devices = [], loading }) => {
  if (loading) {
    return <LoadingSpinner message="Fetching observed devices..." />;
  }

  const deviceList = devices || [];

  if (deviceList.length === 0) {
    return (
      <EmptyState
        icon={<Laptop className="w-6 h-6 text-slate-400" />}
        title="No devices detected yet"
        description="Start a live capture session or run ARP discovery to populate device endpoints."
      />
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-950/40">
            <th className="py-3 px-4">IP Address</th>
            <th className="py-3 px-4">MAC Address</th>
            <th className="py-3 px-4">Hostname</th>
            <th className="py-3 px-4">Discovery Source</th>
            <th className="py-3 px-4">First Observed</th>
            <th className="py-3 px-4">Last Seen</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {deviceList.map((device) => (
            <DeviceRow key={device.device_key} device={device} />
          ))}
        </tbody>
      </table>
    </div>
  );
};

