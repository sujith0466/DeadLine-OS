import React from 'react';
import { Inbox } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface BusinessEmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const BusinessEmptyState: React.FC<BusinessEmptyStateProps> = ({
  title,
  description,
  icon: Icon = Inbox,
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div
      role="status"
      className={`p-10 sm:p-14 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-xl flex flex-col items-center justify-center text-center ${className}`}
    >
      <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4 shadow-lg shadow-emerald-500/5" aria-hidden="true">
        <Icon className="w-7 h-7" />
      </div>

      <h3 className="text-base font-bold text-slate-100 tracking-tight mb-1.5 font-sans">
        {title}
      </h3>

      <p className="text-xs sm:text-sm text-slate-400 max-w-md leading-relaxed mb-6">
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-md shadow-emerald-500/20 transition-all duration-200 active:scale-[0.98] outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
        >
          <span>{actionLabel}</span>
        </button>
      )}
    </div>
  );
};
