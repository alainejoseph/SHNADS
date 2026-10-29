import React, { useState, useEffect, useCallback } from 'react';
import { DeviceFilters } from '../components/devices/DeviceFilters';
import { DeviceTable } from '../components/devices/DeviceTable';
import { Pagination } from '../components/ui/Pagination';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { getDevices, discoverDevices } from '../services/api';
import type { Device } from '../types';
import { Info } from 'lucide-react';

export const DevicesPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [skip, setSkip] = useState(0);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const limit = 20;

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDevices({ skip, limit, search: search.trim() || undefined });
      const list = data.devices || data.items || [];
      setDevices(list);
      setTotal(data.total ?? list.length);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load devices');
    } finally {
      setLoading(false);
    }
  }, [skip, limit, search]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const handleDiscover = async () => {
    setIsDiscovering(true);
    try {
      await discoverDevices();
      // Wait a moment for ARP scan to complete then re-fetch
      setTimeout(() => {
        fetchDevices();
        setIsDiscovering(false);
      }, 3500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Discovery scan failed');
      setIsDiscovering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-slate-800/80 pb-4">
        <h2 className="text-xl font-bold text-slate-100 tracking-tight">Observed Devices Inventory</h2>
      </div>

      {/* Scope Disclaimer banner
      <div className="bg-blue-950/20 border border-blue-800/40 rounded-xl p-3.5 text-xs text-blue-300 flex items-start space-x-2.5">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Observation Boundary:</strong> Passive capture only detects devices that have actively sent or received packets. MAC addresses are only observable for devices on the immediate broadcast domain (layer 2).
        </p>
      </div> */}

      {error && <ErrorMessage message={error} onRetry={fetchDevices} />}

      {/* Search and Action Bar */}
      <DeviceFilters
        search={search}
        onSearchChange={(val) => {
          setSearch(val);
          setSkip(0);
        }}
        onDiscover={handleDiscover}
        onRefresh={fetchDevices}
        isDiscovering={isDiscovering}
      />

      {/* Devices Table */}
      <DeviceTable devices={devices} loading={loading} />

      {/* Pagination */}
      <Pagination
        total={total}
        skip={skip}
        limit={limit}
        onPageChange={(newSkip) => setSkip(newSkip)}
      />
    </div>
  );
};

