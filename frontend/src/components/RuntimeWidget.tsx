import React from 'react';
import { useRuntime } from '../context/RuntimeContext';
import { Play, Pause, CheckSquare, Activity } from 'lucide-react';
import { GradientButton } from './UI/GradientButton';

export const RuntimeWidget: React.FC = () => {
  const { runtimeState, pauseActivity, resumeActivity, completeActivity } = useRuntime();

  if (!runtimeState) return null; // Only show when active

  return (
    <div className="bg-[#0a0a0a]/50 backdrop-blur-2xl border border-white/10 rounded-xl p-4 mb-8 flex flex-col md:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
          <Activity className="w-5 h-5 text-emerald-400" />
        </div>
        <div>
          <h3 className="text-white font-medium text-lg">Active {runtimeState.entity_type}: {runtimeState.entity_id}</h3>
          <p className="text-white/50 text-sm">Status: <span className="text-emerald-400">{runtimeState.status}</span></p>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        {runtimeState.status === 'RUNNING' && (
          <button 
            onClick={() => pauseActivity(runtimeState.entity_id!)}
            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-white transition-colors"
            title="Pause"
          >
            <Pause className="w-5 h-5" />
          </button>
        )}
        {runtimeState.status === 'PAUSED' && (
          <button 
            onClick={() => resumeActivity(runtimeState.entity_id!)}
            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-white transition-colors"
            title="Resume"
          >
            <Play className="w-5 h-5" />
          </button>
        )}
        
        <GradientButton onClick={() => completeActivity(runtimeState.entity_id!)}>
          <span className="flex items-center gap-2">
            <CheckSquare className="w-4 h-4" />
            Complete
          </span>
        </GradientButton>
      </div>
    </div>
  );
};
