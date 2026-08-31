import React, { useState, useEffect } from 'react';
import { X, Send, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../../api';

interface ReminderModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoiceId: string | null;
  initialTone?: string;
}

export const ReminderModal: React.FC<ReminderModalProps> = ({ isOpen, onClose, invoiceId, initialTone = 'POLITE' }) => {
  const [tone, setTone] = useState(initialTone);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<any>(null);
  const [customBody, setCustomBody] = useState('');
  const [sentSuccess, setSentSuccess] = useState(false);

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

  if (!isOpen || !invoiceId) return null;

  const handleGenerateDraft = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.draftCollectionReminder(invoiceId, tone);
      setDraft(res.data?.reminder);
      setCustomBody(res.data?.reminder?.message_body || '');
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to draft reminder');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!draft?.id) return;
    setLoading(true);
    setError(null);
    try {
      await api.sendCollectionReminder(draft.id, customBody);
      setSentSuccess(true);
      setTimeout(() => {
        onClose();
        setSentSuccess(false);
        setDraft(null);
      }, 1500);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to dispatch reminder');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="reminder-modal-title"
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <h3 id="reminder-modal-title" className="font-semibold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <span>Collection Reminder</span>
            <span className="text-xs bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-full border border-indigo-500/20">
              Human Review Barrier
            </span>
          </h3>
          <button
            onClick={onClose}
            aria-label="Close reminder modal"
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {sentSuccess && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <span>Reminder dispatched successfully!</span>
            </div>
          )}

          {/* Tone Selector */}
          {!draft && !sentSuccess && (
            <div className="space-y-3">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Select Reminder Tone</label>
              <div className="grid grid-cols-2 gap-2">
                {['GENTLE', 'POLITE', 'URGENT', 'LEGAL'].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTone(t)}
                    className={`py-2 px-3 rounded-xl text-xs font-medium border transition-colors ${
                      tone === t
                        ? 'bg-indigo-600 border-indigo-500 text-white'
                        : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <button
                onClick={handleGenerateDraft}
                disabled={loading}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium flex items-center justify-center gap-2 mt-4 transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                <span>Generate Grounded Draft</span>
              </button>
            </div>
          )}

          {/* Review & Edit Draft */}
          {draft && !sentSuccess && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400">Subject</label>
                <input
                  type="text"
                  value={draft.subject}
                  disabled
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400">Message Body (Editable)</label>
                <textarea
                  value={customBody}
                  onChange={(e) => setCustomBody(e.target.value)}
                  rows={6}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setDraft(null)}
                  className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                >
                  Change Tone
                </button>
                <button
                  onClick={handleSend}
                  disabled={loading || !customBody.trim()}
                  className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-600/20"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Confirm & Send</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
