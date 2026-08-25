"""
DeadlineOS — Analytics Service
==============================
Aggregates historical data from all AI Agents to power the
Executive Intelligence Dashboard.
"""

import os
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from database.db import db
from sqlalchemy import func
from models.task import Task
from models.intervention import Intervention
from models.intelligence import AccountabilityMetrics, CoachReport, ReflectionReport
from models.telemetry import AgentExecutionLog, TwinSimulationLog


class AnalyticsService:

    @classmethod
    def get_overview(cls, user_id: str = None) -> Dict[str, Any]:
        """Returns the Executive Scorecard metrics dynamically."""
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        total_tasks = Task.query.filter_by(user_id=uid).count()
        completed_tasks = Task.query.filter_by(user_id=uid, status="done").count()

        completion_rate = (
            int((completed_tasks / total_tasks * 100)) if total_tasks else 0
        )
        success_rate = completion_rate  # simplified

        avg_conf = (
            db.session.query(func.avg(AgentExecutionLog.confidence))
            .filter_by(user_id=uid)
            .scalar()
            or 0
        )

        latest_twin = (
            TwinSimulationLog.query.filter_by(user_id=uid)
            .order_by(TwinSimulationLog.created_at.desc())
            .first()
        )
        future_risk = "Low"
        if latest_twin and latest_twin.projected_risk_score:
            r = latest_twin.projected_risk_score
            future_risk = "High" if r > 70 else "Medium" if r > 40 else "Low"

        latest_acc = (
            AccountabilityMetrics.query.filter_by(user_id=uid)
            .order_by(AccountabilityMetrics.created_at.desc())
            .first()
        )
        prod_score = latest_acc.productivity_score if latest_acc else 0
        risk_level = latest_acc.risk_profile if latest_acc else "Low"

        return {
            "productivity_score": prod_score,
            "completion_rate": completion_rate,
            "deadline_success_rate": success_rate,
            "current_risk_level": risk_level,
            "future_risk_forecast": future_risk,
            "ai_confidence_score": int(avg_conf),
        }

    @classmethod
    def get_productivity_trends(cls, user_id: str = None) -> List[Dict[str, Any]]:
        """Returns time-series data for area/line charts from DB."""
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        metrics = (
            AccountabilityMetrics.query.filter_by(user_id=uid)
            .order_by(AccountabilityMetrics.created_at.desc())
            .limit(30)
            .all()
        )
        metrics.reverse()
        return [
            {
                "date": m.created_at.strftime("%Y-%m-%d"),
                "productivity": m.productivity_score,
                "completion": m.completion_rate,
                "procrastination": m.procrastination_score,
                "consistency": m.consistency_score,
            }
            for m in metrics
        ]

    @classmethod
    def get_agent_contributions(cls, user_id: str = None) -> List[Dict[str, Any]]:
        """Returns analytics on how often each agent is utilized."""
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        counts = (
            db.session.query(
                AgentExecutionLog.agent_name, func.count(AgentExecutionLog.id)
            )
            .filter_by(user_id=uid)
            .group_by(AgentExecutionLog.agent_name)
            .all()
        )
        return [{"agent": agent_name, "uses": count} for agent_name, count in counts]

    @classmethod
    def get_intelligence_reports(cls, user_id: str = None) -> Dict[str, Any]:
        """Returns the latest Coach and Reflection data for text grids."""
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        coach = (
            CoachReport.query.filter_by(user_id=uid)
            .order_by(CoachReport.created_at.desc())
            .first()
        )
        reflection = (
            ReflectionReport.query.filter_by(user_id=uid)
            .order_by(ReflectionReport.created_at.desc())
            .first()
        )

        return {
            "coach": coach.to_dict() if coach else {},
            "reflection": reflection.to_dict() if reflection else {},
        }

    @classmethod
    def get_productivity_heatmap(cls, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Returns data formatted for a GitHub-style activity heatmap.

        Each entry represents one calendar day and carries:
            date  : YYYY-MM-DD string
            count : number of productive activities completed that day
            level : 0-4 intensity bucket (0=none, 4=very high)

        Data sources:
            - HabitLog (completed=True entries, keyed by `date`)
            - Task (status='done', keyed by `updated_at` date in UTC)

        Covers the trailing 365 days from today (UTC).
        """
        from flask import g
        from models.goal import HabitLog
        from models.task import Task
        from collections import defaultdict
        from datetime import date, timedelta, timezone

        uid = user_id or getattr(g, "user_id", None)

        today_utc = datetime.now(timezone.utc).date()
        cutoff = today_utc - timedelta(days=364)  # inclusive 365-day window

        # Initialise every date in the window with count=0
        day_counts: dict[str, int] = defaultdict(int)
        cursor = cutoff
        while cursor <= today_utc:
            day_counts[cursor.isoformat()] = 0
            cursor += timedelta(days=1)

        # --- HabitLog contributions ---
        try:
            habit_logs = (
                HabitLog.query.filter_by(user_id=uid, completed=True)
                .filter(HabitLog.date >= cutoff.isoformat())
                .all()
            )
            for log in habit_logs:
                if log.date and log.date in day_counts:
                    day_counts[log.date] += 1
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                f"[heatmap] Failed to query HabitLog for user {uid}: {e}"
            )

        # --- Task completion contributions ---
        try:
            done_tasks = (
                Task.query.filter_by(user_id=uid, status="done")
                .filter(
                    Task.updated_at
                    >= datetime(
                        cutoff.year, cutoff.month, cutoff.day, tzinfo=timezone.utc
                    )
                )
                .all()
            )
            for task in done_tasks:
                if task.updated_at:
                    task_date = (
                        task.updated_at.date().isoformat()
                        if hasattr(task.updated_at, "date")
                        else str(task.updated_at)[:10]
                    )
                    if task_date in day_counts:
                        day_counts[task_date] += 1
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                f"[heatmap] Failed to query Tasks for user {uid}: {e}"
            )

        # --- Compute intensity level (0-4 buckets) ---
        max_count = max(day_counts.values()) if day_counts else 1
        max_count = max(max_count, 1)  # avoid division by zero

        def _level(count: int) -> int:
            if count == 0:
                return 0
            ratio = count / max_count
            if ratio <= 0.25:
                return 1
            elif ratio <= 0.50:
                return 2
            elif ratio <= 0.75:
                return 3
            return 4

        return [
            {"date": date_str, "count": count, "level": _level(count)}
            for date_str, count in sorted(day_counts.items())
        ]

    @classmethod
    def generate_chief_of_staff_briefing(cls, user_id: str = None) -> str:
        """Generates dynamic briefing based on system telemetry using Phase 6 AI Provider hierarchy."""
        from flask import g
        from services.ai.provider import get_default_ai_provider

        uid = user_id or getattr(g, "user_id", None)

        overview = cls.get_overview(uid)
        active_goals = Task.query.filter_by(user_id=uid, status="in_progress").count()
        open_interventions = Intervention.query.filter_by(
            user_id=uid, resolved=False
        ).count()

        prod_score = overview.get("productivity_score", 0)
        risk_level = overview.get("future_risk_forecast", "Unknown")

        try:
            has_interv = int(open_interventions) > 0
        except (TypeError, ValueError):
            has_interv = False

        interv_str = (
            f" {open_interventions} open interventions require attention."
            if has_interv
            else " No critical interventions at this time."
        )
        deterministic_fallback = (
            f"System operations are active with a productivity score of {prod_score}%. "
            f"Future risk is currently assessed as {risk_level}.{interv_str}"
        )

        from flask import current_app
        gemini = current_app.extensions.get("gemini_service") if current_app else None
        if gemini and hasattr(gemini, "generate_text"):
            try:
                prompt = (
                    f"Act as an AI Chief-of-Staff. Provide a strictly 2-sentence executive briefing. "
                    f"Telemetry: Productivity={prod_score}%, Active Tasks={active_goals}, "
                    f"Open Interventions={open_interventions}, Future Risk={risk_level}. "
                    f"Tone: Professional, crisp, Palantir-esque."
                )
                briefing_text = gemini.generate_text(prompt)
                if briefing_text:
                    return briefing_text.replace("\n", " ").strip()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Gemini extension briefing failed: {e}")

        try:
            ai_provider = get_default_ai_provider()
            system_prompt = (
                "Act as an AI Chief-of-Staff for an executive productivity OS. "
                "Provide a strictly 2-sentence executive summary. Tone: Crisp, professional, strategic."
            )
            user_prompt = (
                f"Telemetry: Productivity={prod_score}%, Active Tasks={active_goals}, "
                f"Open Interventions={open_interventions}, Future Risk={risk_level}."
            )
            briefing_text = ai_provider.generate_text(system_prompt, user_prompt)
            if (
                briefing_text
                and not briefing_text.startswith("OpenRouter API key not configured")
                and not briefing_text.startswith("AI text response unavailable")
                and not briefing_text.startswith("Deterministic baseline")
            ):
                return briefing_text.replace("\n", " ").strip()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to generate AI briefing, using deterministic fallback: {e}"
            )

        return deterministic_fallback

    @classmethod
    def get_agent_metrics(cls, agent_name: str, user_id: str = None) -> Dict[str, Any]:
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        logs = AgentExecutionLog.query.filter_by(
            user_id=uid, agent_name=agent_name
        ).all()
        successes = len([l for l in logs if l.status == "success"])
        avg_time = (
            db.session.query(func.avg(AgentExecutionLog.execution_time_ms))
            .filter_by(user_id=uid, agent_name=agent_name)
            .scalar()
            or 0
        )
        avg_conf = (
            db.session.query(func.avg(AgentExecutionLog.confidence))
            .filter_by(user_id=uid, agent_name=agent_name)
            .scalar()
            or 0
        )

        last_log = (
            AgentExecutionLog.query.filter_by(user_id=uid, agent_name=agent_name)
            .order_by(AgentExecutionLog.created_at.desc())
            .first()
        )
        last_execution_time = last_log.created_at.isoformat() if last_log else None

        total = len(logs)
        success_rate = int(successes / total * 100) if total else 0
        failure_rate = 100 - success_rate if total else 0

        result = {
            "total_executions": total,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_execution_ms": int(avg_time),
            "average_confidence": int(avg_conf),
            "last_execution_time": last_execution_time,
            "history": [l.to_dict() for l in logs[-10:]],
        }

        if agent_name == "Vision Agent":
            ocr_count = len([l for l in logs if l.action == "OCR Extraction"])
            gemini_count = len(
                [
                    l
                    for l in logs
                    if l.action == "Gemini Extraction"
                    or l.action == "Image Upload Extraction"
                ]
            )
            ocr_fallback_rate = int((gemini_count / total) * 100) if total else 0

            result["ocr_processed_images"] = ocr_count
            result["gemini_processed_images"] = gemini_count
            result["ocr_fallback_rate"] = ocr_fallback_rate

        return result

    @classmethod
    def get_intervention_metrics(cls, user_id: str = None) -> Dict[str, Any]:
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        total = Intervention.query.filter_by(user_id=uid).count()
        resolved = Intervention.query.filter_by(user_id=uid, resolved=True).count()
        return {
            "total_generated": total,
            "resolved": resolved,
            "resolution_rate": int(resolved / total * 100) if total else 0,
            "active": total - resolved,
        }

    @classmethod
    def get_twin_accuracy(cls, user_id: str = None) -> Dict[str, Any]:
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        total = TwinSimulationLog.query.filter_by(user_id=uid).count()
        avg_impact = (
            db.session.query(func.avg(TwinSimulationLog.capacity_impact))
            .filter_by(user_id=uid)
            .scalar()
            or 0
        )
        recent = (
            TwinSimulationLog.query.filter_by(user_id=uid)
            .order_by(TwinSimulationLog.created_at.desc())
            .limit(5)
            .all()
        )
        recent.reverse()
        return {
            "total_simulations": total,
            "average_capacity_impact": int(avg_impact),
            "recent_simulations": [l.to_dict() for l in recent],
        }

    @classmethod
    def get_insights(cls, user_id: str = None) -> Dict[str, Any]:
        """Returns telemetry-driven Insights Engine data."""
        import logging
        import traceback
        from flask import g

        logger = logging.getLogger(__name__)
        uid = user_id or getattr(g, "user_id", None)

        logger.info(f"[AnalyticsService] Starting get_insights for user_id={uid}")

        try:
            logger.info(
                f"[AnalyticsService] Fetching AccountabilityMetrics for user_id={uid}"
            )
            latest_acc = (
                AccountabilityMetrics.query.filter_by(user_id=uid)
                .order_by(AccountabilityMetrics.created_at.desc())
                .first()
            )

            top_risk = "N/A"
            top_opportunity = "N/A"
            if (
                latest_acc
                and latest_acc.key_findings
                and isinstance(latest_acc.key_findings, list)
            ):
                findings = latest_acc.key_findings
                top_risk = findings[0] if len(findings) > 0 else "N/A"
                top_opportunity = findings[1] if len(findings) > 1 else "N/A"

            logger.info(
                f"[AnalyticsService] Fetching AgentExecutionLog metrics for user_id={uid}"
            )
            counts = (
                db.session.query(
                    AgentExecutionLog.agent_name,
                    func.count(AgentExecutionLog.id).label("total"),
                    func.avg(AgentExecutionLog.confidence).label("avg_conf"),
                )
                .filter_by(user_id=uid)
                .group_by(AgentExecutionLog.agent_name)
                .all()
            )

            most_used_agent = "N/A"
            most_accurate_agent = "N/A"

            if counts:
                # Safe aggregation avoiding None comparisons
                most_used = max(
                    counts, key=lambda x: x.total if x.total is not None else 0
                )
                most_used_agent = most_used.agent_name if most_used.total else "N/A"

                most_accurate = max(
                    counts, key=lambda x: x.avg_conf if x.avg_conf is not None else 0
                )
                most_accurate_agent = (
                    most_accurate.agent_name if most_accurate.avg_conf else "N/A"
                )

            logger.info(f"[AnalyticsService] Fetching Interventions for user_id={uid}")
            interventions = Intervention.query.filter_by(
                user_id=uid, resolved=True
            ).all()
            least_effective = "N/A"

            if interventions:
                # Filter out None scores before taking min
                valid_interventions = [
                    i for i in interventions if i.confidence_score is not None
                ]
                if valid_interventions:
                    least_effective_intervention = min(
                        valid_interventions, key=lambda x: x.confidence_score
                    )
                    least_effective = least_effective_intervention.type or "N/A"

            focus = (
                "Review active interventions" if interventions else "Define new goals"
            )
            if (
                latest_acc
                and latest_acc.recommendations
                and isinstance(latest_acc.recommendations, list)
            ):
                if len(latest_acc.recommendations) > 0:
                    focus = latest_acc.recommendations[0]

            response_data = {
                "top_risk": top_risk,
                "top_opportunity": top_opportunity,
                "most_used_agent": most_used_agent,
                "most_accurate_agent": most_accurate_agent,
                "least_effective_intervention": least_effective,
                "recommended_focus_area": focus,
                # Merging requested fallback schema to satisfy external client requirements
                "productivity": [],
                "completion_velocity": [],
                "habit_consistency": [],
                "intervention_metrics": {},
                "agent_metrics": {},
                "summary": {
                    "productivity_score": (
                        latest_acc.productivity_score
                        if latest_acc and latest_acc.productivity_score
                        else 0
                    ),
                    "success_probability": 0,
                    "future_risk": "LOW",
                },
            }

            logger.info(
                f"[AnalyticsService] get_insights completed successfully for user_id={uid}"
            )
            return response_data

        except Exception as e:
            logger.error(
                f"[AnalyticsService] Critical error in get_insights for user_id={uid}: {str(e)}"
            )
            logger.error(traceback.format_exc())

            # Return sensible defaults rather than throwing HTTP 500
            return {
                "top_risk": "N/A",
                "top_opportunity": "N/A",
                "most_used_agent": "N/A",
                "most_accurate_agent": "N/A",
                "least_effective_intervention": "N/A",
                "recommended_focus_area": "Define new goals",
                "productivity": [],
                "completion_velocity": [],
                "habit_consistency": [],
                "intervention_metrics": {},
                "agent_metrics": {},
                "summary": {
                    "productivity_score": 0,
                    "success_probability": 0,
                    "future_risk": "LOW",
                },
            }
