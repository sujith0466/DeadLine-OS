"""
DeadlineOS — Conflict Detection Service
=======================================
Analyzes proposed schedule slots for time overlaps, duplicate assignments,
invalid durations, and window bounds violations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from models.schedule import ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from utils.timezone import utc_now


class ConflictDetectionService:
    """Deterministic schedule conflict analyzer."""

    @classmethod
    def check_conflicts(
        cls,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
        exclude_slot_id: Optional[str] = None,
        allow_past: bool = False
    ) -> Dict[str, Any]:
        """
        Validates a proposed slot against existing commitments and validity rules.
        Returns a structured dictionary with conflict diagnostics.
        """
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        conflicts: List[Dict[str, Any]] = []

        # 1. Validate start / end sanity
        if end_time <= start_time:
            conflicts.append({
                "reason": "INVALID_DURATION",
                "message": "End time must be strictly after start time.",
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            })

        # 2. Validate past scheduling
        now = utc_now()
        if not allow_past and end_time < (now - timedelta(minutes=5)):
            conflicts.append({
                "reason": "PAST_TIME",
                "message": "Cannot schedule slots entirely in the past.",
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            })

        # 3. Validate window bounds
        if window_start:
            w_start = window_start.replace(tzinfo=timezone.utc) if window_start.tzinfo is None else window_start
            if start_time < w_start:
                conflicts.append({
                    "reason": "OUT_OF_WINDOW",
                    "message": "Start time occurs before the allowed window start.",
                    "window_start": w_start.isoformat(),
                    "start": start_time.isoformat()
                })
        if window_end:
            w_end = window_end.replace(tzinfo=timezone.utc) if window_end.tzinfo is None else window_end
            if end_time > w_end:
                conflicts.append({
                    "reason": "OUT_OF_WINDOW",
                    "message": "End time exceeds the allowed window end.",
                    "window_end": w_end.isoformat(),
                    "end": end_time.isoformat()
                })

        # 4. Check time overlap with existing active user slots
        existing_slots = SchedulingRepository.get_slots_by_user(
            user_id=user_id,
            start_time=start_time - timedelta(days=1),
            end_time=end_time + timedelta(days=1),
            status=None
        )

        for slot in existing_slots:
            if slot.status == "CANCELLED" or (exclude_slot_id and slot.id == exclude_slot_id):
                continue

            s_start = slot.start_time.replace(tzinfo=timezone.utc) if slot.start_time.tzinfo is None else slot.start_time
            s_end = slot.end_time.replace(tzinfo=timezone.utc) if slot.end_time.tzinfo is None else slot.end_time

            # Direct time overlap condition: (start < s_end) and (end > s_start)
            if start_time < s_end and end_time > s_start:
                conflicts.append({
                    "reason": "TIME_OVERLAP",
                    "slot_id": slot.id,
                    "entity_id": slot.entity_id or slot.task_id,
                    "title": slot.task_title,
                    "start": s_start.isoformat(),
                    "end": s_end.isoformat(),
                    "message": f"Overlaps with existing slot '{slot.task_title}'."
                })

            # Check duplicate same-activity scheduling on same date if entity_id is provided
            if entity_id and (slot.entity_id == entity_id or slot.task_id == entity_id):
                if s_start.date() == start_time.date() and not (start_time < s_end and end_time > s_start):
                    conflicts.append({
                        "reason": "DUPLICATE_ACTIVITY",
                        "slot_id": slot.id,
                        "entity_id": entity_id,
                        "title": slot.task_title,
                        "start": s_start.isoformat(),
                        "end": s_end.isoformat(),
                        "message": f"Activity '{slot.task_title}' is already scheduled on this day."
                    })

        return {
            "has_conflict": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts
        }
