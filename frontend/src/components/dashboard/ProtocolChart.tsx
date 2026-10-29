import React from 'react';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/StatusBadge';

interface ProtocolChartProps {
  distribution?: Array<{ protocol: string; count: number }> | Record<string, number>;
}

export const ProtocolChart: React.FC<ProtocolChartProps> = ({ distribution }) => {
  const entries: Array<[string, number]> = React.useMemo(() => {
    if (!distribution) return [];
    if (Array.isArray(distribution)) {
      return distribution
        .map((item) => {
          if (typeof item === 'object' && item !== null && 'protocol' in item) {
            return [item.protocol, Number(item.count) || 0] as [string, number];
          }
          return null;
        })
        .filter((e): e is [string, number] => e !== null)
        .sort((a, b) => b[1] - a[1]);
    }
    return Object.entries(distribution).sort((a, b) => (b[1] as number) - (a[1] as number));
  }, [distribution]);

  const total = entries.reduce((acc, [, val]) => acc + Number(val || 0), 0);

  const getBarColor = (proto: string) => {
    switch ((proto || '').toUpperCase()) {
      case 'TCP':
        return 'bg-blue-500';
      case 'UDP':
        return 'bg-emerald-500';
      case 'ICMP':
        return 'bg-amber-500';
      case 'ARP':
        return 'bg-purple-500';
      case 'HTTP':
        return 'bg-cyan-500';
      case 'HTTPS':
        return 'bg-sky-500';
      default:
        return 'bg-slate-500';
    }
  };

  return (
    <Card title="Observed Protocol Distribution">
      {entries.length === 0 ? (
        <p className="text-xs text-slate-500 py-6 text-center">No protocol traffic recorded yet</p>
      ) : (
        <div className="space-y-3.5">
          {entries.map(([proto, count]) => {
            const pct = total > 0 ? ((Number(count) / total) * 100).toFixed(1) : '0';
            return (
              <div key={proto} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center space-x-2">
                    <StatusBadge status={proto} type="protocol" />
                    <span className="text-slate-400 font-mono">({Number(count).toLocaleString()} flows)</span>
                  </div>
                  <span className="font-semibold text-slate-200">{pct}%</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${getBarColor(proto)}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};

