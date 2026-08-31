import React, { useEffect, useState } from 'react';
import { X, History, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../../api';

interface AutomationLogsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AutomationLogsDrawer: React.FC<AutomationLogsDrawerProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<any[]>([]);

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

  useEffect(() => {
    if (isOpen) {
      api.getAutomationLogs({ limit: 30 })
        .then(res => setLogs(res.data?.logs || []))
        .catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="logs-drawer-title"
        className="bg-slate-900 border-l border-slate-800 w-full max-w-md h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            <h3 id="logs-drawer-title" className="font-semibold text-white">Automation Execution Logs</h3>
          </div>
          <button
            onClick={onClose}
            aria-label="Close automation logs drawer"
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* List */}
        <div className="p-6 flex-1 overflow-y-auto space-y-3">
          {logs.map((log) => (
            <div key={log.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                  {log.status === 'SUCCESS' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-rose-400" />
                  )}
                  {log.execution_type}
                </span>
                <span className="text-[10px] font-mono text-slate-500">{log.execution_date}</span>
              </div>
              <p className="text-[11px] text-slate-400">{log.details}</p>
            </div>
          ))}

          {logs.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-xs">
              No automation executions recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
