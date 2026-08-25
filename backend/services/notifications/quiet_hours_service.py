"""
DeadlineOS — Quiet Hours Service
================================
Evaluates user quiet hours deterministically in the user's local timezone.
Defers non-critical notifications to the conclusion of quiet hours.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date, time as dt_time, timezone, timedelta
from models.user_settings import UserSettings
from utils.timezone import get_user_timezone, to_user_local, to_utc, utc_now


class QuietHoursService:
    """Calculates quiet hours boundaries and notification deferrals."""

    DEFAULT_QUIET_START = "22:00"  # 10:00 PM
    DEFAULT_QUIET_END = "07:00"    # 07:00 AM

    @classmethod
    def get_quiet_hours_config(cls, user_id: str) -> Dict[str, Any]:
        """Loads user quiet hours preferences with safe defaults."""
        settings = UserSettings.query.get(user_id)
        if not settings or not settings.notifications:
            return {
                "enabled": False,
                "start_hhmm": cls.DEFAULT_QUIET_START,
                "end_hhmm": cls.DEFAULT_QUIET_END,
                "allow_critical": True
            }

        n = settings.notifications
        return {
            "enabled": n.get("quiet_hours_enabled", False),
            "start_hhmm": n.get("quiet_hours_start", cls.DEFAULT_QUIET_START),
            "end_hhmm": n.get("quiet_hours_end", cls.DEFAULT_QUIET_END),
            "allow_critical": n.get("quiet_hours_allow_critical", True)
        }

    @classmethod
    def is_in_quiet_hours(
        cls,
        user_id: str,
        target_utc: datetime,
        is_critical: bool = False
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Checks if target_utc falls in quiet hours.
        If in quiet hours, returns (True, deferred_utc_time).
        Otherwise returns (False, None).
        """
        config = cls.get_quiet_hours_config(user_id)
        if not config["enabled"]:
            return False, None

        if is_critical and config["allow_critical"]:
            return False, None

        tz_name = get_user_timezone(user_id)
        local_dt = to_user_local(target_utc, tz_name)
        
        q_start_h, q_start_m = map(int, config["start_hhmm"].split(":"))
        q_end_h, q_end_m = map(int, config["end_hhmm"].split(":"))

        current_local_time = local_dt.time()
        start_time = dt_time(q_start_h, q_start_m)
        end_time = dt_time(q_end_h, q_end_m)

        # Case A: Same-day quiet hours (e.g. 13:00 to 15:00)
        if start_time < end_time:
            if start_time <= current_local_time < end_time:
                # Defer to end_time today
                deferred_local = datetime.combine(local_dt.date(), end_time)
                deferred_utc = to_utc(deferred_local, tz_name)
                return True, deferred_utc
            return False, None

        # Case B: Overnight quiet hours (e.g. 22:00 to 07:00 next day)
        else:
            if current_local_time >= start_time:
                # Late night (e.g. 23:30) -> Defer to end_time TOMORROW
                deferred_local = datetime.combine(local_dt.date() + timedelta(days=1), end_time)
                deferred_utc = to_utc(deferred_local, tz_name)
                return True, deferred_utc
            elif current_local_time < end_time:
                # Early morning (e.g. 05:30) -> Defer to end_time TODAY
                deferred_local = datetime.combine(local_dt.date(), end_time)
                deferred_utc = to_utc(deferred_local, tz_name)
                return True, deferred_utc
            return False, None
