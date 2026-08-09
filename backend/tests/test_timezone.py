import pytest
from datetime import datetime, timezone
from utils.timezone import (
    get_user_timezone,
    to_user_local,
    to_utc,
    slot_times_to_utc,
    validate_iana_timezone,
)


def test_timezone_validation():
    assert validate_iana_timezone("UTC") is True
    assert validate_iana_timezone("Asia/Kolkata") is True
    assert validate_iana_timezone("America/New_York") is True
    assert validate_iana_timezone("Invalid/Timezone") is False
    assert validate_iana_timezone(None) is False
    assert validate_iana_timezone("") is False


def test_slot_times_to_utc():
    # Test normal day
    s_utc, e_utc = slot_times_to_utc("2026-07-16", "09:00", "10:30", "America/New_York")
    assert s_utc.isoformat() == "2026-07-16T13:00:00+00:00"  # EDT is UTC-4 in July
    assert e_utc.isoformat() == "2026-07-16T14:30:00+00:00"

    # Test midnight crossover
    s_utc2, e_utc2 = slot_times_to_utc(
        "2026-07-16", "23:00", "01:00", "America/New_York"
    )
    assert s_utc2.isoformat() == "2026-07-17T03:00:00+00:00"
    assert e_utc2.isoformat() == "2026-07-17T05:00:00+00:00"


def test_to_utc():
    # Naive dt
    naive = datetime(2026, 7, 16, 9, 0)
    utc_dt = to_utc(naive, "America/New_York")
    assert utc_dt.isoformat() == "2026-07-16T13:00:00+00:00"


def test_to_user_local():
    utc_dt = datetime(2026, 7, 16, 13, 0, tzinfo=timezone.utc)
    local_dt = to_user_local(utc_dt, "America/New_York")
    assert local_dt.strftime("%H:%M") == "09:00"
