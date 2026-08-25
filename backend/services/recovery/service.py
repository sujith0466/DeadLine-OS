"""
DeadlineOS — Recovery Service (Phase 5)
=======================================
Central coordinator for recovery interventions. Orchestrates Runtime,
Scheduling, and Notification services without mutating state machines directly.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from database.db import db
from models.recovery import RecoveryActionType, RecoveryRecord
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from services.recovery.repository import RecoveryRepository
from services.runtime.session_engine import RuntimeSessionEngine
from services.runtime.repository import RuntimeRepository
from services.runtime.state_machine import RuntimeStateMachine, RuntimeLifecycleState
from services.scheduling.repository import SchedulingRepository
from services.notifications.repository import NotificationRepository
from services.notifications.reminder_service import ReminderService
from utils.timezone import get_user_timezone, to_user_local, utc_now


class RecoveryService:
    """Orchestrates recovery actions cleanly across domain services."""

    @classmethod
    def log_recovery_action(
        cls,
        user_id: str,
        action_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        schedule_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> RecoveryRecord:
        return RecoveryRepository.save_record(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            schedule_id=schedule_id,
            details=details
        )

    @classmethod
    def skip_today(
        cls,
        user_id: str,
        entity_id: str,
        entity_type: str = "TASK",
        schedule_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Intentionally skips an activity for the current local day without deleting
        the underlying domain record. Idempotent and non-destructive.
        """
        tz_name = get_user_timezone(user_id)
        local_now = to_user_local(utc_now(), tz_name)
        today_str = local_now.strftime("%Y-%m-%d")

        # 1. Update ScheduleSlot if exists
        slot = None
        if schedule_id:
            slot = SchedulingRepository.get_slot_by_id(schedule_id)
        elif entity_id:
            # Look up slot for today
            day_start = datetime(local_now.year, local_now.month, local_now.day, 0, 0, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            slots = SchedulingRepository.get_slots_by_user(user_id, day_start, day_end)
            slot = next((s for s in slots if s.entity_id == entity_id), None)

        if slot and slot.user_id == user_id:
            slot.status = "SKIPPED"
            slot.updated_at = utc_now()
            db.session.commit()

        # 2. Update RuntimeState if currently active/scheduled
        runtime_state = RuntimeRepository.get_active_state_for_entity(entity_type, entity_id)
        if runtime_state and runtime_state.user_id == user_id:
            if runtime_state.status not in ("COMPLETED_MANUAL", "COMPLETED_AUTO", "SKIPPED"):
                try:
                    RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.SKIPPED)
                except Exception:
                    pass

        # 3. Invalidate/Cancel pending notifications for today
        NotificationRepository.cancel_pending_for_entity(user_id, entity_id)
        if slot:
            NotificationRepository.cancel_pending_for_entity(user_id, slot.id)

        # 4. Audit Log
        record = cls.log_recovery_action(
            user_id=user_id,
            action_type=RecoveryActionType.SKIP,
            entity_type=entity_type,
            entity_id=entity_id,
            schedule_id=slot.id if slot else schedule_id,
            details={"reason": reason or "User skipped for today", "date": today_str}
        )

        return {
            "success": True,
            "action": "SKIP_TODAY",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "date": today_str,
            "recovery_record_id": record.id
        }


    @classmethod
    def pause_activity(
        cls,
        user_id: str,
        entity_id: str,
        entity_type: str = "TASK",
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Temporarily excludes an individual activity from scheduling and notification
        pre-alerts without affecting the underlying domain object.
        """
        # Cancel any pending future schedule slots for this activity
        future_slots = ScheduleSlot.query.filter(
            ScheduleSlot.user_id == user_id,
            ScheduleSlot.entity_id == entity_id,
            ScheduleSlot.status.in_(["PLANNED", "TENTATIVE"])
        ).all()

        for slot in future_slots:
            slot.status = "PAUSED"
            slot.updated_at = utc_now()
            NotificationRepository.cancel_pending_for_entity(user_id, slot.id)

        # Cancel any entity-level pending notifications
        NotificationRepository.cancel_pending_for_entity(user_id, entity_id)
        db.session.commit()

        # Audit log
        record = cls.log_recovery_action(
            user_id=user_id,
            action_type=RecoveryActionType.PAUSE,
            entity_type=entity_type,
            entity_id=entity_id,
            details={"reason": reason or "User paused activity", "paused_slots_count": len(future_slots)}
        )

        return {
            "success": True,
            "action": "PAUSE_ACTIVITY",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "paused_slots_count": len(future_slots),
            "recovery_record_id": record.id
        }

    @classmethod
    def resume_activity(
        cls,
        user_id: str,
        entity_id: str,
        entity_type: str = "TASK"
    ) -> Dict[str, Any]:
        """
        Resumes a paused activity and restores future schedule eligibility.
        """
        paused_slots = ScheduleSlot.query.filter(
            ScheduleSlot.user_id == user_id,
            ScheduleSlot.entity_id == entity_id,
            ScheduleSlot.status == "PAUSED"
        ).all()

        for slot in paused_slots:
            slot.status = "PLANNED"
            slot.updated_at = utc_now()

        db.session.commit()

        # Audit log
        record = cls.log_recovery_action(
            user_id=user_id,
            action_type=RecoveryActionType.RESUME,
            entity_type=entity_type,
            entity_id=entity_id,
            details={"resumed_slots_count": len(paused_slots)}
        )

        return {
            "success": True,
            "action": "RESUME_ACTIVITY",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "resumed_slots_count": len(paused_slots),
            "recovery_record_id": record.id
        }


    @classmethod
    def get_recoverable_items(cls, user_id: str) -> Dict[str, Any]:
        """
        Aggregates missed, interrupted, skipped, overdue, and at-risk activities
        for display in the Recovery Center.
        """
        from models.task import Task
        from models.runtime_state import RuntimeState
        from utils.timezone import to_user_local

        tz_name = get_user_timezone(user_id)
        now_utc = utc_now()

        # 1. Missed schedule slots (end_time in past and still PLANNED)
        missed_slots = ScheduleSlot.query.filter(
            ScheduleSlot.user_id == user_id,
            ScheduleSlot.end_time < now_utc,
            ScheduleSlot.status == "PLANNED"
        ).order_by(ScheduleSlot.end_time.desc()).limit(20).all()

        # 2. Interrupted runtime states
        interrupted_states = RuntimeState.query.filter(
            RuntimeState.user_id == user_id,
            RuntimeState.status.in_(["INTERRUPTED", "MISSED"])
        ).order_by(RuntimeState.updated_at.desc()).limit(20).all()

        # 3. Overdue pending tasks
        overdue_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.deadline < now_utc,
            Task.status == "pending"
        ).order_by(Task.deadline.asc()).limit(20).all()

        # 4. Skipped slots today
        local_now = to_user_local(now_utc, tz_name)
        day_start = datetime(local_now.year, local_now.month, local_now.day, 0, 0, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        skipped_slots = ScheduleSlot.query.filter(
            ScheduleSlot.user_id == user_id,
            ScheduleSlot.status == "SKIPPED",
            ScheduleSlot.start_time >= day_start,
            ScheduleSlot.start_time < day_end
        ).all()

        return {
            "missed": [s.to_dict() for s in missed_slots],
            "interrupted": [
                {
                    "entity_id": rs.entity_id,
                    "entity_type": rs.entity_type,
                    "status": rs.status,
                    "updated_at": rs.updated_at.isoformat() if rs.updated_at else None
                }
                for rs in interrupted_states
            ],
            "overdue": [
                {
                    "id": t.id,
                    "title": t.title,
                    "deadline": t.deadline.isoformat() if t.deadline else None,
                    "priority_score": getattr(t, "priority_score", 50)
                }
                for t in overdue_tasks
            ],
            "skipped": [s.to_dict() for s in skipped_slots],
            "total_threats": len(missed_slots) + len(interrupted_states) + len(overdue_tasks)
        }

    @classmethod
    def execute_recovery_action(
        cls,
        user_id: str,
        action: str,
        entity_id: str,
        entity_type: str = "TASK",
        schedule_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Routes user recovery interventions cleanly to Runtime, Scheduling, or Recovery services.
        """
        params = params or {}
        action = action.upper()

        if action == "SKIP":
            return cls.skip_today(
                user_id=user_id,
                entity_id=entity_id,
                entity_type=entity_type,
                schedule_id=schedule_id,
                reason=params.get("reason")
            )
        elif action == "PAUSE":
            return cls.pause_activity(
                user_id=user_id,
                entity_id=entity_id,
                entity_type=entity_type,
                reason=params.get("reason")
            )
        elif action == "RESUME":
            return cls.resume_activity(
                user_id=user_id,
                entity_id=entity_id,
                entity_type=entity_type
            )
        elif action == "RESCHEDULE":
            new_start_iso = params.get("new_start_time")
            if not schedule_id or not new_start_iso:
                raise ValueError("schedule_id and new_start_time are required for RESCHEDULE")
            new_start = datetime.fromisoformat(new_start_iso.replace("Z", "+00:00"))
            res = ReschedulingEngine.reschedule_slot(
                user_id=user_id,
                slot_id=schedule_id,
                new_start_time=new_start,
                cascade=params.get("cascade", True)
            )
            cls.log_recovery_action(
                user_id=user_id,
                action_type=RecoveryActionType.RESCHEDULE,
                entity_type=entity_type,
                entity_id=entity_id,
                schedule_id=schedule_id,
                details=params
            )
            return {"success": True, "reschedule_result": res}
        elif action == "COMPLETE":
            # Safely complete runtime state
            try:
                RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.COMPLETED_MANUAL)
            except Exception:
                pass
            from models.task import Task
            task = Task.query.filter_by(id=entity_id, user_id=user_id).first()
            if task:
                task.status = "completed"
                db.session.commit()
            cls.log_recovery_action(
                user_id=user_id,
                action_type=RecoveryActionType.RECOVER,
                entity_type=entity_type,
                entity_id=entity_id,
                details={"action": "COMPLETE"}
            )
            return {"success": True, "completed": True}
        else:
            raise ValueError(f"Unknown recovery action: {action}")


    @classmethod
    def set_vacation_mode(
        cls,
        user_id: str,
        start_date: str,
        end_date: str,
        suppress_notifications: bool = True,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activates user-level Vacation Mode for the specified date range.
        Stores state in UserSettings without deleting activities or recurrence rules.
        """
        from sqlalchemy.orm.attributes import flag_modified
        from models.user_settings import UserSettings
        settings = UserSettings.get_or_create(user_id)
        planner = dict(settings.planner or {})

        planner["vacation_mode"] = {
            "enabled": True,
            "start_date": start_date,
            "end_date": end_date,
            "suppress_notifications": suppress_notifications,
            "reason": reason or "Vacation"
        }

        settings.planner = dict(planner)
        flag_modified(settings, "planner")
        settings.updated_at = utc_now()
        db.session.commit()

        # Audit log
        record = cls.log_recovery_action(
            user_id=user_id,
            action_type=RecoveryActionType.VACATION,
            details={"status": "START", "start_date": start_date, "end_date": end_date, "reason": reason}
        )

        return {
            "success": True,
            "vacation_mode": planner["vacation_mode"],
            "recovery_record_id": record.id
        }

    @classmethod
    def end_vacation_mode(cls, user_id: str) -> Dict[str, Any]:
        """Deactivates Vacation Mode and restores normal scheduling."""
        from sqlalchemy.orm.attributes import flag_modified
        from models.user_settings import UserSettings
        settings = UserSettings.get_or_create(user_id)
        planner = dict(settings.planner or {})

        if "vacation_mode" in planner:
            planner["vacation_mode"] = dict(planner["vacation_mode"])
            planner["vacation_mode"]["enabled"] = False

        settings.planner = dict(planner)
        flag_modified(settings, "planner")
        settings.updated_at = utc_now()
        db.session.commit()

        # Audit log
        record = cls.log_recovery_action(
            user_id=user_id,
            action_type=RecoveryActionType.VACATION,
            details={"status": "END"}
        )

        return {
            "success": True,
            "vacation_mode": planner.get("vacation_mode", {"enabled": False}),
            "recovery_record_id": record.id
        }

    @classmethod
    def is_user_on_vacation(cls, user_id: str) -> bool:
        """Evaluates whether current user local time falls within an active vacation window."""
        from models.user_settings import UserSettings
        from utils.timezone import get_user_timezone, to_user_local

        settings = UserSettings.get_or_create(user_id)
        planner = settings.planner or {}
        vacation = planner.get("vacation_mode", {})

        if not vacation.get("enabled"):
            return False

        start_date_str = vacation.get("start_date")
        end_date_str = vacation.get("end_date")
        if not start_date_str or not end_date_str:
            return False

        try:
            tz_name = get_user_timezone(user_id)
            local_today = to_user_local(utc_now(), tz_name).date()
            start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            return start_d <= local_today <= end_d
        except Exception:
            return False


    @classmethod
    def activate_emergency_mode(
        cls,
        user_id: str,
        reason: Optional[str] = None,
        auto_skip_non_critical: bool = False
    ) -> Dict[str, Any]:
        """
        Activates Emergency Mode. Sheds execution load to critical tasks only
        without deleting domain activities or changing deadlines.
        """
        from sqlalchemy.orm.attributes import flag_modified
        from models.user_settings import UserSettings
        from utils.timezone import to_user_local

        settings = UserSettings.get_or_create(user_id)
        planner = dict(settings.planner or {})

        planner["emergency_mode"] = {
            "enabled": True,
            "activated_at": utc_now().isoformat(),
            "reason": reason or "High schedule stress / emergency",
            "auto_skip_non_critical": auto_skip_non_critical
        }

        settings.planner = dict(planner)
        flag_modified(settings, "planner")
        settings.updated_at = utc_now()
        db.session.commit()

        skipped_slots_count = 0
        if auto_skip_non_critical:
            # Skip non-critical slots today
            tz_name = get_user_timezone(user_id)
            local_now = to_user_local(utc_now(), tz_name)
            day_start = datetime(local_now.year, local_now.month, local_now.day, 0, 0, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            slots = SchedulingRepository.get_slots_by_user(user_id, day_start, day_end)

            for s in slots:
                if s.status in ("PLANNED", "TENTATIVE") and getattr(s, "priority_score", 50) < 70:
                    s.status = "SKIPPED"
                    s.updated_at = utc_now()
                    NotificationRepository.cancel_pending_for_entity(user_id, s.id)
                    if s.entity_id:
                        NotificationRepository.cancel_pending_for_entity(user_id, s.entity_id)
                    skipped_slots_count += 1
            db.session.commit()

        # Audit log
        record = cls.log_recovery_action(
            user_id=user_id,
            action_type=RecoveryActionType.EMERGENCY,
            details={"status": "ACTIVATE", "reason": reason, "skipped_slots_count": skipped_slots_count}
        )

        return {
            "success": True,
            "emergency_mode": planner["emergency_mode"],
            "skipped_slots_count": skipped_slots_count,
            "recovery_record_id": record.id
        }

    @classmethod
    def deactivate_emergency_mode(cls, user_id: str) -> Dict[str, Any]:
        """Deactivates Emergency Mode and restores standard execution surface."""
        from sqlalchemy.orm.attributes import flag_modified
        from models.user_settings import UserSettings

        settings = UserSettings.get_or_create(user_id)
        planner = dict(settings.planner or {})

        if "emergency_mode" in planner:
            planner["emergency_mode"] = dict(planner["emergency_mode"])
            planner["emergency_mode"]["enabled"] = False

        settings.planner = dict(planner)
        flag_modified(settings, "planner")
        settings.updated_at = utc_now()
        db.session.commit()

        # Audit log
        record = cls.log_recovery_action(
            user_id=user_id,
            action_type=RecoveryActionType.EMERGENCY,
            details={"status": "DEACTIVATE"}
        )

        return {
            "success": True,
            "emergency_mode": planner.get("emergency_mode", {"enabled": False}),
            "recovery_record_id": record.id
        }

    @classmethod
    def is_emergency_mode_active(cls, user_id: str) -> bool:
        """Checks if Emergency Mode is actively enabled."""
        from models.user_settings import UserSettings
        settings = UserSettings.get_or_create(user_id)
        planner = settings.planner or {}
        return bool(planner.get("emergency_mode", {}).get("enabled", False))
