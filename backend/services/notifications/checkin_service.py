"""
DeadlineOS — Assisted Auto Check-In Service
==========================================
Detects scheduled activities that have passed their start time without an active
runtime session, and creates an actionable confirmation check-in notification.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from services.notifications.notification_engine import NotificationEngine
from services.notifications.repository import NotificationRepository
from services.scheduling.repository import SchedulingRepository
from utils.timezone import utc_now


class CheckInService:
    """Evaluates unstarted activities and emits assisted check-ins."""

    DEFAULT_GRACE_MINUTES = 10

    @classmethod
    def evaluate_unstarted_activities(
        cls,
        user_id: str,
        grace_minutes: int = DEFAULT_GRACE_MINUTES
    ) -> List[Notification]:
        """
        Finds scheduled slots for user_id where:
        1. slot.start_time <= (now - grace_minutes)
        2. slot.end_time > now
        3. slot.status == 'PLANNED'
        4. No active RUNNING RuntimeState exists for the entity
        """
        now = utc_now()
        threshold_start = now - timedelta(minutes=grace_minutes)

        # Query user slots around today
        slots = SchedulingRepository.get_slots_by_user(
            user_id=user_id,
            start_time=now - timedelta(hours=4),
            end_time=now + timedelta(hours=1),
            status="PLANNED"
        )

        created_checkins: List[Notification] = []

        for slot in slots:
            slot_start = slot.start_time.replace(tzinfo=timezone.utc) if slot.start_time.tzinfo is None else slot.start_time
            slot_end = slot.end_time.replace(tzinfo=timezone.utc) if slot.end_time.tzinfo is None else slot.end_time

            # Check eligibility
            if slot_start <= threshold_start and slot_end > now:
                entity_id = slot.entity_id or slot.id
                
                # Check if already running in runtime
                active_state = RuntimeState.query.filter_by(
                    user_id=user_id,
                    entity_id=entity_id,
                    status="RUNNING"
                ).first()

                if active_state:
                    continue  # Already actively executing

                # Deduplication key for this check-in
                dedup_key = f"CHECKIN:{slot.id}:{slot_start.strftime('%Y%m%d%H%M')}"
                existing = NotificationRepository.get_by_deduplication_key(user_id, dedup_key)
                if existing:
                    continue

                minutes_late = int((now - slot_start).total_seconds() / 60.0)
                
                notif = Notification(
                    user_id=user_id,
                    notification_type=NotificationType.CHECKIN,
                    title=f"Check-In: {slot.task_title}",
                    description=f"Your scheduled activity started {minutes_late} minutes ago. Did you start?",
                    severity="medium",
                    status=NotificationStatus.DELIVERED,
                    scheduled_at=now,
                    delivered_at=now,
                    entity_type=slot.entity_type,
                    entity_id=entity_id,
                    schedule_id=slot.id,
                    deduplication_key=dedup_key,
                    requires_confirmation=True,
                    confirmation_action={
                        "options": [
                            {"label": "Start Now", "action": "START_ACTIVITY"},
                            {"label": "Dismiss", "action": "DISMISS"}
                        ]
                    },
                    action_url="/today",
                    category="CheckIn"
                )
                NotificationRepository.save(notif)
                created_checkins.append(notif)

        return created_checkins
