import React from 'react';
import { AlertTriangle, Play, Square } from 'lucide-react';
import { useRuntime } from '../../context/RuntimeContext';

export const InterruptedBanner: React.FC = () => {
  const { runtimeState, resumeActivity, completeActivity } = useRuntime();

  if (!runtimeState || !runtimeState.active || runtimeState.status !== 'PAUSED') {
    return null;
  }

  return (
    <div className="mb-6 bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-500">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-semibold text-amber-500">Interrupted Session Detected</h4>
          <p className="text-sm text-amber-500/80">
            You have a paused {runtimeState.entity_type} session. Would you like to resume it?
          </p>
        </div>
      </div>
      <div className="flex gap-2">
        <button 
          onClick={() => resumeActivity(runtimeState.entity_id!)}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-medium rounded-xl flex items-center gap-2 transition-colors"
        >
          <Play className="w-4 h-4 fill-current" /> Resume
        </button>
        <button 
          onClick={() => completeActivity(runtimeState.entity_id!)}
          className="px-4 py-2 bg-slate-900/50 hover:bg-slate-800 text-slate-300 font-medium rounded-xl border border-slate-700 flex items-center gap-2 transition-colors"
        >
          <Square className="w-4 h-4" /> End
        </button>
      </div>
    </div>
  );
};
