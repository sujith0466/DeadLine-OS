"""
DeadlineOS — Intervention Engine (Threat Detection)
=================================================
Proactively monitors all intelligence streams (Analytics, Calendar, Twin, Coach, Rescue)
to identify impending failures and generate actionable threats.
"""

import os
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid
from database.db import db
from models.intervention import Threat

class InterventionEngine:

    @classmethod
    def run_engine(cls, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Aggregates data across the system and evaluates conditions to spawn Threats.
        """
        from models.task import Task
        from services.availability_service import AvailabilityService
        from services.telemetry_service import TelemetryService
        import time
        from flask import g
        
        t0 = time.time()
        uid = user_id or getattr(g, "user_id", None)
        if not uid: return []
        
        # 1. Detect Overdue Tasks
        now = datetime.now(timezone.utc)
        overdue_tasks = Task.query.filter(Task.user_id == uid, Task.status == 'pending', Task.deadline < now).all()
        
        # Pre-fetch all active threats to prevent N+1 duplicate checks
        active_threats = Threat.query.filter_by(user_id=uid, status="active").all()
        active_messages = [t.message for t in active_threats if t.message]
        active_types = {t.type for t in active_threats}

        new_threats = []

        for task in overdue_tasks:
            # Check if an active threat already exists for this task
            if not any(task.title in msg for msg in active_messages):
                inv = Threat(
                    user_id=uid,
                    type="deadline_collision",
                    severity="Critical",
                    source="Planner",
                    message=f"Task '{task.title}' is overdue.",
                    details={"task_id": task.id}
                )
                new_threats.append(inv)
                active_messages.append(inv.message)
                
        # 2. Detect Workload Overload / Burnout
        avail = AvailabilityService.get_current_availability()
        if avail.get("utilization_percentage", 0) > 95:
             if "capacity_overload" not in active_types:
                 inv = Threat(
                    user_id=uid,
                    type="capacity_overload",
                    severity="High",
                    source="Planner",
                    message=f"Workload capacity is at {avail['utilization_percentage']}%. Burnout risk is extremely high.",
                    details={"utilization_percentage": avail.get("utilization_percentage")}
                 )
                 new_threats.append(inv)
                 active_types.add("capacity_overload")

        # 3. Detect Goal Deviation
        from models.goal import Goal
        at_risk_goals = Goal.query.filter_by(user_id=uid, status='at_risk').all()
        for goal in at_risk_goals:
             if not any(goal.title in msg for msg in active_messages):
                 inv = Threat(
                    user_id=uid,
                    type="goal_drift",
                    severity="Medium",
                    source="Goals",
                    message=f"Goal '{goal.title}' is deviating from its target trajectory.",
                    details={"goal_id": goal.id}
                 )
                 new_threats.append(inv)
                 active_messages.append(inv.message)

        # 4. Detect Habit Degradation
        from models.goal import Habit
        at_risk_habits = Habit.query.filter(Habit.user_id == uid, Habit.current_streak < 1).all()
        for habit in at_risk_habits:
             if not any(habit.name in msg for msg in active_messages):
                 inv = Threat(
                    user_id=uid,
                    type="habit_degradation",
                    severity="Low",
                    source="Habits",
                    message=f"Habit streak for '{habit.name}' has been broken.",
                    details={"habit_id": habit.id}
                 )
                 new_threats.append(inv)
                 active_messages.append(inv.message)

        if new_threats:
            db.session.add_all(new_threats)
            db.session.commit()
            
            from services.notification_service import NotificationService
            for t in new_threats:
                NotificationService.create_notification(
                    title=f"Threat Detected: {t.type.replace('_', ' ').title()}",
                    description=t.message,
                    severity=t.severity.lower(),
                    priority="Critical" if t.severity == "Critical" else "High",
                    module="Rescue",
                    entity_type="threat",
                    entity_id=t.id,
                    action_url=f"/rescue?threat={t.id}",
                    icon="AlertTriangle" if t.severity == "Critical" else "ShieldAlert",
                    color="rose" if t.severity == "Critical" else "amber",
                    category="Rescue"
                ) # NotificationService relies on global 'g' or standard channel hooks
        
        TelemetryService.log_execution("Threat Detection Engine", "Run Evaluation", "success", t0, 95)
        
        active = Threat.query.filter_by(user_id=uid, status="active").order_by(Threat.created_at.desc()).all()
        return [t.to_dict() for t in active]

    @classmethod
    def get_active_threats(cls, user_id: str = None, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns currently active threats with pagination."""
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        offset = (page - 1) * limit
        active = Threat.query.filter_by(user_id=uid, status="active").order_by(Threat.created_at.desc()).offset(offset).limit(limit).all()
        return [t.to_dict() for t in active]

    @classmethod
    def resolve_threat(cls, user_id: str = None, threat_id: str = None) -> bool:
        """Marks a threat as resolved."""
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        threat = Threat.query.filter_by(user_id=uid, id=threat_id).first()
        if threat:
            threat.status = "resolved"
            threat.resolved_at = datetime.now(timezone.utc)
            db.session.commit()
            return True
        return False

    @classmethod
    def trigger_evaluation(cls, user_id: str = None):
        """Event-driven hook to re-evaluate threats."""
        try:
            cls.run_engine(user_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Threat evaluation failed: {e}")


