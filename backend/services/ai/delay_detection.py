"""
DeadlineOS — AI Delay Detection Service
=======================================
Detects execution delay signals (session drift, pause frequency, elapsed vs planned)
and generates explainable delay risk recommendations with 100% deterministic fallbacks.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.context_builder import AIContextBuilder
from services.ai.safety import AISafety
from utils.timezone import utc_now

logger = logging.getLogger(__name__)

DELAY_SCHEMA = {
    "type": "object",
    "properties": {
        "delay_probability": {"type": "integer"},
        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "reason": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer"},
        "recommended_action": {"type": "string"}
    },
    "required": ["delay_probability", "risk_level", "reason", "evidence", "confidence", "recommended_action"]
}


class DelayDetectionService:
    @classmethod
    def evaluate_delay_risk(
        cls,
        user_id: str,
        entity_id: Optional[str] = None,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Evaluates delay risk using hybrid AI reasoning with strict deterministic fallback.
        """
        ai_provider = provider or get_default_ai_provider()
        context = AIContextBuilder.build_unified_inference_context(user_id)

        # Deterministic fallback calculation
        def deterministic_fallback() -> Dict[str, Any]:
            runtime_items = context.get("runtime", [])
            evidence = []
            delay_prob = 15
            risk_level = "LOW"
            rec = "Continue execution as planned."

            for item in runtime_items:
                for sess in item.get("sessions", []):
                    paused = sess.get("paused_duration_sec", 0)
                    planned = sess.get("planned_duration_sec", 1800)
                    if paused > 600:
                        delay_prob += 35
                        evidence.append(f"Extended pause time detected: {paused // 60} minutes")
                    if paused > planned * 0.5:
                        delay_prob += 30
                        evidence.append("Pause duration exceeds 50% of planned block")

            delay_prob = min(100, max(0, delay_prob))
            if delay_prob > 75:
                risk_level = "CRITICAL"
                rec = "Schedule drift high: consider pausing or splitting remaining work."
            elif delay_prob > 50:
                risk_level = "HIGH"
                rec = "Delay risk elevated: streamline current block to meet planned window."
            elif delay_prob > 30:
                risk_level = "MEDIUM"
                rec = "Minor drift detected: maintain focus to complete on time."

            if not evidence:
                evidence.append("Activity duration and pause patterns are within normal operational limits.")

            return {
                "delay_probability": delay_prob,
                "risk_level": risk_level,
                "reason": f"Heuristic evaluation indicates {risk_level.lower()} delay risk.",
                "evidence": evidence,
                "confidence": 85,
                "recommended_action": rec
            }

        system_prompt = (
            "You are the DeadlineOS Delay Detection Intelligence. Analyze the user's active session, "
            "pause patterns, and schedule context to assess the likelihood of activity delay. "
            "Output strictly according to the requested JSON schema without fabricating facts."
        )

        user_prompt = f"USER CONTEXT:\n{context}"

        return ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=DELAY_SCHEMA,
            fallback_fn=deterministic_fallback
        )
