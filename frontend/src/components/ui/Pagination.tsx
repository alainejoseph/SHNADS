import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  total: number;
  skip: number;
  limit: number;
  onPageChange: (newSkip: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  total,
  skip,
  limit,
  onPageChange,
}) => {
  if (total <= limit && skip === 0) return null;

  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const hasPrev = skip > 0;
  const hasNext = skip + limit < total;

  return (
    <div className="flex items-center justify-between border-t border-slate-800/80 px-4 py-3 mt-4 text-xs text-slate-400">
      <div>
        Showing <span className="font-medium text-slate-200">{Math.min(total, skip + 1)}</span> to{' '}
        <span className="font-medium text-slate-200">{Math.min(total, skip + limit)}</span> of{' '}
        <span className="font-medium text-slate-200">{total}</span> results
      </div>
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onPageChange(Math.max(0, skip - limit))}
          disabled={!hasPrev}
          className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="px-2 py-1 text-slate-300">
          Page {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(skip + limit)}
          disabled={!hasNext}
          className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition"
          aria-label="Next page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

