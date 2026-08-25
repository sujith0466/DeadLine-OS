"""
DeadlineOS — Deadline Heatmap Service (Phase 7 Milestone 6)
===========================================================
Aggregates deadline density, task completions, and execution load
across calendar days and time-of-day buckets.
Strictly read-only: does not mutate runtime or domain state.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import get_user_timezone, to_user_local
from services.analytics.foundation import AnalyticsTimeWindow
from models.task import Task
from models.schedule import ScheduleSlot
from models.recovery import RecoveryRecord


class DeadlineHeatmapService:
    """Computes timezone-aware deadline intensity and completion heatmaps."""

    @staticmethod
    def generate_deadline_heatmap(user_id: str, days: int = 30) -> Dict[str, Any]:
        start_utc, end_utc, date_strings = AnalyticsTimeWindow.get_n_days_range_utc(user_id, days=days)
        user_tz = get_user_timezone(user_id)

        # 1. Fetch relevant tasks, slots, and recoveries
        tasks = Task.query.filter(Task.user_id == user_id).all()
        slots = (
            ScheduleSlot.query
            .filter(
                ScheduleSlot.user_id == user_id,
                ScheduleSlot.start_time >= start_utc,
                ScheduleSlot.start_time <= end_utc
            )
            .all()
        )
        recoveries = (
            RecoveryRecord.query
            .filter(
                RecoveryRecord.user_id == user_id,
                RecoveryRecord.created_at >= start_utc,
                RecoveryRecord.created_at <= end_utc
            )
            .all()
        )

        # 2. Build daily matrix
        daily_matrix = {d: {"date": d, "deadlines_count": 0, "completed_count": 0, "missed_count": 0, "recovery_count": 0, "density_level": 0} for d in date_strings}

        # Populate tasks deadlines
        for t in tasks:
            if t.deadline:
                t_local = to_user_local(t.deadline, user_tz)
                d_str = f"{t_local.year:04d}-{t_local.month:02d}-{t_local.day:02d}"
                if d_str in daily_matrix:
                    daily_matrix[d_str]["deadlines_count"] += 1

        # Populate schedule completions
        for s in slots:
            if s.start_time:
                s_local = to_user_local(s.start_time, user_tz)
                d_str = f"{s_local.year:04d}-{s_local.month:02d}-{s_local.day:02d}"
                if d_str in daily_matrix:
                    if s.status in ["COMPLETED", "done"]:
                        daily_matrix[d_str]["completed_count"] += 1
                    elif s.status in ["MISSED", "CANCELLED"]:
                        daily_matrix[d_str]["missed_count"] += 1

        # Populate recoveries
        for r in recoveries:
            if r.created_at:
                r_local = to_user_local(r.created_at, user_tz)
                d_str = f"{r_local.year:04d}-{r_local.month:02d}-{r_local.day:02d}"
                if d_str in daily_matrix:
                    daily_matrix[d_str]["recovery_count"] += 1

        # Assign density levels (0 to 4)
        heatmap_items = []
        for d in date_strings:
            item = daily_matrix[d]
            load_factor = item["deadlines_count"] + item["completed_count"]
            if load_factor >= 8:
                item["density_level"] = 4
            elif load_factor >= 5:
                item["density_level"] = 3
            elif load_factor >= 2:
                item["density_level"] = 2
            elif load_factor >= 1:
                item["density_level"] = 1
            else:
                item["density_level"] = 0
            heatmap_items.append(item)

        # 3. Time-of-Day distribution across the dataset
        time_of_day_buckets = {
            "morning": 0,    # 06:00 - 12:00
            "afternoon": 0,  # 12:00 - 18:00
            "evening": 0,    # 18:00 - 22:00
            "night": 0       # 22:00 - 06:00
        }

        for s in slots:
            if s.start_time:
                s_local = to_user_local(s.start_time, user_tz)
                hr = s_local.hour
                if 6 <= hr < 12:
                    time_of_day_buckets["morning"] += 1
                elif 12 <= hr < 18:
                    time_of_day_buckets["afternoon"] += 1
                elif 18 <= hr < 22:
                    time_of_day_buckets["evening"] += 1
                else:
                    time_of_day_buckets["night"] += 1

        return {
            "days_analyzed": days,
            "timezone": user_tz,
            "heatmap": heatmap_items,
            "time_of_day_distribution": time_of_day_buckets,
            "summary": f"Calculated deadline and completion density over {days} days.",
            "is_ai_generated": False
        }
