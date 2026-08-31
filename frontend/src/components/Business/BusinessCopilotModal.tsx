import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, Send, X, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../../api';

interface BusinessCopilotModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BusinessCopilotModal: React.FC<BusinessCopilotModalProps> = ({ isOpen, onClose }) => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.askBusinessCopilot(prompt.trim());
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to query Business Copilot');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="copilot-modal-title"
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 id="copilot-modal-title" className="font-semibold text-white flex items-center gap-2">
                Business Copilot
                <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 flex items-center gap-1 font-mono">
                  <Sparkles className="w-3 h-3" /> Grounded Truth
                </span>
              </h3>
              <p className="text-xs text-slate-400">Ask anything about your cash reality, overdue invoices, and runway</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Business Copilot"
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3 text-red-400 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {result && (
            <div className="space-y-4 animate-in fade-in duration-300">
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Executive Summary</h4>
                <p className="text-white text-sm leading-relaxed">{result.response?.summary}</p>
              </div>

              {result.response?.insights?.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/30">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Verified Insights</h4>
                  <ul className="space-y-1.5">
                    {result.response.insights.map((insight: string, idx: number) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.response?.suggested_actions?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Proposed Actions</h4>
                  {result.response.suggested_actions.map((act: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/20 flex items-center justify-between">
                      <div>
                        <div className="text-xs font-medium text-indigo-300">{act.title}</div>
                        <div className="text-[11px] text-slate-400">{act.details}</div>
                      </div>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {act.action_type}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {!result && !loading && (
            <div className="text-center py-8 text-slate-500">
              <Bot className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Try asking:</p>
              <p className="text-xs text-slate-400 mt-1 italic">"Who owes us money this week?" or "What is our current runway?"</p>
            </div>
          )}
        </div>

        {/* Input Footer */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-slate-950/60 flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask Copilot about your business finances..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm flex items-center gap-2 transition-colors shadow-lg shadow-indigo-600/20"
          >
            {loading ? <Sparkles className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span>Ask</span>
          </button>
        </form>
      </div>
    </div>
  );
};
