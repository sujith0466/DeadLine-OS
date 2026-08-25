"""
DeadlineOS — Analytics Timezone & Boundary Foundation
=====================================================
Provides deterministic, timezone-aware datetime boundary calculation for analytics.
All queries against PostgreSQL / SQLite use UTC datetime ranges calculated from
the user's configured IANA local timezone.
"""

from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from utils.timezone import get_user_timezone, to_utc, to_user_local, utc_now, DEFAULT_TIMEZONE


class AnalyticsTimeWindow:
    """Calculates local-to-UTC time boundaries for analytics reporting."""

    @staticmethod
    def get_day_boundaries_utc(user_id: Optional[str], date_str: Optional[str] = None) -> Tuple[datetime, datetime, str]:
        """
        Returns (start_utc, end_utc, user_tz) for a single calendar day in user's local timezone.
        date_str format: "YYYY-MM-DD" (defaults to today in user's local time).
        """
        user_tz = get_user_timezone(user_id)
        now_utc = utc_now()
        now_local = to_user_local(now_utc, user_tz)

        if not date_str:
            target_year, target_month, target_day = now_local.year, now_local.month, now_local.day
            resolved_date_str = f"{target_year:04d}-{target_month:02d}-{target_day:02d}"
        else:
            resolved_date_str = date_str
            parts = [int(p) for p in date_str.split("-")]
            target_year, target_month, target_day = parts[0], parts[1], parts[2]

        naive_start = datetime(target_year, target_month, target_day, 0, 0, 0)
        naive_end = naive_start + timedelta(days=1) - timedelta(microseconds=1)

        start_utc = to_utc(naive_start, user_tz)
        end_utc = to_utc(naive_end, user_tz)

        return start_utc, end_utc, resolved_date_str

    @staticmethod
    def get_range_boundaries_utc(
        user_id: Optional[str],
        start_date_str: str,
        end_date_str: str
    ) -> Tuple[datetime, datetime]:
        """
        Returns (start_utc, end_utc) spanning from start_date_str 00:00:00 to end_date_str 23:59:59 local.
        """
        user_tz = get_user_timezone(user_id)
        s_parts = [int(p) for p in start_date_str.split("-")]
        e_parts = [int(p) for p in end_date_str.split("-")]

        naive_start = datetime(s_parts[0], s_parts[1], s_parts[2], 0, 0, 0)
        naive_end = datetime(e_parts[0], e_parts[1], e_parts[2], 23, 59, 59, 999999)

        start_utc = to_utc(naive_start, user_tz)
        end_utc = to_utc(naive_end, user_tz)

        return start_utc, end_utc

    @staticmethod
    def get_n_days_range_utc(user_id: Optional[str], days: int = 7) -> Tuple[datetime, datetime, list]:
        """
        Returns (start_utc, end_utc, date_strings) for the last N full local days including today.
        """
        user_tz = get_user_timezone(user_id)
        now_utc = utc_now()
        now_local = to_user_local(now_utc, user_tz)
        today_start_local = datetime(now_local.year, now_local.month, now_local.day, 0, 0, 0)
        
        start_local = today_start_local - timedelta(days=days - 1)
        end_local = today_start_local + timedelta(days=1) - timedelta(microseconds=1)

        date_strings = []
        cur = start_local
        while cur <= today_start_local:
            date_strings.append(f"{cur.year:04d}-{cur.month:02d}-{cur.day:02d}")
            cur += timedelta(days=1)

        start_utc = to_utc(start_local, user_tz)
        end_utc = to_utc(end_local, user_tz)

        return start_utc, end_utc, date_strings
