"""
DeadlineOS — Flexible Window Engine
===================================
Finds optimal non-overlapping placements within a user's defined time window.
"""

from typing import Optional, Tuple, List
from datetime import datetime, timezone, timedelta
from models.schedule import ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from utils.timezone import utc_now


class FlexibleWindowEngine:
    """Calculates deterministic placement inside scheduling windows."""

    @classmethod
    def find_best_slot(
        cls,
        user_id: str,
        window_start: datetime,
        window_end: datetime,
        duration_minutes: int,
        buffer_minutes: int = 0,
        exclude_slot_id: Optional[str] = None
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Scans existing user commitments within [window_start, window_end] and identifies
        the earliest available contiguous interval of duration_minutes.
        """
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        needed_delta = timedelta(minutes=duration_minutes)
        buffer_delta = timedelta(minutes=buffer_minutes)

        if (window_end - window_start) < needed_delta:
            return None

        # Fetch existing user slots that overlap with the window
        existing_slots = SchedulingRepository.get_slots_by_user(
            user_id=user_id,
            start_time=window_start,
            end_time=window_end,
            status=None
        )

        # Filter out cancelled slots or the slot being moved
        active_commitments = [
            s for s in existing_slots
            if s.status != "CANCELLED" and (not exclude_slot_id or s.id != exclude_slot_id)
        ]

        # Sort commitments chronologically
        active_commitments.sort(key=lambda s: s.start_time)

        # Normalize commitment boundaries to UTC
        intervals: List[Tuple[datetime, datetime]] = []
        for s in active_commitments:
            s_start = s.start_time.replace(tzinfo=timezone.utc) if s.start_time.tzinfo is None else s.start_time
            s_end = s.end_time.replace(tzinfo=timezone.utc) if s.end_time.tzinfo is None else s.end_time
            # Only consider overlap with the window
            int_start = max(window_start, s_start)
            int_end = min(window_end, s_end)
            if int_end > int_start:
                intervals.append((int_start, int_end))

        # Check candidate gap before the first commitment
        candidate_start = window_start
        for (c_start, c_end) in intervals:
            if c_start > candidate_start:
                gap = c_start - candidate_start
                if gap >= needed_delta:
                    return candidate_start, candidate_start + needed_delta
            # Advance candidate_start past the current commitment + buffer
            candidate_start = max(candidate_start, c_end + buffer_delta)

        # Check trailing gap after all commitments
        if (window_end - candidate_start) >= needed_delta:
            return candidate_start, candidate_start + needed_delta

        return None
