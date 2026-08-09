"""
DeadlineOS — Activity Runtime Foundation
========================================
Defines the shared interfaces and runtime contracts for all actionable entities
(Tasks, Goals, Habits, Interventions) without forcing them into a single
monolithic database table.

This prepares the backend for the Phase 1 Activity Runtime Engine.
"""

from typing import Protocol, Any, Dict, Optional, List
from datetime import datetime


class ActivityInterface(Protocol):
    """
    Contract for any entity that can be executed, tracked, or scheduled
    by the Activity Runtime Engine.
    """

    @property
    def id(self) -> str: ...

    @property
    def title(self) -> str: ...

    @property
    def status(self) -> str: ...

    @property
    def user_id(self) -> str: ...

    def get_runtime_context(self) -> Dict[str, Any]:
        """Return the execution context needed by the runtime engine."""
        ...


class ActivityFacade:
    """
    A unified entry point for querying and mutating activities regardless of
    their underlying model (Task, Goal, Habit).
    """

    @classmethod
    def get_all_activities(
        cls, user_id: str, date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch and normalize all actionable items into a unified activity stream.
        """
        activities = []

        # 1. Fetch Tasks
        try:
            from models.task import Task

            tasks = Task.query.filter_by(user_id=user_id).all()
            for t in tasks:
                activities.append(
                    {
                        "type": "task",
                        "id": t.id,
                        "title": t.title,
                        "status": t.status,
                        "timestamp": t.created_at.isoformat() if t.created_at else None,
                        "data": t.serialize(),
                    }
                )
        except Exception:
            pass

        # 2. Fetch Goals/Habits
        try:
            from models.goal import Goal

            goals = Goal.query.filter_by(user_id=user_id).all()
            for g in goals:
                activities.append(
                    {
                        "type": "goal" if not g.is_habit else "habit",
                        "id": g.id,
                        "title": g.title,
                        "status": g.status,
                        "timestamp": g.created_at.isoformat() if g.created_at else None,
                        "data": g.serialize(),
                    }
                )
        except Exception:
            pass

        # Sort unified stream by timestamp descending
        activities.sort(
            key=lambda x: x.get("timestamp") or "1970-01-01T00:00:00", reverse=True
        )
        return activities

    @classmethod
    def execute_activity(
        cls, activity_id: str, activity_type: str, action: str, payload: dict
    ) -> bool:
        """
        Route an execution command to the appropriate underlying service.
        """
        if activity_type == "task":
            # Delegate to task service
            pass
        elif activity_type == "habit":
            # Delegate to habit logging
            pass

        return True
