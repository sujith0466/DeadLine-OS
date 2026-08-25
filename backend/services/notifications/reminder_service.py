"""
DeadlineOS — Reminder Service
=============================
Manages pre-alerts, multi-offset activity reminders, and deadline alerts.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from models.schedule import ScheduleSlot
from models.task import Task
from models.user_settings import UserSettings
from services.notifications.notification_engine import NotificationEngine
from services.notifications.repository import NotificationRepository
from utils.timezone import utc_now


class ReminderService:
    """Service for orchestrating pre-alerts, activity reminders, and deadline warnings."""

    DEFAULT_PRE_ALERT_OFFSETS = [15]     # 15 minutes before
    DEFAULT_REMINDER_OFFSETS = [5]       # 5 minutes before
    DEFAULT_DEADLINE_OFFSETS = [1440, 120] # 24h (1440m) and 2h (120m) before

    @classmethod
    def get_user_offsets(cls, user_id: str) -> Dict[str, List[int]]:
        """Retrieves user custom reminder offsets or defaults."""
        settings = UserSettings.query.get(user_id)
        if not settings or not settings.notifications:
            return {
                "pre_alerts": cls.DEFAULT_PRE_ALERT_OFFSETS,
                "reminders": cls.DEFAULT_REMINDER_OFFSETS,
                "deadlines": cls.DEFAULT_DEADLINE_OFFSETS
            }
        
        n_pref = settings.notifications
        return {
            "pre_alerts": n_pref.get("pre_alert_offsets", cls.DEFAULT_PRE_ALERT_OFFSETS),
            "reminders": n_pref.get("reminder_offsets", cls.DEFAULT_REMINDER_OFFSETS),
            "deadlines": n_pref.get("deadline_offsets", cls.DEFAULT_DEADLINE_OFFSETS)
        }

    @classmethod
    def register_schedule_reminders(cls, slot: ScheduleSlot) -> List[Notification]:
        """Registers all configured pre-alerts and reminders for a ScheduleSlot."""
        offsets = cls.get_user_offsets(slot.user_id)
        slot_start = slot.start_time.replace(tzinfo=timezone.utc) if slot.start_time.tzinfo is None else slot.start_time
        
        created = []
        
        # Pre-alerts
        for mins in offsets["pre_alerts"]:
            trigger_time = slot_start - timedelta(minutes=mins)
            notif = NotificationEngine.schedule_notification(
                user_id=slot.user_id,
                notification_type=NotificationType.PRE_ALERT,
                title=f"Pre-Alert: {slot.task_title}",
                description=f"Starts in {mins} minutes.",
                scheduled_at=trigger_time,
                entity_type=slot.entity_type,
                entity_id=slot.entity_id or slot.id,
                schedule_id=slot.id,
                severity="info",
                action_url="/today",
                category="Planner"
            )
            if notif:
                created.append(notif)

        # Imminent Reminders
        for mins in offsets["reminders"]:
            trigger_time = slot_start - timedelta(minutes=mins)
            notif = NotificationEngine.schedule_notification(
                user_id=slot.user_id,
                notification_type=NotificationType.REMINDER,
                title=f"Reminder: {slot.task_title}",
                description=f"Begins in {mins} minutes.",
                scheduled_at=trigger_time,
                entity_type=slot.entity_type,
                entity_id=slot.entity_id or slot.id,
                schedule_id=slot.id,
                severity="medium",
                action_url="/today",
                category="Planner"
            )
            if notif:
                created.append(notif)

        return created

    @classmethod
    def register_deadline_reminders(cls, task: Task) -> List[Notification]:
        """Registers deadline alerts for a Task."""
        if not task.deadline or task.status == "done":
            return []

        dl_utc = task.deadline.replace(tzinfo=timezone.utc) if task.deadline.tzinfo is None else task.deadline
        offsets = cls.get_user_offsets(task.user_id)
        
        created = []
        for mins in offsets["deadlines"]:
            trigger_time = dl_utc - timedelta(minutes=mins)
            hours_label = f"{mins // 60} hour(s)" if mins >= 60 else f"{mins} minutes"
            notif = NotificationEngine.schedule_notification(
                user_id=task.user_id,
                notification_type=NotificationType.REMINDER,
                title=f"Deadline Approaching: {task.title}",
                description=f"Due in {hours_label}.",
                scheduled_at=trigger_time,
                entity_type="TASK",
                entity_id=task.id,
                severity="high" if mins <= 120 else "medium",
                action_url="/today",
                category="Deadline"
            )
            if notif:
                created.append(notif)

        return created

    @classmethod
    def on_activity_completed_or_cancelled(cls, user_id: str, entity_id: str):
        """Cleans up pending/scheduled reminders when activity is completed or cancelled."""
        NotificationRepository.cancel_pending_for_entity(user_id, entity_id)
