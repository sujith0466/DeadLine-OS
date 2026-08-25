"""
DeadlineOS — Runtime Notification Listener
==========================================
Listens to Phase 1 Runtime Event Bus signals and produces execution notifications
without modifying the runtime state machine or blocking transactions.
"""

import logging
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.notification_engine import NotificationEngine
from services.notifications.reminder_service import ReminderService
from services.runtime.event_bus import (
    activity_started,
    activity_paused,
    activity_resumed,
    activity_completed,
    activity_interrupted
)
from utils.timezone import utc_now

logger = logging.getLogger(__name__)


@activity_started.connect
def on_activity_started(sender, **kwargs):
    payload = kwargs.get("payload", {})
    user_id = payload.get("user_id")
    entity_id = payload.get("entity_id")
    entity_type = payload.get("entity_type", "TASK")
    title = payload.get("title", f"Active {entity_type}")

    if not user_id or not entity_id:
        return

    try:
        NotificationEngine.schedule_notification(
            user_id=user_id,
            notification_type=NotificationType.RUNNING_SESSION,
            title=f"Session Started: {title}",
            description="Your focus timer is actively running.",
            scheduled_at=utc_now(),
            entity_type=entity_type,
            entity_id=entity_id,
            severity="info",
            action_url="/today",
            category="Runtime"
        )
    except Exception as e:
        logger.error(f"RuntimeListener failed on activity_started: {e}")


@activity_paused.connect
def on_activity_paused(sender, **kwargs):
    payload = kwargs.get("payload", {})
    user_id = payload.get("user_id")
    entity_id = payload.get("entity_id")
    entity_type = payload.get("entity_type", "TASK")
    title = payload.get("title", f"{entity_type}")

    if not user_id or not entity_id:
        return

    try:
        NotificationEngine.schedule_notification(
            user_id=user_id,
            notification_type=NotificationType.RUNNING_SESSION,
            title=f"Session Paused: {title}",
            description="Your session is on hold. Resume when ready.",
            scheduled_at=utc_now(),
            entity_type=entity_type,
            entity_id=entity_id,
            severity="medium",
            action_url="/today",
            category="Runtime"
        )
    except Exception as e:
        logger.error(f"RuntimeListener failed on activity_paused: {e}")


@activity_completed.connect
def on_activity_completed(sender, **kwargs):
    payload = kwargs.get("payload", {})
    user_id = payload.get("user_id")
    entity_id = payload.get("entity_id")
    entity_type = payload.get("entity_type", "TASK")
    title = payload.get("title", f"{entity_type}")

    if not user_id or not entity_id:
        return

    try:
        # Cancel any pending pre-alerts/reminders for this entity
        ReminderService.on_activity_completed_or_cancelled(user_id, entity_id)

        NotificationEngine.schedule_notification(
            user_id=user_id,
            notification_type=NotificationType.CONFIRMATION,
            title=f"Great job! Completed: {title}",
            description="Activity logged and recorded successfully.",
            scheduled_at=utc_now(),
            entity_type=entity_type,
            entity_id=entity_id,
            severity="info",
            action_url="/today",
            category="Runtime"
        )
    except Exception as e:
        logger.error(f"RuntimeListener failed on activity_completed: {e}")


@activity_interrupted.connect
def on_activity_interrupted(sender, **kwargs):
    payload = kwargs.get("payload", {})
    user_id = payload.get("user_id")
    entity_id = payload.get("entity_id")
    entity_type = payload.get("entity_type", "TASK")
    title = payload.get("title", f"{entity_type}")

    if not user_id or not entity_id:
        return

    try:
        NotificationEngine.schedule_notification(
            user_id=user_id,
            notification_type=NotificationType.CHECKIN,
            title=f"Session Interrupted: {title}",
            description="Your activity was paused due to inactivity. Click to resume.",
            scheduled_at=utc_now(),
            entity_type=entity_type,
            entity_id=entity_id,
            severity="high",
            action_url="/today",
            requires_confirmation=True,
            category="Runtime"
        )
    except Exception as e:
        logger.error(f"RuntimeListener failed on activity_interrupted: {e}")
