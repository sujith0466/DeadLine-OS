"""
DeadlineOS — Goal Progress Intelligence Service (Phase 7 Milestone 5)
====================================================================
Computes deterministic goal advancement velocity, milestone completion rates,
target date proximity, and explainable execution risk indicators.
Strictly read-only: does not mutate goal or milestone records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import utc_now, get_user_timezone
from models.goal import Goal, Milestone
from models.task import Task


class GoalProgressService:
    """Computes explainable goal progress and execution trajectory analytics."""

    @staticmethod
    def calculate_goal_progress(user_id: str) -> Dict[str, Any]:
        goals = Goal.query.filter(Goal.user_id == user_id, Goal.archived == False).all()
        now_utc = utc_now()

        if not goals:
            return {
                "active_goals_count": 0,
                "overall_completion_rate_pct": 100.0,
                "at_risk_goals_count": 0,
                "goals": [],
                "summary": "No active goals configured.",
                "is_ai_generated": False
            }

        goal_results = []
        total_progress = 0
        at_risk_count = 0

        for g in goals:
            milestones = g.milestones or []
            total_ms = len(milestones)
            completed_ms = sum(1 for m in milestones if m.completed)
            
            # Linked tasks
            linked_tasks = Task.query.filter(Task.goal_id == g.id).all()
            total_tasks = len(linked_tasks)
            done_tasks = sum(1 for t in linked_tasks if t.status == "done")

            if total_ms > 0:
                progress_pct = round((completed_ms / total_ms) * 100.0, 1)
            elif total_tasks > 0:
                progress_pct = round((done_tasks / total_tasks) * 100.0, 1)
            else:
                progress_pct = float(g.progress_percentage or 0.0)

            total_progress += progress_pct

            # Target date proximity
            days_remaining = None
            risk_level = "ON_TRACK"
            risk_factors = []

            if g.target_date:
                try:
                    t_parts = [int(p) for p in g.target_date.split("-")]
                    target_dt = datetime(t_parts[0], t_parts[1], t_parts[2], 23, 59, 59, tzinfo=timezone.utc)
                    days_remaining = (target_dt - now_utc).days

                    if days_remaining < 0 and progress_pct < 100.0:
                        risk_level = "OVERDUE"
                        risk_factors.append(f"Target date was {abs(days_remaining)} days ago with incomplete progress.")
                        at_risk_count += 1
                    elif days_remaining <= 7 and progress_pct < 50.0:
                        risk_level = "AT_RISK"
                        risk_factors.append(f"Only {days_remaining} days remaining with {progress_pct}% progress.")
                        at_risk_count += 1
                    elif days_remaining <= 14 and progress_pct < 30.0:
                        risk_level = "MODERATE_RISK"
                        risk_factors.append(f"Advancement velocity is low relative to {days_remaining} days remaining.")
                except Exception:
                    pass

            if progress_pct >= 100.0:
                risk_level = "COMPLETED"

            goal_results.append({
                "goal_id": g.id,
                "title": g.title,
                "category": g.category or "General",
                "status": g.status,
                "priority": g.priority or "Medium",
                "progress_percentage": progress_pct,
                "health_score": g.health_score or 100,
                "target_date": g.target_date,
                "days_remaining": days_remaining,
                "total_milestones": total_ms,
                "completed_milestones": completed_ms,
                "total_linked_tasks": total_tasks,
                "completed_linked_tasks": done_tasks,
                "risk_level": risk_level,
                "risk_factors": risk_factors
            })

        avg_completion = round(total_progress / len(goals), 1)

        return {
            "active_goals_count": len(goals),
            "overall_completion_rate_pct": avg_completion,
            "at_risk_goals_count": at_risk_count,
            "goals": goal_results,
            "summary": f"Tracking {len(goals)} active goals with an average progress of {avg_completion}%.",
            "is_ai_generated": False
        }
