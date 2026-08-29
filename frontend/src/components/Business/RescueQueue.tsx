import React, { useEffect, useState } from 'react';
import { ShieldAlert, Clock, Send, RefreshCw } from 'lucide-react';
import { api } from '../../api';

interface RescueQueueProps {
  onOpenReminder: (invoiceId: string, tone?: string) => void;
}

export const RescueQueue: React.FC<RescueQueueProps> = ({ onOpenReminder }) => {
  const [aging, setAging] = useState<any>(null);
  const [priorities, setPriorities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [agingRes, prioritiesRes] = await Promise.all([
        api.getRescueAgingSummary(),
        api.getPriorityReceivables(10)
      ]);
      setAging(agingRes.data);
      setPriorities(prioritiesRes.data?.priorities || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Receivable Rescue & Overdue Aging
          </h3>
          <p className="text-xs text-slate-400">Prioritized collection workflow grounded in deterministic cash aging</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Aging Buckets Cards */}
      {aging && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="text-xs font-medium text-emerald-400">1–30 Days Overdue</div>
            <div className="text-xl font-bold text-white mt-1">₹{aging.buckets['1_to_30_days'].total}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{aging.buckets['1_to_30_days'].count} invoices</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="text-xs font-medium text-amber-400">31–60 Days Overdue</div>
            <div className="text-xl font-bold text-white mt-1">₹{aging.buckets['31_to_60_days'].total}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{aging.buckets['31_to_60_days'].count} invoices</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="text-xs font-medium text-orange-400">61–90 Days Overdue</div>
            <div className="text-xl font-bold text-white mt-1">₹{aging.buckets['61_to_90_days'].total}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{aging.buckets['61_to_90_days'].count} invoices</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="text-xs font-medium text-rose-400">90+ Days Overdue</div>
            <div className="text-xl font-bold text-white mt-1">₹{aging.buckets['90_plus_days'].total}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{aging.buckets['90_plus_days'].count} invoices</div>
          </div>
        </div>
      )}

      {/* Priority Receivables Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            Top Recovery Priorities
          </h4>
        </div>
        <div className="divide-y divide-slate-800">
          {priorities.map((item) => (
            <div key={item.invoice_id} className="p-4 flex items-center justify-between hover:bg-slate-800/30 transition-colors">
              <div>
                <div className="text-sm font-semibold text-white flex items-center gap-2">
                  {item.partner_name}
                  <span className="text-xs font-mono text-slate-400">({item.invoice_number})</span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-3">
                  <span className="text-rose-400 font-medium">{item.days_overdue} days past due</span>
                  <span>•</span>
                  <span>Due: {item.due_date}</span>
                  <span>•</span>
                  <span className="text-indigo-400">Priority Score: {item.priority_score}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-bold text-white">₹{item.balance_due}</div>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {item.recommended_tone}
                  </span>
                </div>
                <button
                  onClick={() => onOpenReminder(item.invoice_id, item.recommended_tone)}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Draft Reminder</span>
                </button>
              </div>
            </div>
          ))}

          {priorities.length === 0 && !loading && (
            <div className="p-8 text-center text-slate-500 text-sm">
              No overdue receivables found. All customer accounts are up to date!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
