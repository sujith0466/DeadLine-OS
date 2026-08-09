import os
import re

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'frontend'))

def write_file(path, content):
    full_path = os.path.join(FRONTEND_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created/Updated: {path}")

def update_api_ts():
    api_path = os.path.join(FRONTEND_DIR, 'src', 'api.ts')
    with open(api_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'runtimeApi' not in content:
        # We'll append it before `};` at the end of the file.
        # DeadlineOSApi is an object exported at the end.
        runtime_api_code = '''
  runtime: {
    async getActive() {
      const response = await apiClient.get('/runtime/active');
      return response.data;
    },
    async start(entityId: string, entityType: string, plannedDurationSec?: number) {
      const response = await apiClient.post('/runtime/start', { entity_id: entityId, entity_type: entityType, planned_duration_sec: plannedDurationSec });
      return response.data;
    },
    async pause(entityId: string) {
      const response = await apiClient.post('/runtime/pause', { entity_id: entityId });
      return response.data;
    },
    async resume(entityId: string) {
      const response = await apiClient.post('/runtime/resume', { entity_id: entityId });
      return response.data;
    },
    async complete(entityId: string, completionSource: string = 'MANUAL') {
      const response = await apiClient.post('/runtime/complete', { entity_id: entityId, completion_source: completionSource });
      return response.data;
    }
  }
};'''
        # Replace the last `};`
        content = content.rstrip()
        if content.endswith('};'):
            content = content[:-2] + ',\n' + runtime_api_code
        with open(api_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated api.ts with runtime API")

def update_app_tsx():
    app_path = os.path.join(FRONTEND_DIR, 'src', 'App.tsx')
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'RuntimeProvider' not in content:
        content = re.sub(
            r"(import { SettingsProvider } from '\./context/SettingsContext';)",
            r"\1\nimport { RuntimeProvider } from './context/RuntimeContext';",
            content
        )
        content = re.sub(
            r"(<SettingsProvider>)",
            r"\1\n        <RuntimeProvider>",
            content
        )
        content = re.sub(
            r"(</SettingsProvider>)",
            r"        </RuntimeProvider>\n\1",
            content
        )
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated App.tsx with RuntimeProvider")

def update_command_center():
    cc_path = os.path.join(FRONTEND_DIR, 'src', 'pages', 'CommandCenter.tsx')
    with open(cc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'RuntimeWidget' not in content:
        content = re.sub(
            r"(import { useSync } from '\.\./hooks/useSync';)",
            r"\1\nimport { RuntimeWidget } from '../components/RuntimeWidget';",
            content
        )
        # Add RuntimeWidget below the header in the UI
        # We can look for the main div grid
        content = re.sub(
            r"(<div className=\"flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-10\">\n\s*<div>.*?</div>\n\s*</div>)",
            r"\1\n\n        {/* Runtime Widget injected from Milestone 5 */}\n        <RuntimeWidget />\n",
            content,
            flags=re.DOTALL
        )
        with open(cc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated CommandCenter.tsx with RuntimeWidget")

def main():
    print("--- Milestone 5: Frontend Runtime Context ---")
    
    runtime_context_code = '''import React, { createContext, useContext, useState, useEffect } from 'react';
import { DeadlineOSApi } from '../api';

interface RuntimeState {
  active: boolean;
  runtime_id?: string;
  entity_id?: string;
  entity_type?: string;
  status?: string;
}

interface RuntimeContextType {
  runtimeState: RuntimeState | null;
  refreshRuntime: () => Promise<void>;
  startActivity: (entityId: string, entityType: string, duration?: number) => Promise<void>;
  pauseActivity: (entityId: string) => Promise<void>;
  resumeActivity: (entityId: string) => Promise<void>;
  completeActivity: (entityId: string) => Promise<void>;
}

const RuntimeContext = createContext<RuntimeContextType | undefined>(undefined);

export const RuntimeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [runtimeState, setRuntimeState] = useState<RuntimeState | null>(null);

  const refreshRuntime = async () => {
    try {
      const data = await DeadlineOSApi.runtime.getActive();
      if (data.active) {
        setRuntimeState(data);
      } else {
        setRuntimeState(null);
      }
    } catch (err) {
      console.error("Failed to fetch runtime state", err);
    }
  };

  useEffect(() => {
    refreshRuntime();
    const interval = setInterval(refreshRuntime, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const startActivity = async (entityId: string, entityType: string, duration?: number) => {
    await DeadlineOSApi.runtime.start(entityId, entityType, duration);
    await refreshRuntime();
  };

  const pauseActivity = async (entityId: string) => {
    await DeadlineOSApi.runtime.pause(entityId);
    await refreshRuntime();
  };

  const resumeActivity = async (entityId: string) => {
    await DeadlineOSApi.runtime.resume(entityId);
    await refreshRuntime();
  };

  const completeActivity = async (entityId: string) => {
    await DeadlineOSApi.runtime.complete(entityId);
    await refreshRuntime();
  };

  return (
    <RuntimeContext.Provider value={{
      runtimeState, refreshRuntime, startActivity, pauseActivity, resumeActivity, completeActivity
    }}>
      {children}
    </RuntimeContext.Provider>
  );
};

export const useRuntime = () => {
  const context = useContext(RuntimeContext);
  if (!context) throw new Error("useRuntime must be used within RuntimeProvider");
  return context;
};
'''
    write_file('src/context/RuntimeContext.tsx', runtime_context_code)

    runtime_widget_code = '''import React from 'react';
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
'''
    write_file('src/components/RuntimeWidget.tsx', runtime_widget_code)
    
    update_api_ts()
    update_app_tsx()
    update_command_center()

if __name__ == "__main__":
    main()
