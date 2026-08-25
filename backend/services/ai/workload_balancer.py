"""
DeadlineOS — Dynamic Workload Balancer
======================================
Analyzes schedule congestion and peak day loads, generating explainable
rebalancing proposals without directly mutating authoritative ScheduleSlot records.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.context_builder import AIContextBuilder
from utils.timezone import utc_now, to_user_local, get_user_timezone

logger = logging.getLogger(__name__)

WORKLOAD_BALANCER_SCHEMA = {
    "type": "object",
    "properties": {
        "is_overloaded": {"type": "boolean"},
        "overloaded_dates": {"type": "array", "items": {"type": "string"}},
        "redistribution_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "title": {"type": "string"},
                    "suggested_action": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["entity_id", "title", "suggested_action", "reason"]
            }
        },
        "reason": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer"}
    },
    "required": ["is_overloaded", "overloaded_dates", "redistribution_plan", "reason", "evidence", "confidence"]
}


class WorkloadBalancerService:
    @classmethod
    def evaluate_workload(
        cls,
        user_id: str,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Evaluates daily task loads and generates rebalancing recommendations.
        """
        ai_provider = provider or get_default_ai_provider()
        context = AIContextBuilder.build_unified_inference_context(user_id)
        tz_name = get_user_timezone(user_id)

        def deterministic_fallback() -> Dict[str, Any]:
            tasks = context.get("tasks", [])
            slots = context.get("schedule", [])
            now = utc_now()
            
            # Group slots by local day
            day_load_minutes: Dict[str, int] = {}
            for s in slots:
                if s.get("start_time") and s.get("end_time"):
                    try:
                        st = datetime.fromisoformat(s["start_time"])
                        et = datetime.fromisoformat(s["end_time"])
                        day_str = to_user_local(st, tz_name).strftime("%Y-%m-%d")
                        duration_m = max(0, int((et - st).total_seconds() / 60))
                        day_load_minutes[day_str] = day_load_minutes.get(day_str, 0) + duration_m
                    except Exception:
                        pass

            overloaded_dates = []
            evidence = []
            proposals = []

            for d_str, total_mins in day_load_minutes.items():
                if total_mins > 360:  # > 6 hours in schedule slots
                    overloaded_dates.append(d_str)
                    evidence.append(f"Date {d_str} has {total_mins // 60}h {total_mins % 60}m scheduled, exceeding 6h focus threshold.")

            # Identify candidates for redistribution
            if overloaded_dates:
                for s in slots:
                    if s.get("priority_score", 50) < 60:
                        proposals.append({
                            "entity_id": s.get("entity_id") or s.get("id"),
                            "title": s.get("task_title", "Low Priority Block"),
                            "suggested_action": "SHIFT_TO_NEXT_OPEN_WINDOW",
                            "reason": "Lower priority activity scheduled during overloaded day."
                        })
                        if len(proposals) >= 3:
                            break

            is_overloaded = len(overloaded_dates) > 0
            if not evidence:
                evidence.append("Workload is evenly distributed across available days.")

            return {
                "is_overloaded": is_overloaded,
                "overloaded_dates": overloaded_dates,
                "redistribution_plan": proposals,
                "reason": f"Analyzed {len(slots)} schedule blocks across current window.",
                "evidence": evidence,
                "confidence": 85
            }

        system_prompt = (
            "You are the DeadlineOS Dynamic Workload Balancer. Analyze user schedule congestion "
            "and suggest non-destructive rebalancing actions. Output strictly conforming to JSON schema."
        )

        user_prompt = f"USER CONTEXT:\n{context}"

        return ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=WORKLOAD_BALANCER_SCHEMA,
            fallback_fn=deterministic_fallback
        )
