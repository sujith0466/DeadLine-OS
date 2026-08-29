import React, { useState } from 'react';
import { X, Download, ShieldCheck } from 'lucide-react';

interface AccountantExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AccountantExportModal: React.FC<AccountantExportModalProps> = ({ isOpen, onClose }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  if (!isOpen) return null;

  const handleDownload = (format: string) => {
    let url = `/api/business/exports/${format}`;
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    window.open(url, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="font-semibold text-white">Accountant Export Package</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-xs text-slate-400">
            Export deterministic CSV streams and complete ZIP audit package with SHA-256 provenance checksums.
          </p>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-400">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1"
              />
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => handleDownload('accountant-package')}
              className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20"
            >
              <Download className="w-4 h-4" />
              <span>Download Complete ZIP Package</span>
            </button>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleDownload('invoices.csv')}
                className="py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700"
              >
                Invoices CSV
              </button>
              <button
                onClick={() => handleDownload('transactions.csv')}
                className="py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700"
              >
                Transactions CSV
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
