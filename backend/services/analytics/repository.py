"""
DeadlineOS — Analytics Read-Only Data Repository
================================================
Queries historical domain records using efficient database filtering and aggregations.
Strictly read-only: never mutates authoritative models.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from database.db import db
from models.runtime_session import RuntimeSession
from models.runtime_state import RuntimeState
from models.schedule import ScheduleSlot, Schedule
from models.recovery import RecoveryRecord
from models.notification import Notification
from models.task import Task
from models.goal import Goal, Milestone, Habit, HabitLog


class AnalyticsRepository:
    """Read-only query service for analytics aggregations."""

    @staticmethod
    def get_sessions(user_id: str, start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves all RuntimeSessions executed by user in the given UTC time window.
        Joins with RuntimeState to verify user ownership and extract entity details.
        """
        query = (
            db.session.query(RuntimeSession, RuntimeState)
            .join(RuntimeState, RuntimeSession.runtime_state_id == RuntimeState.id)
            .filter(
                RuntimeState.user_id == user_id,
                RuntimeSession.started_at >= start_utc,
                RuntimeSession.started_at <= end_utc
            )
            .order_by(RuntimeSession.started_at.asc())
        )
        
        results = []
        for session, state in query.all():
            actual_sec = 0
            if session.ended_at and session.started_at:
                total_duration = int((session.ended_at - session.started_at).total_seconds())
                actual_sec = max(0, total_duration - (session.paused_duration_sec or 0))

            results.append({
                "session_id": session.id,
                "runtime_state_id": session.runtime_state_id,
                "entity_type": state.entity_type,
                "entity_id": state.entity_id,
                "status": state.status,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "planned_duration_sec": session.planned_duration_sec or 0,
                "paused_duration_sec": session.paused_duration_sec or 0,
                "actual_duration_sec": actual_sec,
                "completion_source": session.completion_source
            })
        return results

    @staticmethod
    def get_schedule_slots(user_id: str, start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves all ScheduleSlots planned or active in the given UTC time window.
        """
        slots = (
            ScheduleSlot.query
            .filter(
                ScheduleSlot.user_id == user_id,
                ScheduleSlot.start_time >= start_utc,
                ScheduleSlot.start_time <= end_utc
            )
            .order_by(ScheduleSlot.start_time.asc())
            .all()
        )
        return [slot.to_dict() for slot in slots]

    @staticmethod
    def get_recovery_records(user_id: str, start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves all RecoveryRecords created in the given UTC time window.
        """
        records = (
            RecoveryRecord.query
            .filter(
                RecoveryRecord.user_id == user_id,
                RecoveryRecord.created_at >= start_utc,
                RecoveryRecord.created_at <= end_utc
            )
            .order_by(RecoveryRecord.created_at.asc())
            .all()
        )
        return [rec.to_dict() for rec in records]

    @staticmethod
    def get_notifications(user_id: str, start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves notifications delivered or scheduled in the given UTC window.
        """
        notifications = (
            Notification.query
            .filter(
                Notification.user_id == user_id,
                Notification.created_at >= start_utc,
                Notification.created_at <= end_utc
            )
            .order_by(Notification.created_at.asc())
            .all()
        )
        return [n.to_dict() for n in notifications]

    @staticmethod
    def get_tasks_overview(user_id: str) -> Dict[str, Any]:
        """
        Calculates snapshot task statistics (pending, done, overdue, completion rate).
        """
        tasks = Task.query.filter(Task.user_id == user_id).all()
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        pending = sum(1 for t in tasks if t.status == "pending")
        in_progress = sum(1 for t in tasks if t.status == "in_progress")
        overdue = sum(1 for t in tasks if t.is_overdue)
        
        return {
            "total_tasks": total,
            "completed_tasks": done,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "overdue_tasks": overdue,
            "completion_rate_pct": round((done / total * 100), 1) if total > 0 else 100.0
        }

    @staticmethod
    def get_goals_overview(user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves active goals with computed progress and milestone completion rates.
        """
        goals = Goal.query.filter(Goal.user_id == user_id, Goal.archived == False).all()
        results = []
        for g in goals:
            ms = g.milestones or []
            total_ms = len(ms)
            completed_ms = sum(1 for m in ms if m.completed)
            ms_pct = round((completed_ms / total_ms * 100), 1) if total_ms > 0 else (g.progress_percentage or 0)
            
            results.append({
                "id": g.id,
                "title": g.title,
                "category": g.category,
                "target_date": g.target_date,
                "status": g.status,
                "priority": g.priority,
                "health_score": g.health_score,
                "progress_percentage": ms_pct,
                "total_milestones": total_ms,
                "completed_milestones": completed_ms
            })
        return results

    @staticmethod
    def get_habits_overview(user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves active habits with streaks, consistency velocity, and recent check-in counts.
        """
        habits = Habit.query.filter(Habit.user_id == user_id, Habit.archived == False).all()
        results = []
        for h in habits:
            results.append({
                "id": h.id,
                "name": h.name,
                "category": h.category,
                "frequency": h.frequency,
                "current_streak": h.current_streak,
                "longest_streak": h.longest_streak,
                "completion_rate": h.completion_rate,
                "momentum_score": h.momentum_score,
                "last_checkin_date": h.last_checkin_date
            })
        return results
