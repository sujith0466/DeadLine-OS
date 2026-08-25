"""
DeadlineOS — Notification Engine
================================
Core engine for determining notification eligibility, calculating trigger times,
enforcing deduplication, and synchronizing notification state with schedules.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from models.schedule import ScheduleSlot
from services.notifications.repository import NotificationRepository
from utils.timezone import get_user_timezone, to_utc, to_user_local, utc_now


class NotificationEngine:
    """Deterministic notification decision and scheduling engine."""

    @classmethod
    def generate_dedup_key(
        cls,
        user_id: str,
        notification_type: str,
        entity_id: str,
        scheduled_at: datetime
    ) -> str:
        """Constructs a deterministic idempotency key for notifications."""
        utc_ts = scheduled_at.replace(tzinfo=timezone.utc) if scheduled_at.tzinfo is None else scheduled_at
        ts_str = utc_ts.astimezone(timezone.utc).strftime("%Y%m%d%H%M")
        return f"{notification_type}:{entity_id}:{ts_str}"

    @classmethod
    def schedule_notification(
        cls,
        user_id: str,
        notification_type: str,
        title: str,
        description: Optional[str],
        scheduled_at: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        schedule_id: Optional[str] = None,
        severity: str = "info",
        priority: str = "info",
        action_url: Optional[str] = None,
        requires_confirmation: bool = False,
        confirmation_action: Optional[Dict[str, Any]] = None,
        category: str = "Planner"
    ) -> Optional[Notification]:
        """
        Creates or updates a scheduled notification record.
        Idempotent: Prevents duplicate notification creation with identical dedup key.
        """
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

        dedup_key = cls.generate_dedup_key(
            user_id=user_id,
            notification_type=notification_type,
            entity_id=entity_id or schedule_id or "generic",
            scheduled_at=scheduled_at
        )

        existing = NotificationRepository.get_by_deduplication_key(user_id, dedup_key)
        if existing:
            # Already planned or delivered
            return existing

        now = utc_now()
        status = NotificationStatus.DELIVERED if scheduled_at <= now else NotificationStatus.SCHEDULED
        delivered_at = now if status == NotificationStatus.DELIVERED else None

        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            description=description,
            severity=severity,
            priority=priority,
            entity_type=entity_type,
            entity_id=entity_id,
            schedule_id=schedule_id,
            scheduled_at=scheduled_at,
            delivered_at=delivered_at,
            status=status,
            deduplication_key=dedup_key,
            action_url=action_url,
            requires_confirmation=requires_confirmation,
            confirmation_action=confirmation_action,
            category=category
        )

        return NotificationRepository.save(notif)

    @classmethod
    def sync_schedule_slot_notifications(
        cls,
        slot: ScheduleSlot,
        pre_alert_minutes: int = 15,
        reminder_minutes: int = 5
    ) -> List[Notification]:
        """
        Schedules pre-alerts and reminders for a ScheduleSlot and cancels obsolete ones.
        """
        # Cancel any previous pending notifications for this slot
        NotificationRepository.cancel_pending_for_entity(slot.user_id, slot.id)

        if slot.status in ("CANCELLED", "COMPLETED"):
            return []

        slot_start = slot.start_time.replace(tzinfo=timezone.utc) if slot.start_time.tzinfo is None else slot.start_time
        created: List[Notification] = []

        # 1. Pre-Alert (e.g. 15 mins before start)
        if pre_alert_minutes > 0:
            pre_time = slot_start - timedelta(minutes=pre_alert_minutes)
            pre_notif = cls.schedule_notification(
                user_id=slot.user_id,
                notification_type=NotificationType.PRE_ALERT,
                title=f"Upcoming: {slot.task_title}",
                description=f"Starts in {pre_alert_minutes} minutes.",
                scheduled_at=pre_time,
                entity_type=slot.entity_type,
                entity_id=slot.entity_id or slot.id,
                schedule_id=slot.id,
                severity="info",
                action_url=f"/today",
                category="Planner"
            )
            if pre_notif:
                created.append(pre_notif)

        # 2. Activity Reminder (e.g. 5 mins before start)
        if reminder_minutes > 0:
            rem_time = slot_start - timedelta(minutes=reminder_minutes)
            rem_notif = cls.schedule_notification(
                user_id=slot.user_id,
                notification_type=NotificationType.REMINDER,
                title=f"Starting Soon: {slot.task_title}",
                description=f"Begins in {reminder_minutes} minutes. Get ready!",
                scheduled_at=rem_time,
                entity_type=slot.entity_type,
                entity_id=slot.entity_id or slot.id,
                schedule_id=slot.id,
                severity="medium",
                action_url=f"/today",
                category="Planner"
            )
            if rem_notif:
                created.append(rem_notif)

        return created
