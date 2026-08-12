import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

def generate_today_progress():
    path = FRONTEND_DIR / "src" / "components" / "Today" / "TodayProgress.tsx"
    content = """import React from 'react';
import { CheckCircle2, Clock, Target } from 'lucide-react';

interface TodayProgressProps {
  completedTasks: number;
  totalTasks: number;
  focusTimeMinutes: number;
}

export const TodayProgress: React.FC<TodayProgressProps> = ({ 
  completedTasks, 
  totalTasks, 
  focusTimeMinutes 
}) => {
  const percentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-slate-400 font-medium">Task Completion</h3>
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-indigo-400" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-white">{completedTasks}</span>
          <span className="text-slate-500 font-medium">/ {totalTasks}</span>
        </div>
        <div className="mt-4 h-2 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-indigo-500 rounded-full transition-all duration-1000" 
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-slate-400 font-medium">Focus Time</h3>
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
            <Clock className="w-5 h-5 text-amber-500" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-white">{focusTimeMinutes}</span>
          <span className="text-slate-500 font-medium">min</span>
        </div>
        <p className="text-xs text-amber-500/70 mt-2 font-medium">
          Logged today
        </p>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-slate-400 font-medium">Daily Score</h3>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
            <Target className="w-5 h-5 text-emerald-500" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-white">{percentage}</span>
          <span className="text-slate-500 font-medium">%</span>
        </div>
        <p className="text-xs text-emerald-500/70 mt-2 font-medium">
          Efficiency rating
        </p>
      </div>
    </div>
  );
};
"""
    path.write_text(content, encoding='utf-8')
    print(f"Created {path}")

def update_today_page():
    path = FRONTEND_DIR / "src" / "pages" / "Today" / "Today.tsx"
    if path.exists():
        content = path.read_text(encoding='utf-8')
        if "TodayProgress" not in content:
            # Inject import
            content = content.replace(
                "import { InterruptedBanner } from '../../components/FocusSession/InterruptedBanner';",
                "import { InterruptedBanner } from '../../components/FocusSession/InterruptedBanner';\\nimport { TodayProgress } from '../../components/Today/TodayProgress';"
            )
            # Inject Progress component
            content = content.replace(
                "<section>",
                "<TodayProgress \\n        completedTasks={data?.completed?.length || 0}\\n        totalTasks={(data?.upcoming?.length || 0) + (data?.completed?.length || 0)}\\n        focusTimeMinutes={Math.floor((data?.metrics?.focus_time_seconds || 0) / 60)}\\n      />\\n\\n      <section>"
            )
            path.write_text(content, encoding='utf-8')
            print(f"Updated {path}")
        else:
            print(f"{path} already updated")
    else:
        print(f"Warning: {path} not found")

if __name__ == "__main__":
    generate_today_progress()
    update_today_page()
    print("Milestone 4 Progress Applied.")
