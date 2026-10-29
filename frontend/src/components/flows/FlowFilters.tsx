import React from 'react';
import { Search, RotateCcw, Calendar } from 'lucide-react';

interface FlowFiltersProps {
  srcIp: string;
  dstIp: string;
  protocol: string;
  startDate: string;
  startTime: string;
  endDate: string;
  endTime: string;
  onSrcIpChange: (value: string) => void;
  onDstIpChange: (value: string) => void;
  onProtocolChange: (value: string) => void;
  onStartDateChange: (value: string) => void;
  onStartTimeChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onEndTimeChange: (value: string) => void;
  onReset: () => void;
}

const protocols = ['All', 'TCP', 'UDP', 'ICMP', 'ARP', 'HTTP', 'HTTPS', 'Other'];

export const FlowFilters: React.FC<FlowFiltersProps> = ({
  srcIp,
  dstIp,
  protocol,
  startDate,
  startTime,
  endDate,
  endTime,
  onSrcIpChange,
  onDstIpChange,
  onProtocolChange,
  onStartDateChange,
  onStartTimeChange,
  onEndDateChange,
  onEndTimeChange,
  onReset,
}) => {
  const now = new Date();
  const pad = (n: number) => n.toString().padStart(2, '0');
  const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const currentTime = `${pad(now.getHours())}:${pad(now.getMinutes())}`;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg shadow-black/20">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={srcIp}
            onChange={(e) => onSrcIpChange(e.target.value)}
            placeholder="Source IP"
            className="w-full bg-slate-950/60 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500/60 focus:border-cyan-500/60 transition-colors"
          />
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={dstIp}
            onChange={(e) => onDstIpChange(e.target.value)}
            placeholder="Destination IP"
            className="w-full bg-slate-950/60 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500/60 focus:border-cyan-500/60 transition-colors"
          />
        </div>
        <div>
          <select
            value={protocol}
            onChange={(e) => onProtocolChange(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500/60 focus:border-cyan-500/60 transition-colors"
          >
            {protocols.map((p) => (
              <option key={p} value={p === 'All' ? '' : p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div className="relative col-span-1">
          <div className="flex items-center gap-1 bg-slate-950/60 border border-slate-800 rounded-lg px-2 py-1.5 focus-within:ring-1 focus-within:ring-cyan-500/60 focus-within:border-cyan-500/60 transition-colors">
            <Calendar className="w-4 h-4 text-slate-500" />
            <input
              type="date"
              value={startDate}
              max={endDate || today}
              onChange={(e) => onStartDateChange(e.target.value)}
              className="flex-1 bg-transparent text-xs text-slate-200 outline-none"
            />
            <input
              type="time"
              value={startTime || currentTime}
              onChange={(e) => onStartTimeChange(e.target.value)}
              className="w-24 bg-transparent text-xs text-slate-200 outline-none"
            />
          </div>
          <div className="text-[10px] text-slate-500 mt-1">From</div>
        </div>
        <div className="relative col-span-1">
          <div className="flex items-center gap-1 bg-slate-950/60 border border-slate-800 rounded-lg px-2 py-1.5 focus-within:ring-1 focus-within:ring-cyan-500/60 focus-within:border-cyan-500/60 transition-colors">
            <Calendar className="w-4 h-4 text-slate-500" />
            <input
              type="date"
              value={endDate}
              min={startDate || undefined}
              max={today}
              onChange={(e) => onEndDateChange(e.target.value)}
              className="flex-1 bg-transparent text-xs text-slate-200 outline-none"
            />
            <input
              type="time"
              value={endTime || currentTime}
              onChange={(e) => onEndTimeChange(e.target.value)}
              className="w-24 bg-transparent text-xs text-slate-200 outline-none"
            />
          </div>
          <div className="text-[10px] text-slate-500 mt-1">To</div>
        </div>
        <button
          onClick={onReset}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-slate-700 text-slate-300 hover:text-slate-100 hover:border-slate-500 transition-colors text-sm self-start mt-0"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </button>
      </div>
    </div>
  );
};
