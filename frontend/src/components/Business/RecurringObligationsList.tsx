import React, { useEffect, useState } from 'react';
import { RefreshCw, Plus, Play, Pause, XCircle, Zap, History } from 'lucide-react';
import { api } from '../../api';

interface RecurringObligationsListProps {
  onOpenCreate: () => void;
  onOpenLogs: () => void;
}

export const RecurringObligationsList: React.FC<RecurringObligationsListProps> = ({ onOpenCreate, onOpenLogs }) => {
  const [obligations, setObligations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningBatch, setRunningBatch] = useState(false);

  const fetchObligations = async () => {
    setLoading(true);
    try {
      const res = await api.listRecurringObligations();
      setObligations(res.data?.obligations || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObligations();
  }, []);

  const handlePause = async (id: string) => {
    try {
      await api.pauseRecurringObligation(id);
      fetchObligations();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResume = async (id: string) => {
    try {
      await api.resumeRecurringObligation(id);
      fetchObligations();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await api.cancelRecurringObligation(id);
      fetchObligations();
    } catch (err) {
      console.error(err);
    }
  };

  const handleTrigger = async (id: string) => {
    try {
      await api.triggerRecurringObligation(id);
      fetchObligations();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunBatch = async () => {
    setRunningBatch(true);
    try {
      await api.runBatchAutomations();
      fetchObligations();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningBatch(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-indigo-400" />
            Recurring Obligations & Automations
          </h3>
          <p className="text-xs text-slate-400">Scheduled retainers, payables, rent, payroll, and tax compliance</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenLogs}
            className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <History className="w-3.5 h-3.5" />
            <span>Execution Logs</span>
          </button>
          <button
            onClick={handleRunBatch}
            disabled={runningBatch}
            className="px-3 py-2 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600/30 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Zap className={`w-3.5 h-3.5 ${runningBatch ? 'animate-spin' : ''}`} />
            <span>Run Automations Now</span>
          </button>
          <button
            onClick={onOpenCreate}
            className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-indigo-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>New Schedule</span>
          </button>
        </div>
      </div>

      {/* Obligations Grid/List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="divide-y divide-slate-800">
          {obligations.map((obl) => (
            <div key={obl.id} className="p-4 flex items-center justify-between hover:bg-slate-800/30 transition-colors">
              <div>
                <div className="text-sm font-semibold text-white flex items-center gap-2">
                  {obl.title}
                  <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${
                    obl.obligation_type === 'RECEIVABLE'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : obl.obligation_type === 'PAYABLE'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {obl.obligation_type}
                  </span>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    {obl.frequency}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                  <span>Partner: {obl.partner_name || 'General'}</span>
                  <span>•</span>
                  <span>Next Due: <strong className="text-white">{obl.next_due_date}</strong></span>
                  <span>•</span>
                  <span className={`font-medium ${obl.status === 'ACTIVE' ? 'text-emerald-400' : 'text-slate-500'}`}>
                    Status: {obl.status}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-bold text-white">₹{obl.amount}</div>
                  <div className="text-[10px] text-slate-500">{obl.currency}</div>
                </div>

                {obl.status === 'ACTIVE' && (
                  <>
                    <button
                      onClick={() => handleTrigger(obl.id)}
                      title="Trigger Immediate Generation"
                      className="p-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 transition-colors"
                    >
                      <Zap className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handlePause(obl.id)}
                      title="Pause Schedule"
                      className="p-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 transition-colors"
                    >
                      <Pause className="w-4 h-4" />
                    </button>
                  </>
                )}

                {obl.status === 'PAUSED' && (
                  <button
                    onClick={() => handleResume(obl.id)}
                    title="Resume Schedule"
                    className="p-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 transition-colors"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                )}

                {obl.status !== 'CANCELLED' && (
                  <button
                    onClick={() => handleCancel(obl.id)}
                    title="Cancel Schedule"
                    className="p-2 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}

          {obligations.length === 0 && !loading && (
            <div className="p-8 text-center text-slate-500 text-sm">
              No recurring obligations configured. Create one to automate your retainers and bill schedules!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
