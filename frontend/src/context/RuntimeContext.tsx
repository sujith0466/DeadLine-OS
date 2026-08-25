import React, { createContext, useContext, useState, useEffect } from 'react';
import { DeadlineOSApi } from '../api';
import { useAuth } from './AuthContext';

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
  const { user } = useAuth();
  const [runtimeState, setRuntimeState] = useState<RuntimeState | null>(null);

  const refreshRuntime = async () => {
    if (!user) {
      setRuntimeState(null);
      return;
    }
    try {
      const data = await DeadlineOSApi.runtime.getActive();
      if (data?.active) {
        setRuntimeState(data);
      } else {
        setRuntimeState(null);
      }
    } catch {
      // Ignored if unauthenticated or no active session
      setRuntimeState(null);
    }
  };

  useEffect(() => {
    if (!user) {
      setRuntimeState(null);
      return;
    }
    refreshRuntime();
    const interval = setInterval(refreshRuntime, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, [user]);

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
