import React from 'react';
import { Play } from 'lucide-react';
import { useRuntime } from '../../context/RuntimeContext';

interface Activity {
  id: string;
  title: string;
  type: string;
  status: string;
  priority_score: number;
}

interface DailyTimelineProps {
  activities: Activity[];
}

export const DailyTimeline: React.FC<DailyTimelineProps> = ({ activities }) => {
  const { startActivity, runtimeState } = useRuntime();
  
  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500 border border-slate-800 rounded-2xl bg-slate-900/50">
        <p>No activities scheduled for today.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activities.map((activity, idx) => {
        const isRunning = runtimeState?.entity_id === activity.id && runtimeState?.active;
        
        return (
          <div 
            key={activity.id} 
            className={`p-4 rounded-xl flex items-center justify-between border transition-all ${
              isRunning ? 'bg-indigo-500/10 border-indigo-500/30' : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs text-slate-400 font-mono">
                {idx + 1}
              </div>
              <div>
                <h4 className={`font-medium ${isRunning ? 'text-indigo-400' : 'text-slate-200'}`}>
                  {activity.title}
                </h4>
                <p className="text-xs text-slate-500 uppercase tracking-wider mt-0.5">
                  {activity.type}
                </p>
              </div>
            </div>
            
            {!isRunning && (
              <button 
                onClick={() => startActivity(activity.id, activity.type, 1500)} // default 25min focus
                className="w-10 h-10 rounded-full bg-slate-800 hover:bg-indigo-600 hover:text-white flex items-center justify-center transition-colors text-slate-400"
                title="Start Focus Session"
              >
                <Play className="w-4 h-4 ml-1" />
              </button>
            )}
            
            {isRunning && (
              <div className="px-3 py-1 bg-indigo-500/20 text-indigo-400 text-xs rounded-full animate-pulse font-medium tracking-wider">
                ACTIVE
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
