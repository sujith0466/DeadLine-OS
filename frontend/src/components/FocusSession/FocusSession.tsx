import React from 'react';
import { useRuntime } from '../../context/RuntimeContext';
import { Timer } from './Timer';

export const FocusSession: React.FC = () => {
  const { runtimeState, pauseActivity, resumeActivity, completeActivity } = useRuntime();

  if (!runtimeState || !runtimeState.active) {
    return null; // Hidden if no active session
  }

  const isRunning = runtimeState.status === 'RUNNING';

  return (
    <div className="fixed bottom-6 right-6 z-50 bg-slate-900/90 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-2xl p-6 w-80 text-center shadow-indigo-500/10">
      <h3 className="text-sm font-semibold text-indigo-400 mb-1 uppercase tracking-wider">
        Focus Session
      </h3>
      <p className="text-slate-300 mb-4 truncate text-sm">
        {runtimeState.entity_type} {runtimeState.entity_id?.substring(0, 8)}
      </p>
      
      <div className="mb-6 flex justify-center items-center py-4 bg-slate-950/50 rounded-xl inset-shadow-sm border border-slate-800/50">
        <Timer />
      </div>
      
      <div className="flex gap-3 justify-center">
        {isRunning ? (
          <button 
            onClick={() => pauseActivity(runtimeState.entity_id!)}
            className="flex-1 py-2.5 px-4 bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border border-amber-500/20 rounded-xl transition-all font-medium text-sm flex items-center justify-center gap-2"
          >
            Pause
          </button>
        ) : (
          <button 
            onClick={() => resumeActivity(runtimeState.entity_id!)}
            className="flex-1 py-2.5 px-4 bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border border-emerald-500/20 rounded-xl transition-all font-medium text-sm flex items-center justify-center gap-2"
          >
            Resume
          </button>
        )}
        <button 
          onClick={() => completeActivity(runtimeState.entity_id!)}
          className="flex-1 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-all shadow-md shadow-indigo-500/20 font-medium text-sm"
        >
          Complete
        </button>
      </div>
    </div>
  );
};
