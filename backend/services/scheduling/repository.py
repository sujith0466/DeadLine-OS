"""
DeadlineOS — Scheduling Repository
===================================
Provides unified, timezone-safe persistence and query operations for schedules,
schedule slots, and recurrence rules.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from database.db import db
from models.schedule import Schedule, ScheduleSlot
from models.recurrence_rule import RecurrenceRule


class SchedulingRepository:
    """Repository pattern implementation for DeadlineOS scheduling."""

    @staticmethod
    def get_slot_by_id(slot_id: str) -> Optional[ScheduleSlot]:
        return ScheduleSlot.query.get(slot_id)

    @staticmethod
    def get_slots_by_user(
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[ScheduleSlot]:
        """Query user slots in UTC within a given time range safely."""
        from utils.timezone import parse_datetime_safe

        query = ScheduleSlot.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        slots = query.all()

        if not start_time and not end_time:
            return sorted(
                slots,
                key=lambda s: parse_datetime_safe(s.start_time) or datetime.min.replace(tzinfo=timezone.utc)
            )

        st_bound = parse_datetime_safe(start_time) if start_time else None
        if st_bound and st_bound.tzinfo is None:
            st_bound = st_bound.replace(tzinfo=timezone.utc)

        et_bound = parse_datetime_safe(end_time) if end_time else None
        if et_bound and et_bound.tzinfo is None:
            et_bound = et_bound.replace(tzinfo=timezone.utc)

        filtered = []
        for s in slots:
            s_st = parse_datetime_safe(s.start_time)
            s_et = parse_datetime_safe(s.end_time)
            if s_st and s_st.tzinfo is None:
                s_st = s_st.replace(tzinfo=timezone.utc)
            if s_et and s_et.tzinfo is None:
                s_et = s_et.replace(tzinfo=timezone.utc)

            if st_bound and s_et and s_et < st_bound:
                continue
            if et_bound and s_st and s_st > et_bound:
                continue

            filtered.append(s)

        return sorted(
            filtered,
            key=lambda s: parse_datetime_safe(s.start_time) or datetime.min.replace(tzinfo=timezone.utc)
        )

    @staticmethod
    def get_slots_by_entity(entity_type: str, entity_id: str) -> List[ScheduleSlot]:
        return ScheduleSlot.query.filter_by(entity_type=entity_type, entity_id=entity_id).order_by(ScheduleSlot.start_time.asc()).all()

    @staticmethod
    def save_slot(slot: ScheduleSlot) -> ScheduleSlot:
        db.session.add(slot)
        db.session.commit()
        return slot

    @staticmethod
    def delete_slot(slot_id: str) -> bool:
        slot = ScheduleSlot.query.get(slot_id)
        if slot:
            db.session.delete(slot)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_schedule_by_date(user_id: str, target_date: str) -> Optional[Schedule]:
        return Schedule.query.filter_by(user_id=user_id, target_date=target_date).order_by(Schedule.created_at.desc()).first()

    @staticmethod
    def save_schedule(schedule: Schedule) -> Schedule:
        db.session.add(schedule)
        db.session.commit()
        return schedule

    @staticmethod
    def get_recurrence_rule(rule_id: str) -> Optional[RecurrenceRule]:
        return RecurrenceRule.query.get(rule_id)

    @staticmethod
    def save_recurrence_rule(rule: RecurrenceRule) -> RecurrenceRule:
        db.session.add(rule)
        db.session.commit()
        return rule
