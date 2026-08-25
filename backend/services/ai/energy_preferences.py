"""
DeadlineOS — User Energy Preferences Service
============================================
Manages explicit user-configured focus and low-energy intervals.
Guarantees the strict precedence hierarchy: Explicit User Preference > Learned Profile > Generic Fallback.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm.attributes import flag_modified
from database.db import db
from models.user_settings import UserSettings
from utils.timezone import utc_now


class EnergyPreferencesService:
    DEFAULT_ENERGY_CONFIG = {
        "peak_focus_start": "09:00",
        "peak_focus_end": "12:00",
        "low_energy_start": "14:00",
        "low_energy_end": "16:00",
        "preferred_session_duration_minutes": 50,
        "preferred_break_duration_minutes": 10,
        "is_explicitly_configured": False
    }

    @classmethod
    def get_energy_preferences(cls, user_id: str) -> Dict[str, Any]:
        """Retrieves user energy preferences or default baseline."""
        settings = UserSettings.get_or_create(user_id)
        planner = settings.planner or {}
        return planner.get("energy_preferences", dict(cls.DEFAULT_ENERGY_CONFIG))

    @classmethod
    def set_energy_preferences(
        cls,
        user_id: str,
        peak_focus_start: Optional[str] = None,
        peak_focus_end: Optional[str] = None,
        low_energy_start: Optional[str] = None,
        low_energy_end: Optional[str] = None,
        preferred_session_duration_minutes: Optional[int] = None,
        preferred_break_duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sets explicit user-controlled energy preference windows."""
        settings = UserSettings.get_or_create(user_id)
        planner = dict(settings.planner or {})
        current = planner.get("energy_preferences", dict(cls.DEFAULT_ENERGY_CONFIG))

        if peak_focus_start:
            current["peak_focus_start"] = peak_focus_start
        if peak_focus_end:
            current["peak_focus_end"] = peak_focus_end
        if low_energy_start:
            current["low_energy_start"] = low_energy_start
        if low_energy_end:
            current["low_energy_end"] = low_energy_end
        if preferred_session_duration_minutes is not None:
            current["preferred_session_duration_minutes"] = max(15, min(180, preferred_session_duration_minutes))
        if preferred_break_duration_minutes is not None:
            current["preferred_break_duration_minutes"] = max(5, min(60, preferred_break_duration_minutes))

        current["is_explicitly_configured"] = True
        planner["energy_preferences"] = current
        settings.planner = dict(planner)
        flag_modified(settings, "planner")
        settings.updated_at = utc_now()
        db.session.commit()

        return {
            "success": True,
            "energy_preferences": current
        }
