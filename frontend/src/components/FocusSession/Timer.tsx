import React, { useEffect, useState } from 'react';
import { useRuntime } from '../../context/RuntimeContext';

export const Timer: React.FC = () => {
  const { runtimeState } = useRuntime();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    
    if (runtimeState?.active && runtimeState?.status === 'RUNNING') {
      interval = setInterval(() => {
        setElapsed(prev => prev + 1);
      }, 1000);
    }
    
    return () => clearInterval(interval);
  }, [runtimeState]);

  // Format MM:SS
  const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
  const secs = (elapsed % 60).toString().padStart(2, '0');

  return (
    <div className="font-mono text-4xl font-bold text-white tracking-widest">
      {mins}:{secs}
    </div>
  );
};
