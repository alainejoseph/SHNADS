import React, { useEffect, useState } from 'react';
import { Shield, Activity, Database, CheckCircle2, XCircle, Sun, Moon } from 'lucide-react';
import { getHealth } from '../../services/api';
import type { HealthStatus } from '../../types';
import { useTheme } from '../../context/ThemeContext';

export const Header: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const { theme, toggleTheme } = useTheme();

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
    <header className="h-16 border-b border-slate-200 bg-white/90 dark:border-slate-800 dark:bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30 transition-colors">
      <div className="flex items-center space-x-3">
        <div className="p-2 rounded-lg bg-blue-600/10 text-blue-700 dark:bg-blue-600/20 dark:text-blue-400 border border-blue-500/30">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-bold text-slate-900 dark:text-slate-100 leading-tight">
            Smart Home Anomaly Detection
          </h1>
        </div>
      </div>

      <div className="flex items-center space-x-4 text-xs">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700 hover:bg-slate-200 dark:bg-slate-800/80 dark:border-slate-700/60 dark:text-slate-300 dark:hover:bg-slate-700/80 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
          <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>

        {/* Backend status */}
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700 dark:bg-slate-800/80 dark:border-slate-700/60 dark:text-slate-300">
          <Activity className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
          <span>API:</span>
          {isHealthy ? (
            <span className="flex items-center text-emerald-700 dark:text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Online
            </span>
          ) : (
            <span className="flex items-center text-rose-700 dark:text-rose-400 font-medium">
              <XCircle className="w-3.5 h-3.5 mr-1" /> Offline
            </span>
          )}
        </div>

        {/* MongoDB status */}
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700 dark:bg-slate-800/80 dark:border-slate-700/60 dark:text-slate-300">
          <Database className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
          <span>DB:</span>
          {isDbConnected ? (
            <span className="text-emerald-700 dark:text-emerald-400 font-medium">Connected</span>
          ) : (
            <span className="text-rose-700 dark:text-rose-400 font-medium">Disconnected</span>
          )}
        </div>
      </div>
    </header>
  );
};

