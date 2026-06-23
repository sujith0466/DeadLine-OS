"""
DeadlineOS — Intervention Engine
================================
Proactively monitors all intelligence streams (Analytics, Calendar, Twin, Coach, Rescue)
to identify impending failures and generate actionable interventions.
Designed for future expansion: Voice Copilot, Meeting Automation, Calendar AI.
"""

import os
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid
from database.db import db
from models.intervention import Intervention

class InterventionEngine:

    @classmethod
    def run_engine(cls) -> List[Dict[str, Any]]:
        """
        Aggregates data across the system and evaluates conditions to spawn interventions.
        """
        from models.task import Task
        from services.availability_service import AvailabilityService
        from services.telemetry_service import TelemetryService
        import time
        
        t0 = time.time()
        
        # 1. Detect Overdue Tasks
        now = datetime.now(timezone.utc)
        overdue_tasks = Task.query.filter(Task.status == 'pending', Task.deadline < now).all()
        
        # Pre-fetch all active interventions to prevent N+1 duplicate checks
        active_interventions = Intervention.query.filter_by(resolved=False).all()
        active_messages = [inv.message for inv in active_interventions if inv.message]
        active_types = {inv.type for inv in active_interventions}

        new_interventions = []

        for task in overdue_tasks:
            # Check if an active intervention already exists for this task in memory
            if not any(task.title in msg for msg in active_messages):
                inv = Intervention(
                    type="overdue_task",
                    severity="Critical",
                    priority_score=95,
                    confidence_score=100,
                    trigger_source="Intervention Engine",
                    message=f"Task '{task.title}' is overdue. Immediate rescheduling required.",
                    recommended_action={
                        "action_type": "calendar_reschedule",
                        "target_task_id": task.id,
                        "target_task": task.title,
                        "voice_prompt_ready": f"Would you like me to move '{task.title}' to your next available block?"
                    }
                )
                new_interventions.append(inv)
                active_messages.append(inv.message)
                
        # 2. Detect Workload Overload / Burnout
        avail = AvailabilityService.get_current_availability()
        if avail.get("utilization_percentage", 0) > 95:
             if "workload_overload" not in active_types:
                 inv = Intervention(
                    type="workload_overload",
                    severity="High",
                    priority_score=90,
                    confidence_score=90,
                    trigger_source="Availability Engine",
                    message=f"Workload capacity is at {avail['utilization_percentage']}%. Burnout risk is extremely high.",
                    recommended_action={
                        "action_type": "focus_block_injection",
                        "voice_prompt_ready": "Your workload is critical. Shall I activate Rescue Mode and clear non-essential meetings?"
                    }
                 )
                 new_interventions.append(inv)
                 active_types.add("workload_overload")

        # 3. Detect Goal Deviation
        from models.goal import Goal
        at_risk_goals = Goal.query.filter_by(status='at_risk').all()
        for goal in at_risk_goals:
             if not any(goal.title in msg for msg in active_messages):
                 inv = Intervention(
                    type="goal_deviation",
                    severity="Medium",
                    priority_score=70,
                    confidence_score=85,
                    trigger_source="Goal Tracking",
                    message=f"Goal '{goal.title}' is deviating from its target trajectory.",
                    recommended_action={
                        "action_type": "invoke_planning_agent",
                        "target_goal_id": goal.id,
                        "voice_prompt_ready": f"Would you like me to restructure your week to prioritize '{goal.title}'?"
                    }
                 )
                 new_interventions.append(inv)
                 active_messages.append(inv.message)

        # 4. Detect Habit Degradation
        from models.goal import Habit
        at_risk_habits = Habit.query.filter(Habit.current_streak < 1).all()
        for habit in at_risk_habits:
             if not any(habit.name in msg for msg in active_messages):
                 inv = Intervention(
                    type="habit_degradation",
                    severity="Low",
                    priority_score=50,
                    confidence_score=95,
                    trigger_source="Habit Tracking",
                    message=f"Habit streak for '{habit.name}' has been broken.",
                    recommended_action={
                        "action_type": "coach_challenge",
                        "target_habit_id": habit.id,
                        "voice_prompt_ready": f"You've missed '{habit.name}'. Let's commit to a 10-minute session today."
                    }
                 )
                 new_interventions.append(inv)
                 active_messages.append(inv.message)

        if new_interventions:
            db.session.add_all(new_interventions)
        db.session.commit()
        
        TelemetryService.log_execution("Intervention Engine", "Run Evaluation", "success", t0, 95)
        
        active = Intervention.query.filter_by(resolved=False).order_by(Intervention.priority_score.desc()).all()
        return [i.to_dict() for i in active]

    @classmethod
    def get_active_interventions(cls, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns currently active interventions with pagination."""
        offset = (page - 1) * limit
        active = Intervention.query.filter_by(resolved=False).order_by(Intervention.priority_score.desc()).offset(offset).limit(limit).all()
        return [i.to_dict() for i in active]

    @classmethod
    def resolve_intervention(cls, intervention_id: str) -> bool:
        """Marks an intervention as resolved."""
        intervention = Intervention.query.get(intervention_id)
        if intervention:
            intervention.resolved = True
            intervention.resolved_at = datetime.now(timezone.utc)
            db.session.commit()
            return True
        
        return False


