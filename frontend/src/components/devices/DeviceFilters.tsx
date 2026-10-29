import React from 'react';
import { Search, Radar, RefreshCw } from 'lucide-react';

interface DeviceFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  onDiscover: () => void;
  onRefresh: () => void;
  isDiscovering: boolean;
}

export const DeviceFilters: React.FC<DeviceFiltersProps> = ({
  search,
  onSearchChange,
  onDiscover,
  onRefresh,
  isDiscovering,
}) => {
  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-4">
      <div className="relative flex-1 max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Filter by IP, MAC, or hostname..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full bg-white border border-slate-200 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:border-blue-500/60 dark:focus:ring-blue-500/60"
        />
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={onRefresh}
          className="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-800 dark:text-slate-300"
          title="Refresh list"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <button
          onClick={onDiscover}
          disabled={isDiscovering}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 disabled:opacity-50 transition cursor-pointer"
        >
          <Radar className={`w-4 h-4 ${isDiscovering ? 'animate-spin' : ''}`} />
          <span>{isDiscovering ? 'Scanning Subnet...' : 'Run ARP Discovery'}</span>
        </button>
      </div>
    </div>
  );
};

