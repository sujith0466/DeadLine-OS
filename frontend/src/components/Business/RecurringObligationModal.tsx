import React, { useState, useEffect } from 'react';
import { X, Check } from 'lucide-react';
import { api } from '../../api';

interface RecurringObligationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const RecurringObligationModal: React.FC<RecurringObligationModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [obligationType, setObligationType] = useState('RECEIVABLE');
  const [frequency, setFrequency] = useState('MONTHLY');
  const [amount, setAmount] = useState('');
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    if (!title.trim() || !amount.trim()) return;

    setLoading(true);
    setError(null);
    try {
      await api.createRecurringObligation({
        title: title.trim(),
        obligation_type: obligationType,
        frequency,
        amount: amount.trim(),
        start_date: startDate,
        notes: notes.trim() || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to create recurring obligation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="recurring-modal-title"
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <h3 id="recurring-modal-title" className="font-semibold text-white">Create Recurring Schedule</h3>
          <button
            onClick={onClose}
            aria-label="Close recurring schedule modal"
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="text-xs font-semibold text-slate-400">Schedule Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Monthly Client Retainer or Office Rent"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-400">Obligation Type</label>
              <select
                value={obligationType}
                onChange={(e) => setObligationType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1"
              >
                <option value="RECEIVABLE">Receivable (Income)</option>
                <option value="PAYABLE">Payable (Expense)</option>
                <option value="TAX_COMPLIANCE">Tax Compliance</option>
                <option value="PAYROLL">Payroll</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">Frequency</label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1"
              >
                <option value="WEEKLY">Weekly</option>
                <option value="BIWEEKLY">Bi-Weekly</option>
                <option value="MONTHLY">Monthly</option>
                <option value="QUARTERLY">Quarterly</option>
                <option value="ANNUALLY">Annually</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-400">Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="25000.00"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">First Due Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1"
                required
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-400">Notes (Optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !title.trim() || !amount.trim()}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-colors"
          >
            <Check className="w-4 h-4" />
            <span>Create Recurring Schedule</span>
          </button>
        </form>
      </div>
    </div>
  );
};
