import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { DeviceFilters } from '../components/devices/DeviceFilters';
import { DeviceTable } from '../components/devices/DeviceTable';
import { Pagination } from '../components/ui/Pagination';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { getDevices, discoverDevices } from '../services/api';
import type { Device } from '../types';

export const DevicesPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [discoveryNotification, setDiscoveryNotification] = useState<{
    type: 'success' | 'info';
    message: string;
  } | null>(null);
  const [search, setSearch] = useState('');
  const [skip, setSkip] = useState(0);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const discoveryInFlight = useRef(false);
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
      let message = 'Failed to load devices';
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.detail || err.response?.data?.message || err.message;
      } else if (err instanceof Error) {
        message = err.message;
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [skip, limit, search]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const handleDiscover = async () => {
    if (discoveryInFlight.current) return;
    discoveryInFlight.current = true;
    setIsDiscovering(true);
    setError(null);
    setDiscoveryNotification(null);
    try {
      const res = await discoverDevices();
      setDiscoveryNotification({
        type: 'success',
        message: res.message || `Discovery scan complete. Found ${res.devices_found ?? 0} device(s).`,
      });
      await fetchDevices();
    } catch (err: unknown) {
      let message = 'Discovery scan failed';
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.detail || err.response?.data?.message || err.message;
      } else if (err instanceof Error) {
        message = err.message;
      }
      setError(message);
    } finally {
      discoveryInFlight.current = false;
      setIsDiscovering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-slate-800/80 pb-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">Observed Devices Inventory</h2>
      </div>

      {discoveryNotification && (
        <div className="bg-emerald-950/30 border border-emerald-800/60 rounded-xl p-3.5 text-xs text-emerald-300 flex items-center justify-between">
          <span>{discoveryNotification.message}</span>
          <button
            onClick={() => setDiscoveryNotification(null)}
            className="text-emerald-400 hover:text-emerald-200 text-xs ml-4 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

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
      <DeviceTable devices={devices} loading={loading || isDiscovering} />

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

