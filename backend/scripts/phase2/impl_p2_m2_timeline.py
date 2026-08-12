import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

def create_directories():
    (FRONTEND_DIR / "src" / "components" / "Today").mkdir(parents=True, exist_ok=True)
    (FRONTEND_DIR / "src" / "pages" / "Today").mkdir(parents=True, exist_ok=True)

def generate_daily_timeline():
    path = FRONTEND_DIR / "src" / "components" / "Today" / "DailyTimeline.tsx"
    content = """import React from 'react';
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
"""
    path.write_text(content, encoding='utf-8')
    print(f"Created {path}")

def generate_today_page():
    path = FRONTEND_DIR / "src" / "pages" / "Today" / "Today.tsx"
    content = """import React, { useEffect, useState } from 'react';
import { DeadlineOSApi } from '../../api';
import { DailyTimeline } from '../../components/Today/DailyTimeline';

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
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Today's Execution</h1>
        <p className="text-slate-400">Your prioritized pipeline for {data?.date || 'today'}.</p>
      </header>

      <section>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4">
          Upcoming Pipeline
        </h2>
        <DailyTimeline activities={data?.upcoming || []} />
      </section>
    </div>
  );
};
"""
    path.write_text(content, encoding='utf-8')
    print(f"Created {path}")

def update_app_routes():
    path = FRONTEND_DIR / "src" / "App.tsx"
    if path.exists():
        content = path.read_text(encoding='utf-8')
        if "import('./pages/Today/Today')" not in content:
            # inject lazy load
            content = content.replace(
                "const Dashboard = React.lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));",
                "const Dashboard = React.lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));\\nconst Today = React.lazy(() => import('./pages/Today/Today').then(m => ({ default: m.Today })));"
            )
            # inject route
            content = content.replace(
                '<Route path="/dashboard" element={<PageReveal><Dashboard /></PageReveal>} />',
                '<Route path="/dashboard" element={<PageReveal><Dashboard /></PageReveal>} />\\n          <Route path="/today" element={<PageReveal><Today /></PageReveal>} />'
            )
            path.write_text(content, encoding='utf-8')
            print(f"Updated {path}")
        else:
            print(f"{path} already updated")
    else:
        print(f"Warning: {path} not found")

if __name__ == "__main__":
    create_directories()
    generate_daily_timeline()
    generate_today_page()
    update_app_routes()
    print("Milestone 2 Timeline Applied.")
