import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  action?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children, className = '', title, action }) => {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
          {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};

