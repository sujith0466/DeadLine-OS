"""
DeadlineOS — Weekly AI Coach Service
====================================
Generates evidence-backed weekly performance reviews, learning insights, and
next-week priorities without fabricating historical claims.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.intelligence import CoachReport
from models.task import Task
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.recovery import RecoveryRecord
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.context_builder import AIContextBuilder
from services.ai.safety import AISafety
from utils.timezone import utc_now

logger = logging.getLogger(__name__)

COACH_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "growth_areas": {"type": "array", "items": {"type": "string"}},
        "weekly_challenge": {"type": "string"},
        "priorities_next_week": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer"}
    },
    "required": ["summary", "strengths", "growth_areas", "weekly_challenge", "priorities_next_week", "evidence", "confidence"]
}


class WeeklyAICoachService:
    @classmethod
    def generate_weekly_report(
        cls,
        user_id: str,
        persist: bool = True,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Generates and optionally persists the weekly coaching report.
        """
        ai_provider = provider or get_default_ai_provider()
        now = utc_now()
        week_ago = now - timedelta(days=7)

        # Gather factual 7-day data
        completed_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.updated_at >= week_ago
        ).all()

        overdue_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.status.in_(["pending", "overdue"]),
            Task.deadline < now
        ).all()

        pending_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.status.in_(["pending", "in_progress"])
        ).order_by(Task.deadline.asc()).limit(5).all()

        recovery_records = RecoveryRecord.query.filter(
            RecoveryRecord.user_id == user_id,
            RecoveryRecord.created_at >= week_ago
        ).all()

        def deterministic_fallback() -> Dict[str, Any]:
            comp_count = len(completed_tasks)
            overdue_count = len(overdue_tasks)
            rec_count = len(recovery_records)

            evidence = [
                f"{comp_count} task(s) marked completed in past 7 days.",
                f"{overdue_count} task(s) currently overdue.",
                f"{rec_count} recovery action(s) logged this week."
            ]

            if comp_count == 0 and overdue_count == 0:
                return {
                    "summary": "Insufficient activity history logged over the past 7 days to generate deep coaching insights.",
                    "strengths": ["Clean baseline environment ready for scheduling."],
                    "growth_areas": ["Begin logging and executing daily focus blocks."],
                    "weekly_challenge": "Schedule and complete your first 3 prioritized tasks this week.",
                    "priorities_next_week": [t.title for t in pending_tasks] or ["Define top 3 weekly goals."],
                    "evidence": evidence,
                    "confidence": 70
                }

            strengths = []
            growth_areas = []
            if comp_count > 0:
                strengths.append(f"Completed {comp_count} task commitments successfully.")
            if rec_count > 0:
                strengths.append("Actively engaged recovery workflows when disruptions occurred.")
            if overdue_count > 0:
                growth_areas.append(f"Triage and reschedule {overdue_count} overdue task(s).")
            else:
                strengths.append("Maintained 100% on-time deadline adherence.")

            if not growth_areas:
                growth_areas.append("Scale focus session length to increase total deep work hours.")

            return {
                "summary": f"Weekly review: Completed {comp_count} tasks with {overdue_count} overdue items.",
                "strengths": strengths,
                "growth_areas": growth_areas,
                "weekly_challenge": "Complete all morning priority blocks before 12:00 PM.",
                "priorities_next_week": [t.title for t in pending_tasks] or ["Review backlog."],
                "evidence": evidence,
                "confidence": 85
            }

        system_prompt = (
            "You are the DeadlineOS Weekly AI Coach. Synthesize actual 7-day task completions and recovery data "
            "into an actionable, honest, evidence-grounded performance review. If data is sparse, state so clearly. "
            "Output strictly conforming to JSON schema."
        )

        user_prompt = (
            f"FACTUAL 7-DAY SUMMARY:\n"
            f"Completed Tasks: {[t.title for t in completed_tasks]}\n"
            f"Overdue Tasks: {[t.title for t in overdue_tasks]}\n"
            f"Upcoming Priorities: {[t.title for t in pending_tasks]}\n"
            f"Recovery Actions Logged: {len(recovery_records)}"
        )

        report_data = ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=COACH_SCHEMA,
            fallback_fn=deterministic_fallback
        )

        # Persist report if requested
        if persist:
            try:
                report = CoachReport(
                    user_id=user_id,
                    strengths=report_data.get("strengths", []),
                    weaknesses=report_data.get("growth_areas", []),
                    insights=[report_data.get("summary", "")],
                    improvement_plan=report_data.get("priorities_next_week", []),
                    weekly_challenge=report_data.get("weekly_challenge", ""),
                    recommendations=report_data.get("growth_areas", [])
                )
                db.session.add(report)
                db.session.commit()
                report_data["report_id"] = report.id
            except Exception as e:
                logger.warning(f"Could not persist CoachReport: {e}")

        return report_data
