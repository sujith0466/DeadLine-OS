"""
DeadlineOS — Timezone Utilities
================================
Centralised helpers for timezone-aware datetime operations.

Design principles:
  • All internal data is stored and processed in UTC.
  • User-facing presentation converts UTC → user's configured timezone.
  • No naive datetimes (without tzinfo) enter or leave this module.
  • DST-safe: uses zoneinfo (Python 3.9+) with a dateutil fallback.

Usage:
    from utils.timezone import get_user_timezone, to_user_local, utc_now

    tz = get_user_timezone(user_id)
    local_dt = to_user_local(some_utc_dt, tz)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ── Timezone backend (zoneinfo preferred, dateutil as fallback) ────────────────
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # type: ignore[import]

    def _get_zoneinfo(tz_str: str):
        try:
            return ZoneInfo(tz_str)
        except (ZoneInfoNotFoundError, Exception):
            return None

except ImportError:
    # Python < 3.9 or missing tzdata — fall back to dateutil
    try:
        from dateutil import tz as _dateutil_tz  # type: ignore[import]

        class _ZoneInfoShim:
            """Minimal shim so call sites don't need to branch."""

            def __init__(self, key: str, _tz=None):
                self._tz = _tz
                self.key = key

            def __repr__(self):
                return f"ZoneInfo('{self.key}')"

            def utcoffset(self, dt):
                return self._tz.utcoffset(dt) if self._tz else None

            def fromutc(self, dt):
                return self._tz.fromutc(dt) if self._tz else dt

        ZoneInfo = _ZoneInfoShim  # type: ignore[assignment,misc]

        def _get_zoneinfo(tz_str: str):
            _tz = _dateutil_tz.gettz(tz_str)
            if _tz is None:
                return None
            return _ZoneInfoShim(tz_str, _tz)

    except ImportError:
        # Last resort: only UTC is supported
        def _get_zoneinfo(tz_str: str):  # type: ignore[misc]
            if tz_str == "UTC":
                return timezone.utc
            logger.error(
                "[timezone] Neither zoneinfo nor dateutil is available. Only UTC is supported."
            )
            return None


# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_TIMEZONE = "UTC"
_UTC = timezone.utc


# ── Public API ────────────────────────────────────────────────────────────────


def utc_now() -> datetime:
    """Return the current moment as a timezone-aware UTC datetime."""
    return datetime.now(_UTC)


def get_user_timezone(user_id: Optional[str] = None) -> str:
    """
    Resolve the IANA timezone string for a user.

    Lookup order:
      1. User.timezone column  (set at registration or profile edit)
      2. UserSettings.profile['timezone']  (Settings page override)
      3. Application DEFAULT_TIMEZONE  ("UTC")

    Returns a validated IANA timezone string (e.g. "Asia/Kolkata").
    Falls back to DEFAULT_TIMEZONE if the stored value is invalid.
    """
    if not user_id:
        return DEFAULT_TIMEZONE

    try:
        from models.user import User

        user = User.query.get(user_id)
        if user and user.timezone and _get_zoneinfo(user.timezone):
            return user.timezone
    except Exception as e:
        logger.warning("[timezone] Failed to read User.timezone for %s: %s", user_id, e)

    try:
        from models.user_settings import UserSettings

        settings = UserSettings.query.get(user_id)
        if settings and settings.profile:
            tz_str = settings.profile.get("timezone")
            if tz_str and _get_zoneinfo(tz_str):
                return tz_str
    except Exception as e:
        logger.warning(
            "[timezone] Failed to read UserSettings.profile.timezone for %s: %s",
            user_id,
            e,
        )

    return DEFAULT_TIMEZONE


def to_user_local(dt: datetime, tz_str: str) -> datetime:
    """
    Convert a UTC datetime to the user's local timezone.

    Parameters
    ----------
    dt     : A timezone-aware UTC datetime.
    tz_str : IANA timezone string (e.g. "Asia/Kolkata").

    Returns
    -------
    A timezone-aware datetime in the target timezone.
    Returns the original UTC datetime if conversion fails.
    """
    if dt is None:
        return dt  # type: ignore[return-value]

    # Ensure dt is UTC-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_UTC)

    zi = _get_zoneinfo(tz_str)
    if zi is None:
        logger.warning("[timezone] Invalid tz_str '%s', returning UTC.", tz_str)
        return dt

    try:
        return dt.astimezone(zi)  # type: ignore[arg-type]
    except Exception as e:
        logger.warning("[timezone] astimezone failed for tz '%s': %s", tz_str, e)
        return dt


def to_utc(dt: datetime, tz_str: str) -> datetime:
    """
    Convert a local naive (or aware) datetime to UTC.

    Parameters
    ----------
    dt     : A datetime, possibly naive (assumed to be in tz_str).
    tz_str : IANA timezone string of the source timezone.

    Returns
    -------
    A timezone-aware UTC datetime.
    """
    if dt is None:
        return dt  # type: ignore[return-value]

    # If already UTC-aware, just normalise
    if dt.tzinfo is not None:
        try:
            return dt.astimezone(_UTC)
        except Exception:
            pass

    zi = _get_zoneinfo(tz_str)
    if zi is None:
        logger.warning("[timezone] Invalid tz_str '%s', treating as UTC.", tz_str)
        return dt.replace(tzinfo=_UTC)

    try:
        aware_local = dt.replace(tzinfo=zi)  # type: ignore[arg-type]
        return aware_local.astimezone(_UTC)
    except Exception as e:
        logger.warning("[timezone] to_utc failed for tz '%s': %s", tz_str, e)
        return dt.replace(tzinfo=_UTC)


def slot_times_to_utc(
    date_str: str, start_hhmm: str, end_hhmm: str, tz_str: str
) -> Tuple[datetime, datetime]:
    """
    Convert ScheduleSlot HH:MM strings on a given date to UTC-aware datetimes.

    Parameters
    ----------
    date_str   : "YYYY-MM-DD" — the local calendar date of the slot.
    start_hhmm : "HH:MM" — local start time.
    end_hhmm   : "HH:MM" — local end time.
    tz_str     : IANA timezone of the user.

    Returns
    -------
    (start_utc, end_utc) : Tuple of UTC-aware datetimes.
    Falls back to treating input as UTC on parse failure.
    """
    try:
        year, month, day = map(int, date_str.split("-"))
        sh, sm = map(int, start_hhmm.split(":"))
        eh, em = map(int, end_hhmm.split(":"))

        naive_start = datetime(year, month, day, sh, sm)
        naive_end = datetime(year, month, day, eh, em)

        # Handle midnight crossover (e.g. slot from 23:00 to 00:30)
        if naive_end <= naive_start:
            naive_end += timedelta(days=1)

        return to_utc(naive_start, tz_str), to_utc(naive_end, tz_str)

    except Exception as e:
        logger.warning("[timezone] slot_times_to_utc failed: %s", e)
        # Safe fallback: treat as UTC
        try:
            year, month, day = map(int, date_str.split("-"))
            sh, sm = map(int, start_hhmm.split(":"))
            eh, em = map(int, end_hhmm.split(":"))
            return (
                datetime(year, month, day, sh, sm, tzinfo=_UTC),
                datetime(year, month, day, eh, em, tzinfo=_UTC),
            )
        except Exception:
            now = utc_now()
            return now, now


def validate_iana_timezone(tz_str: str) -> bool:
    """Return True if tz_str is a valid IANA timezone identifier."""
    if not tz_str or not isinstance(tz_str, str):
        return False
    return _get_zoneinfo(tz_str) is not None
