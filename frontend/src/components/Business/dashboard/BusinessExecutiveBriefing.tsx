import React, { useState } from 'react';
import { Sparkles, Bot, ArrowRight, RefreshCw } from 'lucide-react';
import { api } from '../../../api';
import type { CashPositionData, RunwayData, AgingSummaryData } from '../../../hooks/useBusinessDashboard';

interface BusinessExecutiveBriefingProps {
  cashPosition: CashPositionData | null;
  runway: RunwayData | null;
  agingSummary: AgingSummaryData | null;
  stagedCount: number;
  onOpenCopilot?: () => void;
  className?: string;
}

export const BusinessExecutiveBriefing: React.FC<BusinessExecutiveBriefingProps> = ({
  cashPosition,
  runway,
  agingSummary,
  stagedCount,
  onOpenCopilot,
  className = '',
}) => {
  const [prompt, setPrompt] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.askBusinessCopilot(prompt.trim());
      if (res?.status === 'success' && res?.data?.response) {
        setAnswer(res.data.response);
      } else {
        setAnswer(res?.message || 'Executive advisory analysis completed.');
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to query Business Copilot');
    } finally {
      setLoading(false);
    }
  };

  // Structured deterministic summary based on authoritative state
  const cashNum = parseFloat(cashPosition?.confirmed_cash || '0');
  const overdueNum = parseFloat(agingSummary?.total_overdue_amount || '0');

  return (
    <div
      className={`rounded-2xl bg-gradient-to-br from-[#0B0F19] via-[#0D1322] to-[#0B0F19] border border-slate-800/90 p-6 shadow-xl relative overflow-hidden ${className}`}
    >
      {/* Decorative Intelligence Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-start justify-between gap-4 mb-4 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-md shadow-cyan-500/10">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-100 tracking-tight">
                Executive Operating Briefing
              </h3>
              <span className="px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-[9px] font-bold text-cyan-300 uppercase tracking-wide">
                AI Advisory
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Grounded synthesis of liquidity, staging pipeline, and debt exposure.
            </p>
          </div>
        </div>

        {onOpenCopilot && (
          <button
            onClick={onOpenCopilot}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
          >
            <Bot className="w-3.5 h-3.5 text-cyan-400" />
            <span>Open Copilot</span>
          </button>
        )}
      </div>

      {/* Briefing Narrative / Content */}
      <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800/60 text-xs text-slate-300 leading-relaxed mb-4 relative z-10 space-y-2">
        {answer ? (
          <div className="space-y-2">
            <p className="text-slate-200 font-medium">{answer}</p>
            <button
              onClick={() => setAnswer(null)}
              className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1 mt-2"
            >
              <span>Back to operating summary</span>
            </button>
          </div>
        ) : (
          <div className="space-y-1.5">
            <p>
              <strong className="text-slate-100">Liquidity & Runway:</strong>{' '}
              {runway?.message || 'Confirmed cash balance is monitored in real-time.'}
              {cashNum > 0 && ` Current position stands at ₹${cashNum.toLocaleString('en-IN')}.`}
            </p>
            <p>
              <strong className="text-slate-100">Action Priorities:</strong>{' '}
              {overdueNum > 0
                ? `You have ₹${overdueNum.toLocaleString('en-IN')} in overdue receivables across ${agingSummary?.total_overdue_count || 0} invoices requiring rescue.`
                : 'Zero overdue customer receivables detected.'}{' '}
              {stagedCount > 0
                ? `${stagedCount} extraction item(s) are awaiting human verification in the staging queue.`
                : 'Staging queue is clear.'}
            </p>
          </div>
        )}
      </div>

      {/* Inline Copilot Input Box */}
      <form onSubmit={handleAsk} className="flex gap-2 relative z-10">
        <input
          type="text"
          placeholder="Ask Chief-of-Staff (e.g., 'What is our runway if overdue invoices are delayed 30 days?')..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          className="flex-1 px-3.5 py-2 text-xs rounded-xl bg-slate-900 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !prompt.trim()}
          className="px-4 py-2 text-xs font-bold bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 disabled:opacity-40 rounded-xl transition-all flex items-center gap-1.5"
        >
          {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}
          <span>Analyze</span>
        </button>
      </form>

      {error && <p className="text-[11px] text-rose-400 mt-2 px-1">{error}</p>}
    </div>
  );
};
