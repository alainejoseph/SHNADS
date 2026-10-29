import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="bg-rose-950/30 border border-rose-800/60 rounded-xl p-4 text-rose-300 flex items-start space-x-3">
      <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
      <div className="flex-1 text-sm">
        <p className="font-medium text-rose-200">Error Encountered</p>
        <p className="mt-1 text-rose-300/90">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-rose-900/60 hover:bg-rose-800/60 text-rose-200 rounded-lg text-xs font-medium transition cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};

