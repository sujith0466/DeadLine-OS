import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { Inbox, Plus, Eye } from 'lucide-react';
import { CaptureModal } from './CaptureModal';
import { ReviewDrawer } from './ReviewDrawer';

export const StagingQueue: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [isCaptureOpen, setIsCaptureOpen] = useState(false);
  const [selectedStagingId, setSelectedStagingId] = useState<string | null>(null);

  useEffect(() => {
    loadStagingItems();
  }, []);

  const loadStagingItems = async () => {
    try {
      const res = await api.listStagedItems({ status: 'NEEDS_REVIEW' });
      if (res.status === 'success' && res.data?.staged_items) {
        setItems(res.data.staged_items);
        setTotal(res.data.total || res.data.staged_items.length);
      }
    } catch (err) {
      console.error('Failed to load staging queue:', err);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Inbox className="w-4 h-4 text-emerald-400" />
            <span>Staging Review Queue</span>
            {total > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
                {total} Pending
              </span>
            )}
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Extracted candidates requiring human review before downstream execution.
          </p>
        </div>

        <button
          onClick={() => setIsCaptureOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-black text-xs font-semibold transition-colors shadow-lg shadow-emerald-500/10"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Capture Entry</span>
        </button>
      </div>

      {items.length === 0 ? (
        <div className="p-8 rounded-2xl bg-white/5 border border-white/5 text-center text-zinc-500 text-xs">
          <Inbox className="w-8 h-8 text-zinc-600 mx-auto mb-2 opacity-50" />
          No items awaiting review. All captured candidates have been verified.
        </div>
      ) : (
        <div className="grid gap-2">
          {items.map(item => (
            <div
              key={item.id}
              onClick={() => setSelectedStagingId(item.id)}
              className="flex items-center justify-between p-3.5 rounded-xl bg-white/5 border border-white/10 hover:border-emerald-500/30 hover:bg-white/[0.07] cursor-pointer transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <div>
                  <div className="text-xs font-semibold text-white">
                    {item.normalized_data?.partner_name || 'Unassigned Partner'}
                  </div>
                  <div className="text-[10px] text-zinc-400 capitalize">
                    {item.candidate_type.toLowerCase()} • {item.normalized_data?.date || 'No Date'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-xs font-bold text-emerald-400 font-mono">
                    ₹{item.normalized_data?.amount || '0.00'}
                  </div>
                  <div className="text-[10px] text-zinc-500">
                    Confidence: {item.confidence_score}%
                  </div>
                </div>

                <button className="p-1.5 rounded-lg bg-white/5 text-zinc-400 hover:text-white">
                  <Eye className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <CaptureModal
        isOpen={isCaptureOpen}
        onClose={() => setIsCaptureOpen(false)}
        onSuccess={loadStagingItems}
      />

      <ReviewDrawer
        stagingId={selectedStagingId}
        onClose={() => setSelectedStagingId(null)}
        onActionComplete={loadStagingItems}
      />
    </div>
  );
};
