"""
DeadlineOS — AI Miss Prediction Service
=======================================
Predicts whether scheduled tasks or activities are at risk of missing their deadlines
based on total pending workload, historical pace, and deadline proximity.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.context_builder import AIContextBuilder
from services.ai.safety import AISafety
from utils.timezone import utc_now

logger = logging.getLogger(__name__)

MISS_PREDICTION_SCHEMA = {
    "type": "object",
    "properties": {
        "miss_probability": {"type": "integer"},
        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "at_risk_tasks": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer"},
        "recommended_action": {"type": "string"}
    },
    "required": ["miss_probability", "risk_level", "at_risk_tasks", "reason", "evidence", "confidence", "recommended_action"]
}


class MissPredictionService:
    @classmethod
    def predict_miss_risk(
        cls,
        user_id: str,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Evaluates the probability of missing upcoming deadlines.
        """
        ai_provider = provider or get_default_ai_provider()
        context = AIContextBuilder.build_unified_inference_context(user_id)

        def deterministic_fallback() -> Dict[str, Any]:
            tasks = context.get("tasks", [])
            now = utc_now()
            at_risk = []
            evidence = []
            total_hours_needed = 0.0

            for t in tasks:
                if t.get("status") == "overdue":
                    at_risk.append(t["title"])
                    evidence.append(f"Task '{t['title']}' is already past deadline.")
                elif t.get("deadline"):
                    try:
                        dl = datetime.fromisoformat(t["deadline"]).replace(tzinfo=timezone.utc)
                        hours_left = max(0.1, (dl - now).total_seconds() / 3600)
                        needed = (t.get("estimated_hours") or 1.0) - (t.get("actual_hours") or 0.0)
                        needed = max(0.2, needed)
                        total_hours_needed += needed
                        if needed > hours_left:
                            at_risk.append(t["title"])
                            evidence.append(f"Task '{t['title']}' needs {needed:.1f}h but only {hours_left:.1f}h remain before deadline.")
                    except Exception:
                        pass

            miss_prob = 10
            if at_risk:
                miss_prob = min(95, 30 + len(at_risk) * 20)

            if miss_prob > 75:
                risk_level = "CRITICAL"
                rec = "Workload deficit detected: open Recovery Center to triage or defer lower-priority tasks."
            elif miss_prob > 50:
                risk_level = "HIGH"
                rec = "Tight deadline margin: prioritize critical tasks immediately."
            elif miss_prob > 25:
                risk_level = "MEDIUM"
                rec = "Moderate load: maintain current pace."
            else:
                risk_level = "LOW"
                rec = "All deadlines currently on track."

            if not evidence:
                evidence.append(f"Total workload ({total_hours_needed:.1f}h) is within available scheduling capacity.")

            return {
                "miss_probability": miss_prob,
                "risk_level": risk_level,
                "at_risk_tasks": at_risk,
                "reason": f"Capacity analysis identified {len(at_risk)} task(s) with tight deadline margins.",
                "evidence": evidence,
                "confidence": 85,
                "recommended_action": rec
            }

        system_prompt = (
            "You are the DeadlineOS Miss Prediction Intelligence. Analyze task estimates and deadline proximity "
            "to calculate miss probabilities and identify at-risk items. Output strictly conforming to the requested schema."
        )

        user_prompt = f"USER CONTEXT:\n{context}"

        return ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=MISS_PREDICTION_SCHEMA,
            fallback_fn=deterministic_fallback
        )
