"""
DeadlineOS — Priority Scheduler Service
=======================================
Calculates deterministic, priority-weighted slot allocations across competing activities.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from models.schedule import ScheduleSlot
from services.scheduling.flexible_window_engine import FlexibleWindowEngine
from services.scheduling.repository import SchedulingRepository
from utils.timezone import utc_now


class PriorityScheduler:
    """Deterministic, explainable priority-driven schedule allocator."""

    @classmethod
    def calculate_effective_priority(
        cls,
        priority_score: int,
        deadline: Optional[datetime],
        reference_time: datetime
    ) -> float:
        """
        Calculates a deterministic composite priority score.
        Formula: base_priority (0-100) + deadline_urgency_bonus (up to +100).
        """
        base = float(priority_score or 50)
        if not deadline:
            return base

        dl_utc = deadline.replace(tzinfo=timezone.utc) if deadline.tzinfo is None else deadline
        ref_utc = reference_time.replace(tzinfo=timezone.utc) if reference_time.tzinfo is None else reference_time

        hours_to_deadline = (dl_utc - ref_utc).total_seconds() / 3600.0

        # Urgent bonus: < 24h = +50, < 6h = +80, overdue = +100
        urgency_bonus = 0.0
        if hours_to_deadline <= 0:
            urgency_bonus = 100.0
        elif hours_to_deadline <= 6:
            urgency_bonus = 80.0
        elif hours_to_deadline <= 24:
            urgency_bonus = 50.0
        elif hours_to_deadline <= 72:
            urgency_bonus = 20.0

        return base + urgency_bonus

    @classmethod
    def plan_priority_schedule(
        cls,
        user_id: str,
        activities: List[Dict[str, Any]],
        window_start: datetime,
        window_end: datetime,
        buffer_minutes: int = 10,
        persist: bool = False
    ) -> Dict[str, Any]:
        """
        Takes a list of proposed activities, sorts them deterministically by effective priority,
        and places each into the earliest available non-conflicting slot within the window.
        """
        ref_now = window_start

        # Decorate with effective priority
        decorated = []
        for a in activities:
            p_score = a.get("priority", 50)
            dl_str = a.get("deadline")
            dl = datetime.fromisoformat(dl_str.replace("Z", "+00:00")) if dl_str else None
            eff_p = cls.calculate_effective_priority(p_score, dl, ref_now)
            decorated.append({
                **a,
                "_effective_priority": eff_p,
                "_duration": a.get("duration_minutes", 60)
            })

        # Sort descending by effective priority, then ascending by duration for equal priorities
        decorated.sort(key=lambda x: (-x["_effective_priority"], x["_duration"]))

        scheduled_slots: List[Dict[str, Any]] = []
        backlog: List[Dict[str, Any]] = []

        # Running placement tracking
        temp_commitments: List[tuple] = []

        for item in decorated:
            dur = item["_duration"]
            
            # Find earliest available slot considering both repository commitments and newly placed items
            slot = FlexibleWindowEngine.find_best_slot(
                user_id=user_id,
                window_start=window_start,
                window_end=window_end,
                duration_minutes=dur,
                buffer_minutes=buffer_minutes
            )

            # Check if newly found slot collides with items placed in this batch
            if slot:
                s_start, s_end = slot
                collides_batch = any(
                    s_start < b_end and s_end > b_start
                    for (b_start, b_end) in temp_commitments
                )
                if collides_batch:
                    # Find next placement after the latest batch commitment
                    latest_end = max(b_end for (b_start, b_end) in temp_commitments)
                    next_start = latest_end + timedelta(minutes=buffer_minutes)
                    if (window_end - next_start) >= timedelta(minutes=dur):
                        slot = (next_start, next_start + timedelta(minutes=dur))
                    else:
                        slot = None

            if slot:
                s_start, s_end = slot
                temp_commitments.append((s_start, s_end))
                
                slot_dict = {
                    "entity_type": item.get("entity_type", "TASK"),
                    "entity_id": item.get("entity_id"),
                    "title": item.get("title", "Priority Activity"),
                    "start_time": s_start.isoformat(),
                    "end_time": s_end.isoformat(),
                    "priority": item.get("priority", 50),
                    "effective_priority": item["_effective_priority"],
                    "focus_block": item.get("focus_block", False)
                }

                if persist:
                    saved = ScheduleSlot(
                        user_id=user_id,
                        entity_type=slot_dict["entity_type"],
                        entity_id=slot_dict["entity_id"],
                        task_id=slot_dict["entity_id"] if slot_dict["entity_type"] == "TASK" else None,
                        task_title=slot_dict["title"],
                        start_time=s_start,
                        end_time=s_end,
                        priority=slot_dict["priority"],
                        status="PLANNED",
                        focus_block=slot_dict["focus_block"]
                    )
                    SchedulingRepository.save_slot(saved)
                    slot_dict["id"] = saved.id

                scheduled_slots.append(slot_dict)
            else:
                backlog.append({
                    "entity_id": item.get("entity_id"),
                    "title": item.get("title"),
                    "reason": "Exceeds window capacity",
                    "effective_priority": item["_effective_priority"]
                })

        return {
            "scheduled": scheduled_slots,
            "backlog": backlog,
            "scheduled_count": len(scheduled_slots),
            "backlog_count": len(backlog)
        }
