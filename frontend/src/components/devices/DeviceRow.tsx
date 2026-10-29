import React from 'react';
import type { Device } from '../../types';

interface DeviceRowProps {
  device: Device;
}

export const DeviceRow: React.FC<DeviceRowProps> = ({ device }) => {
  const formatDate = (val: string | number) => {
    if (!val) return '—';
    const d = typeof val === 'number' ? new Date(val * 1000) : new Date(val);
    return isNaN(d.getTime())
      ? String(val)
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

  const getSourceBadge = (source: string) => {
    switch (source) {
      case 'arp_discovery':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-950/70 dark:text-purple-300 dark:border-purple-800/60">
            ARP Scan
          </span>
        );
      case 'passive_capture':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/70 dark:text-blue-300 dark:border-blue-800/60">
            Passive Flow
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700">
            {source}
          </span>
        );
    }
  };

  return (
    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
      <td className="py-3 px-4 font-mono font-medium text-slate-900 dark:text-slate-200">{device.ip_address}</td>
      <td className="py-3 px-4 font-mono text-slate-700 dark:text-slate-300">
        {device.mac_address || <span className="text-slate-500 italic">Not observed (routed)</span>}
      </td>
      <td className="py-3 px-4 text-slate-700 dark:text-slate-300">
        {device.hostname || <span className="text-slate-400 dark:text-slate-600">—</span>}
      </td>
      <td className="py-3 px-4">{getSourceBadge(device.source)}</td>
      <td className="py-3 px-4 text-slate-600 dark:text-slate-400 text-xs">{formatDate(device.first_seen)}</td>
      <td className="py-3 px-4 text-slate-800 dark:text-slate-300 text-xs font-medium">{formatDate(device.last_seen)}</td>
    </tr>
  );
};

