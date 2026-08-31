import React from 'react';
import { CalendarClock, ArrowRight, Repeat } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StatusBadge } from '../StatusBadge';
import { BusinessLoadingState } from '../BusinessLoadingState';
import { BusinessErrorState } from '../BusinessErrorState';
import type { RecurringObligationSummary } from '../../../hooks/useBusinessDashboard';

interface BusinessRecurringRadarProps {
  obligations: RecurringObligationSummary[];
  loading: boolean;
  error?: string;
  onRetry?: () => void;
  className?: string;
}

export const BusinessRecurringRadar: React.FC<BusinessRecurringRadarProps> = ({
  obligations,
  loading,
  error,
  onRetry,
  className = '',
}) => {
  if (loading && obligations.length === 0) {
    return <BusinessLoadingState type="card" className={className} />;
  }

  if (error && obligations.length === 0) {
    return (
      <BusinessErrorState
        title="Recurring Obligations Unavailable"
        message={error}
        onRetry={onRetry}
        className={className}
      />
    );
  }

  return (
    <div
      className={`rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 p-5 shadow-xl flex flex-col justify-between ${className}`}
    >
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400">
              <CalendarClock className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Recurring Commitments
              </h3>
              <p className="text-[11px] text-slate-500">
                Active automated obligations & subscription burn
              </p>
            </div>
          </div>

          <span className="px-2 py-0.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-[10px] font-bold text-teal-400">
            {obligations.length} Active
          </span>
        </div>

        {obligations.length === 0 ? (
          <div className="py-6 text-center text-slate-400 text-xs">
            <Repeat className="w-7 h-7 text-slate-600 mx-auto mb-2" />
            <p className="font-semibold text-slate-200">No Active Recurring Contracts</p>
            <p className="text-[11px] text-slate-500 mt-0.5 mb-3">
              Set up scheduled rent, payroll, retainers, and subscriptions.
            </p>
          </div>
        ) : (
          <div className="space-y-2 mb-4">
            {obligations.slice(0, 4).map(ob => (
              <div
                key={ob.id}
                className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 flex items-center justify-between text-xs hover:border-slate-700 transition-colors"
              >
                <div className="truncate pr-2">
                  <div className="font-semibold text-slate-200 truncate">{ob.title}</div>
                  <div className="text-[10px] text-slate-500 flex items-center gap-1.5">
                    <span className="capitalize">{ob.frequency?.toLowerCase()}</span>
                    <span>•</span>
                    <span>Next: {ob.next_due_date ? new Date(ob.next_due_date).toLocaleDateString() : 'Pending'}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="font-mono text-slate-200 text-xs font-medium">
                    ₹{parseFloat(ob.amount).toLocaleString('en-IN')}
                  </span>
                  <StatusBadge status="ACTIVE" size="sm" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Link
        to="/business/recurring"
        className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-teal-400 hover:text-teal-300 transition-colors"
      >
        <span>Manage All Recurring Obligations</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    </div>
  );
};
