import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, ArrowUpRight, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { RiskAlert } from '../../../hooks/useBusinessDashboard';

interface BusinessAttentionPanelProps {
  risks: RiskAlert[];
  overdueCount: number;
  stagedCount: number;
  className?: string;
}

export const BusinessAttentionPanel: React.FC<BusinessAttentionPanelProps> = ({
  risks,
  overdueCount,
  stagedCount,
  className = '',
}) => {
  const hasAlerts = risks.length > 0 || overdueCount > 0 || stagedCount > 0;

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
            {risks.length + (overdueCount > 0 ? 1 : 0) + (stagedCount > 0 ? 1 : 0)} Flags
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
            Cash runway, debt recovery, and staging pipelines are within healthy operating parameters.
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
        </div>
      )}
    </div>
  );
};
