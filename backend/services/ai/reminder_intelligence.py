"""
DeadlineOS — Adaptive Reminder Intelligence
===========================================
Recommends tailored pre-alert and reminder timing based on schedule slot priority,
duration, and user responsiveness while strictly respecting quiet hours and notification limits.
"""

import logging
from typing import Dict, Any, List, Optional
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.context_builder import AIContextBuilder
from services.ai.safety import AISafety

logger = logging.getLogger(__name__)

REMINDER_INTELLIGENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_pre_alerts": {"type": "array", "items": {"type": "integer"}},
        "recommended_reminders": {"type": "array", "items": {"type": "integer"}},
        "reason": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer"}
    },
    "required": ["recommended_pre_alerts", "recommended_reminders", "reason", "evidence", "confidence"]
}


class AdaptiveReminderService:
    @classmethod
    def recommend_reminder_timing(
        cls,
        user_id: str,
        slot_duration_minutes: int = 60,
        priority_score: int = 50,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Recommends tailored offsets for pre-alerts and countdown reminders.
        """
        ai_provider = provider or get_default_ai_provider()
        context = AIContextBuilder.build_unified_inference_context(user_id)

        def deterministic_fallback() -> Dict[str, Any]:
            evidence = []
            if priority_score >= 80:
                pre_alerts = [30, 15]
                reminders = [10, 5, 1]
                evidence.append("High priority activity: expanded multi-offset reminder sequence.")
            elif slot_duration_minutes >= 120:
                pre_alerts = [30, 15]
                reminders = [10, 5]
                evidence.append("Extended focus block (>= 2h): early 30m prep alert recommended.")
            elif slot_duration_minutes <= 30:
                pre_alerts = [10]
                reminders = [3]
                evidence.append("Short sprint (<= 30m): compact single pre-alert sequence.")
            else:
                pre_alerts = [15]
                reminders = [5]
                evidence.append("Standard activity: baseline 15m and 5m notifications.")

            return {
                "recommended_pre_alerts": pre_alerts,
                "recommended_reminders": reminders,
                "reason": f"Timing calculated based on {slot_duration_minutes}m duration and priority {priority_score}.",
                "evidence": evidence,
                "confidence": 90
            }

        system_prompt = (
            "You are the DeadlineOS Adaptive Reminder Intelligence. Analyze slot duration and priority "
            "to recommend optimal minute offsets for notifications. Output strictly conforming to JSON schema."
        )

        user_prompt = (
            f"SLOT DETAILS: duration={slot_duration_minutes}m, priority={priority_score}\n"
            f"USER CONTEXT:\n{context}"
        )

        return ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=REMINDER_INTELLIGENCE_SCHEMA,
            fallback_fn=deterministic_fallback
        )
