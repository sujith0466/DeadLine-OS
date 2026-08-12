import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

def update_dashboard():
    path = FRONTEND_DIR / "src" / "pages" / "Dashboard.tsx"
    if path.exists():
        content = path.read_text(encoding='utf-8')
        if "Link to=\"/today\"" not in content:
            # Inject Link import
            content = content.replace(
                "import { motion } from 'framer-motion';",
                "import { motion } from 'framer-motion';\\nimport { Link } from 'react-router-dom';"
            )
            # Inject banner
            banner_html = """
      {/* Today Execution Prominent Link */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <Link to="/today" className="block p-4 rounded-2xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 transition-all group">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/50">
                <Target className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white group-hover:text-indigo-300 transition-colors">Start Today's Execution</h3>
                <p className="text-indigo-400 text-sm">Open the focused execution environment and start your timers.</p>
              </div>
            </div>
            <div className="text-indigo-400 group-hover:translate-x-1 transition-transform">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </Link>
      </motion.div>
"""
            content = content.replace(
                "{/* 1. Header & AI Chief-of-Staff Briefing */}",
                banner_html + "\\n      {/* 1. Header & AI Chief-of-Staff Briefing */}"
            )
            path.write_text(content, encoding='utf-8')
            print(f"Updated {path}")
        else:
            print(f"{path} already updated")
    else:
        print(f"Warning: {path} not found")

if __name__ == "__main__":
    update_dashboard()
    print("Milestone 5 Dashboard Applied.")
