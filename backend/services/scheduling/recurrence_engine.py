"""
DeadlineOS — Recurrence Engine
==============================
Deterministic, DST-safe recurrence rule evaluation and slot expansion.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, date, time as dt_time, timezone, timedelta
from models.recurrence_rule import RecurrenceRule
from models.schedule import ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from utils.timezone import get_user_timezone, to_user_local, to_utc, utc_now


def _normalize_ts(dt: datetime) -> str:
    """Normalizes a datetime to UTC ISO string for robust comparison."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RecurrenceEngine:
    """Evaluates recurrence patterns deterministically across timezones."""

    WEEKDAY_MAP = {
        "MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6,
        "MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6
    }

    @classmethod
    def expand_dates(
        cls,
        rule: RecurrenceRule,
        range_start: datetime,
        range_end: datetime,
        tz_name: str
    ) -> List[date]:
        """
        Generates local calendar dates matching the recurrence rule within [range_start, range_end].
        Uses user local date boundaries to guarantee zero DST time drift.
        """
        local_rule_start = to_user_local(rule.start_date, tz_name).date()
        local_range_start = to_user_local(range_start, tz_name).date()
        local_range_end = to_user_local(range_end, tz_name).date()

        local_rule_end = to_user_local(rule.end_date, tz_name).date() if rule.end_date else None

        freq = (rule.frequency or "DAILY").upper()
        interval = max(1, rule.interval or 1)
        max_occurrences = rule.occurrence_count

        matched_dates: List[date] = []
        occurrences_count = 0

        # Determine target weekdays if applicable
        target_weekdays = set()
        if freq in ("WEEKLY", "WEEKDAYS", "CUSTOM_DAYS"):
            if freq == "WEEKDAYS":
                target_weekdays = {0, 1, 2, 3, 4}
            elif rule.by_weekdays:
                parts = [p.strip().upper() for p in rule.by_weekdays.split(",") if p.strip()]
                for p in parts:
                    if p in cls.WEEKDAY_MAP:
                        target_weekdays.add(cls.WEEKDAY_MAP[p])
            if not target_weekdays:
                target_weekdays = {local_rule_start.weekday()}

        current_date = local_rule_start
        safety_limit = 730

        while safety_limit > 0 and current_date <= local_range_end:
            safety_limit -= 1
            if local_rule_end and current_date > local_rule_end:
                break
            if max_occurrences is not None and occurrences_count >= max_occurrences:
                break

            matches = False
            if freq == "DAILY":
                days_diff = (current_date - local_rule_start).days
                if days_diff >= 0 and days_diff % interval == 0:
                    matches = True
            elif freq in ("WEEKLY", "WEEKDAYS", "CUSTOM_DAYS"):
                weeks_diff = (current_date - local_rule_start).days // 7
                if weeks_diff >= 0 and (weeks_diff % interval == 0) and (current_date.weekday() in target_weekdays):
                    matches = True
            elif freq == "INTERVAL_DAYS":
                days_diff = (current_date - local_rule_start).days
                if days_diff >= 0 and days_diff % interval == 0:
                    matches = True

            if matches:
                occurrences_count += 1
                if current_date >= local_range_start:
                    matched_dates.append(current_date)

            current_date += timedelta(days=1)

        return matched_dates

    @classmethod
    def materialize_occurrences(
        cls,
        rule_id: str,
        user_id: str,
        entity_type: str,
        entity_id: Optional[str],
        title: str,
        start_time_local_hhmm: str,
        duration_minutes: int,
        range_start: datetime,
        range_end: datetime,
        priority: int = 50,
        focus_block: bool = False
    ) -> List[ScheduleSlot]:
        """
        Materializes recurring slots into the database without creating duplicate entries.
        """
        rule = SchedulingRepository.get_recurrence_rule(rule_id)
        if not rule:
            return []

        tz_name = get_user_timezone(user_id)
        dates = cls.expand_dates(rule, range_start, range_end, tz_name)

        sh, sm = map(int, start_time_local_hhmm.split(":"))
        created_slots: List[ScheduleSlot] = []

        # Find existing slots for this rule to avoid duplicates
        existing_slots = ScheduleSlot.query.filter_by(
            user_id=user_id,
            recurrence_rule_id=rule_id
        ).all()
        existing_starts: Set[str] = {_normalize_ts(s.start_time) for s in existing_slots if s.start_time}

        for d in dates:
            naive_start = datetime(d.year, d.month, d.day, sh, sm)
            naive_end = naive_start + timedelta(minutes=duration_minutes)

            utc_start = to_utc(naive_start, tz_name)
            utc_end = to_utc(naive_end, tz_name)

            if _normalize_ts(utc_start) in existing_starts:
                continue

            slot = ScheduleSlot(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                task_id=entity_id if entity_type == "TASK" else None,
                task_title=title,
                start_time=utc_start,
                end_time=utc_end,
                priority=priority,
                status="PLANNED",
                recurrence_rule_id=rule_id,
                focus_block=focus_block,
                is_break=False
            )
            SchedulingRepository.save_slot(slot)
            created_slots.append(slot)
            existing_starts.add(_normalize_ts(utc_start))

        return created_slots
