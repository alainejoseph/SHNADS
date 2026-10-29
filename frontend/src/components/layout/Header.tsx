import React, { useEffect, useState } from 'react';
import { Shield, Activity, Database, CheckCircle2, XCircle } from 'lucide-react';
import { getHealth } from '../../services/api';
import type { HealthStatus } from '../../types';

export const Header: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await getHealth();
        setHealth(res);
      } catch {
        setHealth({
          status: 'error',
          database: 'disconnected',
          timestamp: new Date().toISOString(),
        });
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === 'healthy';
  const isDbConnected = health?.database === 'connected';

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-bold text-slate-100 leading-tight">
            Smart Home Anomaly Detection
          </h1>
        </div>
      </div>

      <div className="flex items-center space-x-4 text-xs">
        {/* Backend status */}
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60">
          <Activity className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-300">API:</span>
          {isHealthy ? (
            <span className="flex items-center text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" /> Online
            </span>
          ) : (
            <span className="flex items-center text-rose-400 font-medium">
              <XCircle className="w-3.5 h-3.5 mr-1 text-rose-400" /> Offline
            </span>
          )}
        </div>

        {/* MongoDB status */}
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60">
          <Database className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-300">DB:</span>
          {isDbConnected ? (
            <span className="text-emerald-400 font-medium">Connected</span>
          ) : (
            <span className="text-rose-400 font-medium">Disconnected</span>
          )}
        </div>
      </div>
    </header>
  );
};

