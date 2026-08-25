"""
DeadlineOS — Workload Strain Indicator
======================================
Monitors schedule density, continuous execution blocks, and session interruptions
to compute non-clinical execution strain metrics and suggest restorative pacing.
"""

import logging
from typing import Dict, Any, List, Optional
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.context_builder import AIContextBuilder
from services.ai.safety import AISafety

logger = logging.getLogger(__name__)

STRAIN_SCHEMA = {
    "type": "object",
    "properties": {
        "strain_level": {"type": "string", "enum": ["LOW", "MODERATE", "ELEVATED", "HIGH"]},
        "strain_score": {"type": "integer"},
        "contributing_factors": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer"},
        "recommended_restoration": {"type": "string"}
    },
    "required": ["strain_level", "strain_score", "contributing_factors", "reason", "evidence", "confidence", "recommended_restoration"]
}


class WorkloadStrainService:
    @classmethod
    def evaluate_workload_strain(
        cls,
        user_id: str,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Calculates execution strain indicator using hybrid AI reasoning.
        """
        ai_provider = provider or get_default_ai_provider()
        context = AIContextBuilder.build_unified_inference_context(user_id)

        def deterministic_fallback() -> Dict[str, Any]:
            tasks = context.get("tasks", [])
            slots = context.get("schedule", [])
            runtime = context.get("runtime", [])

            strain_score = 15
            factors = []
            evidence = []

            # Factor 1: Schedule density
            total_planned_minutes = sum(
                (s.get("priority_score", 50) for s in slots)
            )
            if len(slots) >= 5:
                strain_score += 25
                factors.append("High slot count today")
                evidence.append(f"{len(slots)} distinct activity slots scheduled today.")

            # Factor 2: Pauses and interruptions
            total_pauses = 0
            for item in runtime:
                for sess in item.get("sessions", []):
                    if sess.get("paused_duration_sec", 0) > 300:
                        total_pauses += 1
            
            if total_pauses >= 3:
                strain_score += 25
                factors.append("Frequent session interruptions")
                evidence.append(f"Multiple extended pause interruptions ({total_pauses}) logged recently.")

            # Factor 3: Pending task backlog
            overdue_count = sum(1 for t in tasks if t.get("status") == "overdue")
            if overdue_count > 0:
                strain_score += 20
                factors.append("Overdue backlog accumulation")
                evidence.append(f"{overdue_count} task(s) currently overdue.")

            strain_score = min(100, max(5, strain_score))
            if strain_score >= 70:
                level = "HIGH"
                rec = "Consider activating Emergency Mode or scheduling a 30m break window."
            elif strain_score >= 50:
                level = "ELEVATED"
                rec = "Pacing warning: insert buffer intervals between consecutive focus blocks."
            elif strain_score >= 30:
                level = "MODERATE"
                rec = "Workload manageable: maintain regular break patterns."
            else:
                level = "LOW"
                rec = "Execution load is optimal with healthy pacing."

            if not evidence:
                evidence.append("Schedule density and session duration are within balanced thresholds.")

            return {
                "strain_level": level,
                "strain_score": strain_score,
                "contributing_factors": factors,
                "reason": f"Execution strain calculated at {strain_score}/100 ({level.lower()}).",
                "evidence": evidence,
                "confidence": 85,
                "recommended_restoration": rec
            }

        system_prompt = (
            "You are the DeadlineOS Workload Strain Indicator. Evaluate execution pace, "
            "schedule density, and pause frequency to assess non-clinical strain. "
            "Do NOT make medical or clinical diagnoses. Output strictly conforming to JSON schema."
        )

        user_prompt = f"USER CONTEXT:\n{context}"

        return ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=STRAIN_SCHEMA,
            fallback_fn=deterministic_fallback
        )
