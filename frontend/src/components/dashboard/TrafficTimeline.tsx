import React from 'react';
import { Card } from '../ui/Card';
import { formatHourIST } from '../../utils/time';

interface TrafficTimelineProps {
  timeline?: Array<{ hour: string; count: number }>;
}

const formatLabel = (hour?: string) => {
  if (!hour) return '';
  try {
    const d = new Date(hour);
    if (!isNaN(d.getTime())) {
      return formatHourIST(d);
    }
    return hour;
  } catch {
    return hour;
  }
};

export const TrafficTimeline: React.FC<TrafficTimelineProps> = ({ timeline = [] }) => {
  const entries = timeline || [];
  const maxCount = Math.max(...entries.map((t) => Number(t.count) || 0), 1);

  return (
    <Card title="Traffic Flow Volume (Recent Activity)">
      {entries.length === 0 ? (
        <p className="text-xs text-slate-500 py-6 text-center">No timeline activity to display</p>
      ) : (
        <div className="pt-2">
          <div className="h-32 flex items-end gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
            {entries.map((item, idx) => {
              const count = Number(item.count) || 0;
              const heightPct = Math.max(4, Math.round((count / maxCount) * 100));
              return (
                <div key={item.hour + idx} className="flex-1 flex flex-col items-center group relative h-full justify-end">
                  <div className="absolute -top-7 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 text-slate-200 text-[10px] px-1.5 py-0.5 rounded shadow pointer-events-none whitespace-nowrap z-10">
                    {count.toLocaleString()} flows
                  </div>
                  <div
                    className="w-full bg-blue-600 hover:bg-blue-500 dark:bg-blue-500/70 dark:hover:bg-blue-400 rounded-t transition-all duration-300"
                    style={{ height: `${heightPct}%` }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-[10px] text-slate-600 dark:text-slate-500 mt-2 font-mono">
            <span>{formatLabel(entries[0]?.hour)}</span>
            <span>{formatLabel(entries[Math.floor(entries.length / 2)]?.hour)}</span>
            <span>{formatLabel(entries[entries.length - 1]?.hour)}</span>
          </div>
        </div>
      )}
    </Card>
  );
};

