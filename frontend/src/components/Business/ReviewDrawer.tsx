import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { X, Check, Trash2, Sparkles } from 'lucide-react';

interface StagedExtraction {
  id: string;
  source_channel: string;
  candidate_type: string;
  status: string;
  normalized_data: {
    amount?: string;
    currency?: string;
    date?: string;
    partner_id?: string;
    partner_name?: string;
    description?: string;
  };
  confidence_score: number;
  raw_extracted_data?: any;
}

interface ReviewDrawerProps {
  stagingId: string | null;
  onClose: () => void;
  onActionComplete: () => void;
}

export const ReviewDrawer: React.FC<ReviewDrawerProps> = ({ stagingId, onClose, onActionComplete }) => {
  const [item, setItem] = useState<StagedExtraction | null>(null);
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [dateVal, setDateVal] = useState('');
  const [partnerName, setPartnerName] = useState('');
  const [candidateType, setCandidateType] = useState('EXPENSE');
  const [description, setDescription] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [isRejecting, setIsRejecting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (stagingId) {
      loadItem(stagingId);
    }
  }, [stagingId]);

  const loadItem = async (id: string) => {
    setIsLoading(true);
    try {
      const res = await api.getStagedItem(id);
      if (res.status === 'success' && res.data?.staged_extraction) {
        const ext = res.data.staged_extraction;
        setItem(ext);
        setAmount(ext.normalized_data?.amount || '0.00');
        setCurrency(ext.normalized_data?.currency || 'INR');
        setDateVal(ext.normalized_data?.date || '');
        setPartnerName(ext.normalized_data?.partner_name || '');
        setCandidateType(ext.candidate_type || 'EXPENSE');
        setDescription(ext.normalized_data?.description || '');
      }
    } catch (err) {
      console.error('Failed to load staged item:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!stagingId) return;
    try {
      await api.updateStagedItem(stagingId, {
        candidate_type: candidateType,
        normalized_data: {
          amount,
          currency,
          date: dateVal,
          partner_name: partnerName,
          description
        }
      });
      await loadItem(stagingId);
    } catch (err) {
      console.error('Failed to update staged item:', err);
    }
  };

  const handleConfirm = async () => {
    if (!stagingId) return;
    setIsLoading(true);
    try {
      await handleUpdate();
      const res = await api.confirmStagedItem(stagingId);
      if (res.status === 'success') {
        onActionComplete();
        onClose();
      }
    } catch (err) {
      console.error('Failed to confirm item:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    if (!stagingId) return;
    setIsLoading(true);
    try {
      const res = await api.rejectStagedItem(stagingId, rejectReason);
      if (res.status === 'success') {
        onActionComplete();
        onClose();
      }
    } catch (err) {
      console.error('Failed to reject item:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!stagingId || !item) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-zinc-900 border-l border-white/10 shadow-2xl p-6 overflow-y-auto animate-slide-left">
      <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-bold text-white">Review Staged Candidate</h2>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="space-y-4">
        <div className="p-3 bg-white/5 rounded-xl border border-white/5 flex items-center justify-between text-xs">
          <span className="text-zinc-400">Source: <strong className="text-zinc-200 capitalize">{item.source_channel.toLowerCase()}</strong></span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-semibold border border-emerald-500/20">
            Confidence: {item.confidence_score}%
          </span>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">Candidate Type</label>
            <select
              value={candidateType}
              onChange={e => setCandidateType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="EXPENSE">Expense</option>
              <option value="INVOICE_RECEIVABLE">Invoice Receivable (Customer Inflow)</option>
              <option value="INVOICE_PAYABLE">Invoice Payable (Supplier Outflow)</option>
              <option value="PAYMENT_RECORD">Payment Record</option>
              <option value="NOTE">Business Note</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-1">Amount</label>
              <input
                type="text"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-1">Date</label>
              <input
                type="date"
                value={dateVal}
                onChange={e => setDateVal(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">Counterparty / Partner</label>
            <input
              type="text"
              value={partnerName}
              onChange={e => setPartnerName(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">Description / Notes</label>
            <textarea
              rows={2}
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        {isRejecting ? (
          <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/20 space-y-2">
            <label className="block text-xs font-semibold text-red-400">Reason for Rejection</label>
            <input
              type="text"
              placeholder="e.g. Duplicate receipt or invalid charge"
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg bg-black/40 border border-red-500/30 text-xs text-white focus:outline-none"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setIsRejecting(false)}
                className="px-3 py-1 text-xs text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={isLoading}
                className="px-4 py-1 text-xs bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        ) : (
          <div className="pt-4 border-t border-white/10 flex items-center justify-between">
            <button
              onClick={() => setIsRejecting(true)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Reject</span>
            </button>

            <div className="flex gap-2">
              <button
                onClick={handleUpdate}
                disabled={isLoading}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-zinc-300 bg-white/5 hover:bg-white/10 transition-colors"
              >
                Save Draft
              </button>
              <button
                onClick={handleConfirm}
                disabled={isLoading}
                className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold text-black bg-emerald-500 hover:bg-emerald-600 transition-colors shadow-lg shadow-emerald-500/10"
              >
                <Check className="w-4 h-4" />
                <span>Confirm & Approve</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
