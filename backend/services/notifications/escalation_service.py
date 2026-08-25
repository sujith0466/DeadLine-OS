"""
DeadlineOS — Notification Escalation Service
============================================
Provides bounded, multi-tiered escalation for critical overdue activities and deadlines.
Guarantees a hard cap of 3 escalation levels per entity to prevent notification exhaustion.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from models.schedule import ScheduleSlot
from models.task import Task
from models.runtime_state import RuntimeState
from services.notifications.repository import NotificationRepository
from utils.timezone import utc_now


class EscalationService:
    """Evaluates commitment delinquency and issues bounded escalations."""

    MAX_TIER = 3

    @classmethod
    def get_current_tier(cls, user_id: str, entity_id: str) -> int:
        """Returns the highest escalation tier already emitted for this entity."""
        escalations = (
            Notification.query.filter_by(
                user_id=user_id,
                entity_id=entity_id,
                notification_type=NotificationType.ESCALATION
            ).all()
        )
        if not escalations:
            return 0
        return len(escalations)

    @classmethod
    def evaluate_escalations(cls, user_id: str) -> List[Notification]:
        """
        Scans overdue tasks and slots. If delinquency criteria are met,
        escalates to the next tier up to MAX_TIER.
        """
        now = utc_now()
        created_escalations: List[Notification] = []

        # 1. Overdue Scheduled Slots (passed end_time without completion or start)
        overdue_slots = (
            ScheduleSlot.query.filter_by(user_id=user_id, status="PLANNED")
            .filter(ScheduleSlot.end_time < now)
            .all()
        )

        for slot in overdue_slots:
            entity_id = slot.entity_id or slot.id
            current_tier = cls.get_current_tier(user_id, entity_id)
            if current_tier >= cls.MAX_TIER:
                continue

            next_tier = current_tier + 1
            dedup_key = f"ESCALATION:{entity_id}:T{next_tier}"
            if NotificationRepository.get_by_deduplication_key(user_id, dedup_key):
                continue

            severity = "critical" if next_tier == cls.MAX_TIER else "high"
            notif = Notification(
                user_id=user_id,
                notification_type=NotificationType.ESCALATION,
                title=f"[Tier {next_tier} Alert] Overdue: {slot.task_title}",
                description=f"Scheduled slot ended without recorded completion. Action required.",
                severity=severity,
                priority="urgent" if next_tier == cls.MAX_TIER else "high",
                status=NotificationStatus.DELIVERED,
                scheduled_at=now,
                delivered_at=now,
                entity_type=slot.entity_type,
                entity_id=entity_id,
                schedule_id=slot.id,
                deduplication_key=dedup_key,
                requires_confirmation=True,
                confirmation_action={
                    "tier": next_tier,
                    "options": [
                        {"label": "Start Now", "action": "START_ACTIVITY"},
                        {"label": "Mark Done", "action": "COMPLETE_ACTIVITY"},
                        {"label": "Dismiss", "action": "DISMISS"}
                    ]
                },
                action_url="/today",
                category="Escalation"
            )
            NotificationRepository.save(notif)
            created_escalations.append(notif)

        return created_escalations
