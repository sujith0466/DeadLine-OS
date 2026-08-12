import React, { useEffect, useState } from 'react';
import { DeadlineOSApi } from '../../api';
import { DailyTimeline } from '../../components/Today/DailyTimeline';
import { InterruptedBanner } from '../../components/FocusSession/InterruptedBanner';
import { TodayProgress } from '../../components/Today/TodayProgress';

export const Today: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchToday = async () => {
    try {
      const res = await DeadlineOSApi.getTodayActivities();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchToday();
    const interval = setInterval(fetchToday, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-8 text-slate-500 animate-pulse">Loading Today...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-32">
      <InterruptedBanner />
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Today's Execution</h1>
        <p className="text-slate-400">Your prioritized pipeline for {data?.date || 'today'}.</p>
      </header>

      <TodayProgress 
        completedTasks={data?.completed?.length || 0}
        totalTasks={(data?.upcoming?.length || 0) + (data?.completed?.length || 0)}
        focusTimeMinutes={Math.floor((data?.metrics?.focus_time_seconds || 0) / 60)}
      />

      <section>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4">
          Upcoming Pipeline
        </h2>
        <DailyTimeline activities={data?.upcoming || []} />
      </section>
    </div>
  );
};
