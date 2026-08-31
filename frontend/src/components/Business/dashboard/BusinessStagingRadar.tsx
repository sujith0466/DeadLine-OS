import React from 'react';
import { Layers, Plus, ArrowRight, FileText, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StatusBadge } from '../StatusBadge';
import { BusinessLoadingState } from '../BusinessLoadingState';
import { BusinessErrorState } from '../BusinessErrorState';
import type { StagedItemSummary } from '../../../hooks/useBusinessDashboard';

interface BusinessStagingRadarProps {
  items: StagedItemSummary[];
  total: number;
  loading: boolean;
  error?: string;
  onOpenCapture?: () => void;
  onRetry?: () => void;
  className?: string;
}

export const BusinessStagingRadar: React.FC<BusinessStagingRadarProps> = ({
  items,
  total,
  loading,
  error,
  onOpenCapture,
  onRetry,
  className = '',
}) => {
  if (loading && items.length === 0) {
    return <BusinessLoadingState type="card" className={className} />;
  }

  if (error && items.length === 0) {
    return (
      <BusinessErrorState
        title="Staging Queue Unavailable"
        message={error}
        onRetry={onRetry}
        className={className}
      />
    );
  }

  return (
    <div
      className={`rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 p-5 shadow-xl flex flex-col justify-between ${className}`}
    >
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Staging Radar
              </h3>
              <p className="text-[11px] text-slate-500">
                OCR & text capture extractions pending commit
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400">
              {total} Pending
            </span>
            {onOpenCapture && (
              <button
                onClick={onOpenCapture}
                title="Quick Document/Text Ingestion"
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {items.length === 0 ? (
          <div className="py-6 text-center text-slate-400 text-xs">
            <CheckCircle className="w-7 h-7 text-emerald-400/80 mx-auto mb-2" />
            <p className="font-semibold text-slate-200">Staging Pipeline Clear</p>
            <p className="text-[11px] text-slate-500 mt-0.5 mb-3">
              All OCR and text captures have been reviewed and committed.
            </p>
            {onOpenCapture && (
              <button
                onClick={onOpenCapture}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-xs font-semibold text-emerald-300 transition-colors"
              >
                <Plus className="w-3 h-3" />
                <span>Capture Document</span>
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-2 mb-4">
            {items.map(item => {
              const vendor = item.extracted_data?.partner_name || item.extracted_data?.vendor_name || 'Extracted Entity';
              const amount = item.extracted_data?.total_amount || item.extracted_data?.amount;

              return (
                <div
                  key={item.id}
                  className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 flex items-center justify-between text-xs hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center gap-2.5 truncate pr-2">
                    <FileText className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    <div className="truncate">
                      <div className="font-semibold text-slate-200 truncate">{vendor}</div>
                      <div className="text-[10px] text-slate-500 flex items-center gap-1.5">
                        <span className="uppercase font-mono">{item.candidate_type}</span>
                        <span>•</span>
                        <span>{item.source_type}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {amount && (
                      <span className="font-mono text-slate-300 text-xs font-medium">
                        ₹{parseFloat(amount).toLocaleString('en-IN')}
                      </span>
                    )}
                    <StatusBadge status="STAGED" size="sm" />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <Link
        to="/business/staging"
        className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
      >
        <span>Open Complete Staging Queue ({total})</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    </div>
  );
};
