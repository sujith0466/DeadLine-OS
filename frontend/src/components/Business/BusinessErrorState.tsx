import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface BusinessErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const BusinessErrorState: React.FC<BusinessErrorStateProps> = ({
  title = 'Unable to Load Business Data',
  message = 'An unexpected error occurred while communicating with the Business OS service. Please verify your connection and try again.',
  onRetry,
  className = '',
}) => {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`p-8 sm:p-10 rounded-2xl bg-rose-500/5 border border-rose-500/20 shadow-xl flex flex-col items-center justify-center text-center ${className}`}
    >
      <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-3.5 shadow-lg shadow-rose-500/10">
        <AlertTriangle className="w-6 h-6" />
      </div>

      <h3 className="text-sm sm:text-base font-bold text-slate-100 tracking-tight mb-1">
        {title}
      </h3>

      <p className="text-xs text-slate-400 max-w-md leading-relaxed mb-5">
        {message}
      </p>

      {onRetry && (
        <button
          onClick={onRetry}
          aria-label="Retry loading business data"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900 border border-slate-700 hover:border-slate-600 text-slate-200 hover:text-white transition-all shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
        >
          <RefreshCw className="w-3.5 h-3.5 text-emerald-400" />
          <span>Retry Operation</span>
        </button>
      )}
    </div>
  );
};
