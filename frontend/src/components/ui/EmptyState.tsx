import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'There is currently no activity or data to display.',
  icon,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center text-slate-400">
      <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center mb-3 text-slate-500 border border-slate-700/50">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-base font-semibold text-slate-200">{title}</h4>
      <p className="text-sm text-slate-400 max-w-sm mt-1 mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};

