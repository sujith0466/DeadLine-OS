import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

def generate_today_service():
    path = BACKEND_DIR / "services" / "today_service.py"
    content = '''"""
DeadlineOS — Today Service (Phase 2)
=====================================
Aggregates tasks, habits, and goals for the Today Surface.
Integrates with the Phase 1 Runtime Engine for execution state.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from database.db import db
from models.task import Task
from models.goal import Goal
from models.runtime_state import RuntimeState
from models.user_settings import UserSettings
from utils.timezone import TimezoneService

class TodayService:
    @classmethod
    def get_today_activities(cls, user_id: str) -> Dict[str, Any]:
        """
        Fetch all actionable items for the user's Today Surface.
        Returns them separated by category (running, upcoming, completed, etc.)
        """
        settings = UserSettings.query.get(user_id)
        tz_name = settings.timezone if settings else "UTC"
        local_now = TimezoneService.to_local(datetime.now(timezone.utc), tz_name)
        today_date = local_now.date()

        all_tasks = Task.query.filter_by(user_id=user_id).filter(Task.status.in_(['pending', 'in_progress'])).all()
        habits = Goal.query.filter_by(user_id=user_id, is_habit=True, status='active').all()
        
        active_runtimes = RuntimeState.query.filter_by(user_id=user_id).all()
        runtime_map = {rt.entity_id: rt.serialize() for rt in active_runtimes}
        
        activities = []
        
        for t in all_tasks:
            if t.deadline:
                task_date = TimezoneService.to_local(t.deadline, tz_name).date()
                if task_date > today_date:
                    continue
                    
            activity = {
                "id": t.id,
                "type": "task",
                "title": t.title,
                "status": t.status,
                "priority_score": getattr(t, 'priority_score', 0),
                "ai_confidence": getattr(t, 'ai_confidence', None),
                "runtime": runtime_map.get(t.id)
            }
            activities.append(activity)
            
        for h in habits:
            activity = {
                "id": h.id,
                "type": "habit",
                "title": h.title,
                "status": h.status,
                "runtime": runtime_map.get(h.id)
            }
            activities.append(activity)
            
        running = [a for a in activities if a.get("runtime") and a["runtime"]["lifecycle_state"] == "RUNNING"]
        interrupted = [a for a in activities if a.get("runtime") and a["runtime"]["lifecycle_state"] == "INTERRUPTED"]
        paused = [a for a in activities if a.get("runtime") and a["runtime"]["lifecycle_state"] == "PAUSED"]
        
        active_ids = {a["id"] for a in running + interrupted + paused}
        upcoming = [a for a in activities if a["id"] not in active_ids]
        upcoming.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        
        return {
            "date": today_date.isoformat(),
            "timezone": tz_name,
            "running": running,
            "interrupted": interrupted,
            "paused": paused,
            "upcoming": upcoming,
            "completed": []
        }
'''
    path.write_text(content, encoding='utf-8')
    print(f"Created {path}")

def generate_today_api():
    path = BACKEND_DIR / "api" / "today.py"
    content = '''"""
DeadlineOS — Today API (Phase 2)
=================================
Dedicated API for the Today Surface.
"""
from flask import Blueprint, jsonify, g
from utils.auth import require_auth
from utils.responses import success_response
from services.today_service import TodayService

today_bp = Blueprint("today", __name__)

@today_bp.route("/today", methods=["GET"])
@require_auth
def get_today_surface():
    """
    Fetch the aggregated execution state for the Today Surface.
    """
    data = TodayService.get_today_activities(g.user_id)
    return success_response("Today surface retrieved", data)
'''
    path.write_text(content, encoding='utf-8')
    print(f"Created {path}")

def update_app_py():
    path = BACKEND_DIR / "app.py"
    content = path.read_text(encoding='utf-8')
    if "from api.today import today_bp" not in content:
        content = content.replace(
            "from api.runtime import runtime_bp",
            "from api.runtime import runtime_bp\\n    from api.today import today_bp"
        )
        content = content.replace(
            'app.register_blueprint(runtime_bp, url_prefix="/api")',
            'app.register_blueprint(runtime_bp, url_prefix="/api")\\n\\n    app.register_blueprint(today_bp, url_prefix="/api")\\n    limiter.exempt(today_bp)'
        )
        content = content.replace(
            "users, demo",
            "users, demo, today"
        )
        path.write_text(content, encoding='utf-8')
        print(f"Updated {path}")
    else:
        print(f"{path} already updated")

def update_frontend_api():
    path = BACKEND_DIR.parent / "frontend" / "src" / "api.ts"
    content = path.read_text(encoding='utf-8')
    if "getTodayActivities(" not in content:
        injection = """
  // ── TODAY SURFACE ────────────────────────────────────────────────────────
  async getTodayActivities() {
    const response = await apiClient.get('/today');
    return response.data;
  },
"""
        content = content.replace(
            "// ── TASKS ─────────────────────────────────────────────────────────────",
            injection + "\\n  // ── TASKS ─────────────────────────────────────────────────────────────"
        )
        path.write_text(content, encoding='utf-8')
        print(f"Updated {path}")
    else:
        print(f"{path} already updated")

if __name__ == "__main__":
    generate_today_service()
    generate_today_api()
    update_app_py()
    update_frontend_api()
    print("Milestone 0 Foundation Applied.")
