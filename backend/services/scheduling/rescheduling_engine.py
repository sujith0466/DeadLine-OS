"""
DeadlineOS — Rescheduling Engine
================================
Safely shifts, adjusts, or moves scheduled activities while guaranteeing that
historical RuntimeSessions, completed states, and audit trails remain untouched.
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone, timedelta
from database.db import db
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from services.scheduling.repository import SchedulingRepository
from services.scheduling.conflict_service import ConflictDetectionService
from utils.timezone import utc_now


class ReschedulingEngine:
    """Handles deterministic slot movements and safe conflict resolutions."""

    @classmethod
    def reschedule_slot(
        cls,
        user_id: str,
        slot_id: str,
        new_start_time: datetime,
        new_end_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        force_cascade: bool = False
    ) -> Dict[str, Any]:
        """
        Moves a slot to a new time window.
        - Validates against conflicts.
        - Preserves existing Runtime history (does not mutate completed RuntimeSessions).
        - Returns before/after snapshot.
        """
        slot = SchedulingRepository.get_slot_by_id(slot_id)
        if not slot or slot.user_id != user_id:
            return {
                "success": False,
                "error": "Slot not found or unauthorized"
            }

        if new_start_time.tzinfo is None:
            new_start_time = new_start_time.replace(tzinfo=timezone.utc)

        # Calculate new end time
        if new_end_time:
            if new_end_time.tzinfo is None:
                new_end_time = new_end_time.replace(tzinfo=timezone.utc)
        elif duration_minutes:
            new_end_time = new_start_time + timedelta(minutes=duration_minutes)
        else:
            current_dur = (slot.end_time - slot.start_time).total_seconds() / 60.0
            new_end_time = new_start_time + timedelta(minutes=int(current_dur or 60))

        # Capture Before State
        before_state = slot.to_dict()

        # Check for conflicts excluding the slot itself
        conflict_report = ConflictDetectionService.check_conflicts(
            user_id=user_id,
            start_time=new_start_time,
            end_time=new_end_time,
            entity_id=slot.entity_id,
            exclude_slot_id=slot.id,
            allow_past=True
        )

        cascaded_shifts: List[Dict[str, Any]] = []

        if conflict_report["has_conflict"]:
            if not force_cascade:
                return {
                    "success": False,
                    "error": "CONFLICT_DETECTED",
                    "conflict_report": conflict_report,
                    "before": before_state
                }
            else:
                # Resolve by cascading conflicting slots forward
                for conf in conflict_report["conflicts"]:
                    if conf.get("slot_id"):
                        conf_slot = SchedulingRepository.get_slot_by_id(conf["slot_id"])
                        if conf_slot:
                            conf_dur = (conf_slot.end_time - conf_slot.start_time)
                            c_before = conf_slot.to_dict()
                            conf_slot.start_time = new_end_time + timedelta(minutes=10)
                            conf_slot.end_time = conf_slot.start_time + conf_dur
                            conf_slot.status = "RESCHEDULED"
                            SchedulingRepository.save_slot(conf_slot)
                            cascaded_shifts.append({
                                "slot_id": conf_slot.id,
                                "before": c_before,
                                "after": conf_slot.to_dict()
                            })

        # Apply update to target slot
        slot.start_time = new_start_time
        slot.end_time = new_end_time
        slot.status = "RESCHEDULED"
        slot.updated_at = utc_now()
        SchedulingRepository.save_slot(slot)

        after_state = slot.to_dict()

        return {
            "success": True,
            "slot_id": slot.id,
            "before": before_state,
            "after": after_state,
            "cascaded_shifts": cascaded_shifts
        }
