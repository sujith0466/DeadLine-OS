import React from 'react';
import { LifeBuoy, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StatusBadge } from '../StatusBadge';
import { BusinessLoadingState } from '../BusinessLoadingState';
import { BusinessErrorState } from '../BusinessErrorState';
import type { AgingSummaryData, PriorityReceivable } from '../../../hooks/useBusinessDashboard';

interface BusinessRescueRadarProps {
  agingSummary: AgingSummaryData | null;
  priorities: PriorityReceivable[];
  loading: boolean;
  error?: string;
  onRetry?: () => void;
  className?: string;
}

export const BusinessRescueRadar: React.FC<BusinessRescueRadarProps> = ({
  agingSummary,
  priorities,
  loading,
  error,
  onRetry,
  className = '',
}) => {
  if (loading && !agingSummary) {
    return <BusinessLoadingState type="card" className={className} />;
  }

  if (error && !agingSummary) {
    return (
      <BusinessErrorState
        title="Rescue Data Unavailable"
        message={error}
        onRetry={onRetry}
        className={className}
      />
    );
  }

  const totalCount = agingSummary?.total_overdue_count || 0;
  const buckets = agingSummary?.buckets;

  return (
    <div
      className={`rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 p-5 shadow-xl flex flex-col justify-between ${className}`}
    >
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <LifeBuoy className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Receivable Rescue Radar
              </h3>
              <p className="text-[11px] text-slate-500">
                Aging delinquent invoices & priority recovery queue
              </p>
            </div>
          </div>

          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
              totalCount > 0
                ? 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
                : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
            }`}
          >
            {totalCount} Overdue
          </span>
        </div>

        {/* Aging Buckets Grid */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
            <div className="text-[9px] uppercase font-bold text-slate-500">1-30D</div>
            <div className="text-xs font-bold text-slate-200 mt-0.5">
              ₹{buckets ? parseFloat(buckets['1_to_30_days'].total).toLocaleString('en-IN') : '0'}
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">
              {buckets?.['1_to_30_days']?.count || 0} inv
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
            <div className="text-[9px] uppercase font-bold text-amber-400">31-60D</div>
            <div className="text-xs font-bold text-amber-300 mt-0.5">
              ₹{buckets ? parseFloat(buckets['31_to_60_days'].total).toLocaleString('en-IN') : '0'}
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">
              {buckets?.['31_to_60_days']?.count || 0} inv
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
            <div className="text-[9px] uppercase font-bold text-orange-400">61-90D</div>
            <div className="text-xs font-bold text-orange-300 mt-0.5">
              ₹{buckets ? parseFloat(buckets['61_to_90_days'].total).toLocaleString('en-IN') : '0'}
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">
              {buckets?.['61_to_90_days']?.count || 0} inv
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
            <div className="text-[9px] uppercase font-bold text-rose-400">90+D</div>
            <div className="text-xs font-bold text-rose-300 mt-0.5">
              ₹{buckets ? parseFloat(buckets['90_plus_days'].total).toLocaleString('en-IN') : '0'}
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">
              {buckets?.['90_plus_days']?.count || 0} inv
            </div>
          </div>
        </div>

        {/* Priority Overdue Items */}
        {priorities.length === 0 ? (
          <div className="py-4 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-6 h-6 text-emerald-400/80 mx-auto mb-1.5" />
            <p className="font-medium text-slate-200">Zero Overdue Receivables</p>
          </div>
        ) : (
          <div className="space-y-2 mb-4">
            {priorities.slice(0, 3).map(inv => (
              <div
                key={inv.id}
                className="p-2.5 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between text-xs"
              >
                <div className="truncate pr-2">
                  <div className="font-semibold text-slate-200 truncate">{inv.partner_name}</div>
                  <div className="text-[10px] text-rose-400 flex items-center gap-1.5">
                    <span>{inv.invoice_number}</span>
                    <span>•</span>
                    <span>{inv.days_overdue} days overdue</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="font-mono text-slate-200 font-bold text-xs">
                    ₹{parseFloat(inv.balance_due).toLocaleString('en-IN')}
                  </span>
                  <StatusBadge status="OVERDUE" size="sm" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Link
        to="/business/rescue"
        className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-rose-400 hover:text-rose-300 transition-colors"
      >
        <span>Open Rescue Queue & Send Reminders</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    </div>
  );
};
