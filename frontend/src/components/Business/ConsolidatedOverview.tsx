import React, { useEffect, useState } from 'react';
import { Layers, DollarSign, ArrowUpRight, ArrowDownRight, ShieldCheck } from 'lucide-react';
import { api } from '../../api';

export const ConsolidatedOverview: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getConsolidatedOverview()
      .then(res => setData(res.data?.overview))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-6 text-center text-slate-500 text-xs">Loading consolidated multi-entity overview...</div>;
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Consolidated Multi-Workspace Overview
          </h3>
          <p className="text-xs text-slate-400">
            Real-time multi-tenant financial aggregation across {data.workspaces_count} authorized workspaces
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Inter-Entity Eliminated: ₹{data.inter_entity_eliminations}</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400 flex items-center justify-between">
            <span>Consolidated Cash</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white mt-1">₹{data.consolidated_cash}</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400 flex items-center justify-between">
            <span>Total Revenue</span>
            <ArrowUpRight className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400 mt-1">₹{data.consolidated_revenue}</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400 flex items-center justify-between">
            <span>Total Expenses</span>
            <ArrowDownRight className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-xl font-bold text-rose-400 mt-1">₹{data.consolidated_expenses}</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Net Operating Flow</div>
          <div className="text-xl font-bold text-indigo-400 mt-1">₹{data.net_operating_cashflow}</div>
        </div>
      </div>

      {/* Breakdowns */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/40 text-xs font-semibold text-slate-400">
          Workspace Entities Breakdown
        </div>
        <div className="divide-y divide-slate-800">
          {data.workspace_breakdowns?.map((ws: any) => (
            <div key={ws.workspace_id} className="p-4 flex items-center justify-between hover:bg-slate-800/30 transition-colors">
              <div>
                <div className="text-sm font-semibold text-white">{ws.workspace_name}</div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Receivables: ₹{ws.receivables} • Payables: ₹{ws.payables}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold text-white">₹{ws.cash_position}</div>
                <div className="text-[10px] text-slate-500">Runway: {ws.runway_days} days</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
