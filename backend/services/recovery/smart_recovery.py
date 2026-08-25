"""
DeadlineOS — Smart Recovery Engine (Phase 5)
============================================
Deterministic, rule-based recovery recommendations. Explains recovery options
without generative AI or non-deterministic heuristics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.schedule import ScheduleSlot
from models.task import Task
from models.runtime_state import RuntimeState
from services.recovery.service import RecoveryService
from services.scheduling.repository import SchedulingRepository
from utils.timezone import get_user_timezone, to_user_local, utc_now


class SmartRecoveryService:
    """Evaluates user schedule disruption and yields explainable recovery strategies."""

    @classmethod
    def evaluate_recommendations(cls, user_id: str) -> Dict[str, Any]:
        tz_name = get_user_timezone(user_id)
        now_utc = utc_now()
        local_now = to_user_local(now_utc, tz_name)

        recoverable = RecoveryService.get_recoverable_items(user_id)
        missed = recoverable.get("missed", [])
        overdue = recoverable.get("overdue", [])
        interrupted = recoverable.get("interrupted", [])

        strategies: List[Dict[str, Any]] = []

        # Rule 1: Missed slots with remaining time in day -> Reschedule Strategy
        if missed:
            # Check remaining daytime hours
            end_of_day = datetime(local_now.year, local_now.month, local_now.day, 22, 0, tzinfo=timezone.utc)
            remaining_hours = max(0.0, (end_of_day - now_utc).total_seconds() / 3600.0)
            
            if remaining_hours >= 2.0:
                actions = []
                for idx, m in enumerate(missed[:3]):
                    suggested_start = now_utc + timedelta(minutes=30 + (idx * 60))
                    actions.append({
                        "action": "RESCHEDULE",
                        "schedule_id": m["id"],
                        "entity_id": m.get("entity_id"),
                        "entity_type": m.get("entity_type", "TASK"),
                        "new_start_time": suggested_start.isoformat(),
                        "description": f"Move '{m.get('task_title', 'Activity')}' to {suggested_start.strftime('%H:%M')} UTC"
                    })

                strategies.append({
                    "name": "Intraday Schedule Shift",
                    "impact": f"Reschedules {len(actions)} missed activities into remaining {int(remaining_hours)}h window today.",
                    "success_prob": 90,
                    "confidence_score": 0.95,
                    "rationale": "Sufficient daytime capacity remains to complete missed commitments today.",
                    "actions": actions
                })
            else:
                # Rule 2: Insufficient remaining daytime -> Defer / Skip Today Strategy
                actions = [
                    {
                        "action": "SKIP",
                        "schedule_id": m["id"],
                        "entity_id": m.get("entity_id"),
                        "entity_type": m.get("entity_type", "TASK"),
                        "description": f"Skip '{m.get('task_title', 'Activity')}' for today to avoid burnout"
                    }
                    for m in missed[:5]
                ]
                strategies.append({
                    "name": "Evening Clean Slate",
                    "impact": f"Safely skips {len(actions)} missed activities for today.",
                    "success_prob": 85,
                    "confidence_score": 0.90,
                    "rationale": "Less than 2 hours remain before end of day. Skipping non-essential items prevents schedule overload.",
                    "actions": actions
                })

        # Rule 3: Interrupted sessions -> Resume Top Interrupted Task
        if interrupted:
            top_int = interrupted[0]
            strategies.append({
                "name": "Resume Priority Interruption",
                "impact": f"Re-engage interrupted session for {top_int.get('entity_type')} {top_int.get('entity_id')}.",
                "success_prob": 95,
                "confidence_score": 0.98,
                "rationale": "Active runtime progress was recorded before unexpected interruption.",
                "actions": [
                    {
                        "action": "RESUME",
                        "entity_id": top_int["entity_id"],
                        "entity_type": top_int.get("entity_type", "TASK"),
                        "description": f"Resume {top_int.get('entity_type')} {top_int.get('entity_id')}"
                    }
                ]
            })

        # Rule 4: Overdue tasks prioritization
        if overdue and not strategies:
            # Sort by priority score
            sorted_overdue = sorted(overdue, key=lambda x: x.get("priority_score", 0), reverse=True)
            actions = [
                {
                    "action": "RESCHEDULE",
                    "entity_id": t["id"],
                    "entity_type": "TASK",
                    "description": f"Prioritize overdue task '{t['title']}'"
                }
                for t in sorted_overdue[:2]
            ]
            strategies.append({
                "name": "Overdue Triage Recovery",
                "impact": f"Triage {len(actions)} highest priority overdue tasks.",
                "success_prob": 80,
                "confidence_score": 0.85,
                "rationale": "Overdue items detected past deadline require immediate triage.",
                "actions": actions
            })

        return {
            "threats_count": recoverable.get("total_threats", 0),
            "strategies": strategies
        }
