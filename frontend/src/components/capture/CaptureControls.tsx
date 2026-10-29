import React, { useState } from 'react';
import { Play, Square, Network, AlertTriangle } from 'lucide-react';
import type { InterfaceInfo, CaptureStatus } from '../../types';

interface CaptureControlsProps {
  status: CaptureStatus | null;
  onStart: (iface: string) => Promise<void>;
  onStop: () => Promise<void>;
  disabled?: boolean;
}

export const CaptureControls: React.FC<CaptureControlsProps> = ({
  status,
  onStart,
  onStop,
  disabled,
}) => {
  const interfaces: InterfaceInfo[] = status?.available_interfaces || [];
  const isRunning = status?.is_running ?? false;

  const [selectedIface, setSelectedIface] = useState<string>(() => {
    // Default to the first non-loopback interface or first available
    const nonLoop = interfaces.find((i) => !i.is_loopback && i.is_up);
    return nonLoop ? nonLoop.name : interfaces[0]?.name || '';
  });

  const [isActing, setIsActing] = useState(false);

  // Sync selected interface if not set yet
  React.useEffect(() => {
    if (!selectedIface && interfaces.length > 0) {
      const nonLoop = interfaces.find((i) => !i.is_loopback && i.is_up);
      setSelectedIface(nonLoop ? nonLoop.name : interfaces[0].name);
    }
  }, [interfaces, selectedIface]);

  const handleStart = async () => {
    if (!selectedIface) return;
    setIsActing(true);
    try {
      await onStart(selectedIface);
    } finally {
      setIsActing(false);
    }
  };

  const handleStop = async () => {
    setIsActing(true);
    try {
      await onStop();
    } finally {
      setIsActing(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Interface selection */}
        <div className="flex-1 max-w-md">
          <label className="block text-xs font-medium text-slate-400 mb-1.5 flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5 text-blue-400" />
            <span>Target Network Interface</span>
          </label>
          <select
            value={selectedIface}
            onChange={(e) => setSelectedIface(e.target.value)}
            disabled={isRunning || disabled || isActing}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500/60 disabled:opacity-50 transition"
          >
            {interfaces.length === 0 ? (
              <option value="">No network interfaces detected</option>
            ) : (
              interfaces.map((i) => (
                <option key={i.name} value={i.name}>
                  {i.name} {i.is_loopback ? '(Loopback)' : i.addresses.join(', ') ? `(${i.addresses[0]})` : ''}
                </option>
              ))
            )}
          </select>
          {interfaces.find((i) => i.name === selectedIface)?.is_loopback && (
            <p className="text-[11px] text-amber-400/90 mt-1 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 shrink-0" />
              Monitoring loopback interface (local traffic only)
            </p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center space-x-3 pt-2 md:pt-0">
          {!isRunning ? (
            <button
              onClick={handleStart}
              disabled={disabled || isActing || !selectedIface}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 disabled:opacity-50 transition cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isActing ? 'Starting...' : 'Start Packet Capture'}</span>
            </button>
          ) : (
            <button
              onClick={handleStop}
              disabled={disabled || isActing}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/20 disabled:opacity-50 transition cursor-pointer"
            >
              <Square className="w-4 h-4 fill-current" />
              <span>{isActing ? 'Stopping...' : 'Stop Capture'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

