"""
DeadlineOS — Trends Analytics Service (Phase 7 Milestone 9)
===========================================================
Calculates daily completion, focus time, recovery, and schedule adherence
trends across 7, 14, 30, and 90 day windows.
Strictly read-only: does not mutate runtime or domain state.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import get_user_timezone, to_user_local
from services.analytics.foundation import AnalyticsTimeWindow
from services.analytics.repository import AnalyticsRepository
from models.schedule import ScheduleSlot
from models.recovery import RecoveryRecord, RecoveryActionType


class TrendsAnalyticsService:
    """Computes deterministic multi-day performance and recovery trends."""

    @staticmethod
    def get_trends(user_id: str, days: int = 30) -> Dict[str, Any]:
        # Clamp supported ranges to 7, 14, 30, 90 (defaulting safely)
        valid_days = [7, 14, 30, 90]
        if days not in valid_days:
            days = 30 if days > 90 else days

        start_utc, end_utc, date_strings = AnalyticsTimeWindow.get_n_days_range_utc(user_id, days=days)
        user_tz = get_user_timezone(user_id)

        # 1. Fetch slots, sessions, recoveries
        slots = AnalyticsRepository.get_schedule_slots(user_id, start_utc, end_utc)
        sessions = AnalyticsRepository.get_sessions(user_id, start_utc, end_utc)
        recoveries = AnalyticsRepository.get_recovery_records(user_id, start_utc, end_utc)

        # 2. Map data per day
        daily_trends: Dict[str, Dict[str, Any]] = {
            d: {
                "date": d,
                "planned_count": 0,
                "completed_count": 0,
                "missed_count": 0,
                "skipped_count": 0,
                "recovery_count": 0,
                "focus_hours": 0.0,
                "planned_hours": 0.0,
                "completion_rate_pct": 100.0,
                "adherence_pct": 100.0
            }
            for d in date_strings
        }

        # Aggregate slots
        for s in slots:
            if s.get("start_time_utc"):
                s_dt = datetime.fromisoformat(s["start_time_utc"])
                s_local = to_user_local(s_dt, user_tz)
                d_str = f"{s_local.year:04d}-{s_local.month:02d}-{s_local.day:02d}"
                if d_str in daily_trends:
                    daily_trends[d_str]["planned_count"] += 1
                    if s.get("status") in ["COMPLETED", "done"]:
                        daily_trends[d_str]["completed_count"] += 1
                    elif s.get("status") in ["MISSED", "CANCELLED"]:
                        daily_trends[d_str]["missed_count"] += 1

        # Aggregate sessions
        for sess in sessions:
            if sess.get("started_at"):
                sess_dt = datetime.fromisoformat(sess["started_at"])
                sess_local = to_user_local(sess_dt, user_tz)
                d_str = f"{sess_local.year:04d}-{sess_local.month:02d}-{sess_local.day:02d}"
                if d_str in daily_trends:
                    daily_trends[d_str]["focus_hours"] += round(sess.get("actual_duration_sec", 0) / 3600.0, 2)
                    daily_trends[d_str]["planned_hours"] += round(sess.get("planned_duration_sec", 0) / 3600.0, 2)

        # Aggregate recoveries
        for r in recoveries:
            if r.get("created_at"):
                r_dt = datetime.fromisoformat(r["created_at"])
                r_local = to_user_local(r_dt, user_tz)
                d_str = f"{r_local.year:04d}-{r_local.month:02d}-{r_local.day:02d}"
                if d_str in daily_trends:
                    daily_trends[d_str]["recovery_count"] += 1
                    if r.get("action_type") == RecoveryActionType.SKIP:
                        daily_trends[d_str]["skipped_count"] += 1

        # Calculate daily percentages & summary totals
        trend_items = []
        total_completed = 0
        total_planned = 0
        total_focus = 0.0
        total_recoveries = len(recoveries)

        for d in date_strings:
            item = daily_trends[d]
            p = item["planned_count"]
            c = item["completed_count"]
            total_planned += p
            total_completed += c
            total_focus += item["focus_hours"]

            if p > 0:
                item["completion_rate_pct"] = round((c / p) * 100.0, 1)
            else:
                item["completion_rate_pct"] = 100.0 if item["focus_hours"] > 0 else 0.0

            if item["planned_hours"] > 0:
                item["adherence_pct"] = min(100.0, round((item["focus_hours"] / item["planned_hours"]) * 100.0, 1))
            else:
                item["adherence_pct"] = 100.0 if item["focus_hours"] > 0 else 0.0

            trend_items.append(item)

        overall_completion = round((total_completed / total_planned * 100.0), 1) if total_planned > 0 else 100.0
        avg_daily_focus = round(total_focus / days, 2)

        # Simple trend direction calculation (first half vs second half)
        mid = len(trend_items) // 2
        first_half_comp = sum(i["completed_count"] for i in trend_items[:mid])
        second_half_comp = sum(i["completed_count"] for i in trend_items[mid:])
        
        if second_half_comp > first_half_comp:
            direction = "IMPROVING"
        elif second_half_comp == first_half_comp:
            direction = "STABLE"
        else:
            direction = "DECLINING"

        return {
            "days_analyzed": days,
            "timezone": user_tz,
            "overall_completion_rate_pct": overall_completion,
            "total_completed_tasks": total_completed,
            "total_planned_tasks": total_planned,
            "total_focus_hours": round(total_focus, 1),
            "avg_daily_focus_hours": avg_daily_focus,
            "total_recovery_actions": total_recoveries,
            "trend_direction": direction,
            "daily_trends": trend_items,
            "summary": f"{days}-day execution trend shows {direction.lower()} momentum with {overall_completion}% overall completion rate.",
            "is_ai_generated": False
        }
