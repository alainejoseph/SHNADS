import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Laptop, Radio, Activity } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/devices', label: 'Devices', icon: Laptop },
    { to: '/live', label: 'Live Monitor', icon: Radio },
    { to: '/flows', label: 'Flow History', icon: Activity },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950 flex flex-col justify-between shrink-0 min-h-screen transition-colors">
      <div className="p-4">
        <div className="flex items-center space-x-2.5 px-3 py-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-blue-500/20">
            SH
          </div>
          <span className="font-semibold text-slate-800 dark:text-slate-200 tracking-wide">SH-NIDS</span>
        </div>

        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                    isActive
                      ? 'bg-blue-600/10 text-blue-700 border border-blue-500/30 dark:bg-blue-600/15 dark:text-blue-400'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-900/80'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};

