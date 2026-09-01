import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, ArrowUpRight, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { RiskAlert } from '../../../hooks/useBusinessDashboard';

interface BusinessAttentionPanelProps {
  risks: RiskAlert[];
  overdueCount: number;
  stagedCount: number;
  overdueTasksCount?: number;
  blockedTasksCount?: number;
  lowStockCount?: number;
  outOfStockCount?: number;
  className?: string;
}

export const BusinessAttentionPanel: React.FC<BusinessAttentionPanelProps> = ({
  risks,
  overdueCount,
  stagedCount,
  overdueTasksCount = 0,
  blockedTasksCount = 0,
  lowStockCount = 0,
  outOfStockCount = 0,
  className = '',
}) => {
  const hasAlerts =
    risks.length > 0 ||
    overdueCount > 0 ||
    stagedCount > 0 ||
    overdueTasksCount > 0 ||
    blockedTasksCount > 0 ||
    lowStockCount > 0 ||
    outOfStockCount > 0;

  const totalFlagCount =
    risks.length +
    (overdueCount > 0 ? 1 : 0) +
    (stagedCount > 0 ? 1 : 0) +
    (overdueTasksCount > 0 ? 1 : 0) +
    (blockedTasksCount > 0 ? 1 : 0) +
    (outOfStockCount > 0 ? 1 : 0) +
    (lowStockCount > 0 && outOfStockCount === 0 ? 1 : 0);

  return (
    <div
      className={`rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 p-5 shadow-xl ${className}`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Executive Attention Radar
            </h3>
            <p className="text-[11px] text-slate-500">
              Active operational flags & liquidity risk signals
            </p>
          </div>
        </div>

        {hasAlerts ? (
          <span className="px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[10px] font-bold text-amber-400">
            {totalFlagCount} Flags
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>Optimal</span>
          </span>
        )}
      </div>

      {!hasAlerts ? (
        <div className="py-6 text-center text-slate-400 text-xs">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
          <p className="font-semibold text-slate-200">No Immediate Threats Detected</p>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Cash runway, debt recovery, operations queue, and stock levels are within healthy operating parameters.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {/* Risk Alerts from Backend */}
          {risks.map((risk, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-xl border flex items-start justify-between gap-3 text-xs ${
                risk.severity === 'CRITICAL'
                  ? 'bg-rose-500/5 border-rose-500/20 text-rose-300'
                  : 'bg-amber-500/5 border-amber-500/20 text-amber-300'
              }`}
            >
              <div className="flex items-start gap-2.5">
                {risk.severity === 'CRITICAL' ? (
                  <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                )}
                <div>
                  <div className="font-bold text-slate-200">{risk.title}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{risk.message}</div>
                </div>
              </div>
            </div>
          ))}

          {/* Overdue Debt Alert */}
          {overdueCount > 0 && (
            <div className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <div>
                  <span className="font-bold text-slate-200">{overdueCount} Overdue Invoices</span>
                  <span className="text-[11px] text-slate-400 block">Pending recovery in Rescue Queue</span>
                </div>
              </div>
              <Link
                to="/business/rescue"
                className="text-xs font-semibold text-rose-300 hover:text-rose-200 flex items-center gap-1"
              >
                <span>Rescue</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* Staging Backlog Alert */}
          {stagedCount > 0 && (
            <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <div>
                  <span className="font-bold text-slate-200">{stagedCount} Items in Staging</span>
                  <span className="text-[11px] text-slate-400 block">Extraction ready for human confirmation</span>
                </div>
              </div>
              <Link
                to="/business/staging"
                className="text-xs font-semibold text-emerald-300 hover:text-emerald-200 flex items-center gap-1"
              >
                <span>Review</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* C1: Overdue Business Tasks Alert */}
          {overdueTasksCount > 0 && (
            <div className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <div>
                  <span className="font-bold text-slate-200">{overdueTasksCount} Overdue Operational Tasks</span>
                  <span className="text-[11px] text-slate-400 block">Past due date in Task Queue</span>
                </div>
              </div>
              <Link
                to="/business/tasks"
                className="text-xs font-semibold text-rose-300 hover:text-rose-200 flex items-center gap-1"
              >
                <span>Tasks</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* C1: Blocked Tasks Alert */}
          {blockedTasksCount > 0 && overdueTasksCount === 0 && (
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <div>
                  <span className="font-bold text-slate-200">{blockedTasksCount} Blocked Operational Tasks</span>
                  <span className="text-[11px] text-slate-400 block">Action blocked awaiting resolution</span>
                </div>
              </div>
              <Link
                to="/business/tasks"
                className="text-xs font-semibold text-amber-300 hover:text-amber-200 flex items-center gap-1"
              >
                <span>Tasks</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* C1: Out of Stock / Low Stock Alert */}
          {(outOfStockCount > 0 || lowStockCount > 0) && (
            <div
              className={`p-3 rounded-xl border flex items-center justify-between text-xs ${
                outOfStockCount > 0
                  ? 'bg-rose-500/5 border-rose-500/20'
                  : 'bg-amber-500/5 border-amber-500/20'
              }`}
            >
              <div className="flex items-center gap-2.5">
                {outOfStockCount > 0 ? (
                  <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                )}
                <div>
                  <span className="font-bold text-slate-200">
                    {outOfStockCount > 0
                      ? `${outOfStockCount} SKUs Out of Stock`
                      : `${lowStockCount} SKUs at Low Stock`}
                  </span>
                  <span className="text-[11px] text-slate-400 block">
                    {outOfStockCount > 0
                      ? `${lowStockCount} additional items below reorder level`
                      : 'Inventory at or below reorder threshold'}
                  </span>
                </div>
              </div>
              <Link
                to="/business/inventory"
                className={`text-xs font-semibold flex items-center gap-1 ${
                  outOfStockCount > 0 ? 'text-rose-300 hover:text-rose-200' : 'text-amber-300 hover:text-amber-200'
                }`}
              >
                <span>Stock</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
