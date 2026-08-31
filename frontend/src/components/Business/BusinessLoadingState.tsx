import React from 'react';

interface BusinessLoadingStateProps {
  type?: 'card' | 'table' | 'kpi-grid' | 'full';
  rows?: number;
  className?: string;
}

export const BusinessLoadingState: React.FC<BusinessLoadingStateProps> = ({
  type = 'card',
  rows = 5,
  className = '',
}) => {
  if (type === 'kpi-grid') {
    return (
      <div role="status" className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
        <span className="sr-only">Loading key performance indicators...</span>
        {[1, 2, 3, 4].map(i => (
          <div
            key={i}
            className="p-5 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-xl animate-pulse space-y-3"
          >
            <div className="flex justify-between items-center">
              <div className="w-24 h-3 bg-slate-800 rounded" />
              <div className="w-7 h-7 bg-slate-800/80 rounded-xl" />
            </div>
            <div className="w-32 h-8 bg-slate-800 rounded-lg" />
            <div className="w-20 h-3 bg-slate-800/60 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div
        role="status"
        className={`rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 overflow-hidden shadow-xl p-4 space-y-3 animate-pulse ${className}`}
      >
        <span className="sr-only">Loading data table rows...</span>
        <div className="h-8 bg-slate-800/60 rounded-xl mb-4" />
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center justify-between gap-4 py-2 border-b border-slate-800/40">
            <div className="w-1/4 h-4 bg-slate-800/80 rounded" />
            <div className="w-1/4 h-4 bg-slate-800/60 rounded" />
            <div className="w-1/6 h-4 bg-slate-800/60 rounded" />
            <div className="w-1/6 h-4 bg-slate-800/80 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'full') {
    return (
      <div role="status" className={`space-y-6 animate-pulse ${className}`}>
        <span className="sr-only">Loading full business page...</span>
        {/* Header Skeleton */}
        <div className="space-y-2">
          <div className="w-48 h-7 bg-slate-800 rounded-lg" />
          <div className="w-96 h-4 bg-slate-800/60 rounded" />
        </div>

        {/* KPI Grid Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="p-5 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-xl space-y-3">
              <div className="w-20 h-3 bg-slate-800 rounded" />
              <div className="w-28 h-7 bg-slate-800 rounded-lg" />
            </div>
          ))}
        </div>

        {/* Main Content Skeleton */}
        <div className="p-6 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 h-72" />
      </div>
    );
  }

  // Default card
  return (
    <div
      role="status"
      className={`p-6 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-xl animate-pulse space-y-4 ${className}`}
    >
      <span className="sr-only">Loading card data...</span>
      <div className="w-1/3 h-5 bg-slate-800 rounded-lg" />
      <div className="w-full h-24 bg-slate-800/40 rounded-xl" />
      <div className="w-2/3 h-4 bg-slate-800/60 rounded" />
    </div>
  );
};
