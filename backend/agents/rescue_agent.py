"""
DeadlineOS — Rescue Agent
=============================
An emergency productivity strategist whose sole objective is 
preventing deadline failure by analyzing risks and generating 
actionable recovery plans.
"""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

RESCUE_SYSTEM_PROMPT = """You are the Rescue Agent in DeadlineOS — an emergency productivity strategist whose sole objective is preventing deadline failure.
Your goal is to detect when users are at risk of missing deadlines and automatically generate highly actionable recovery plans.

CORE RESPONSIBILITIES:
1. Detect deadline risk, overloaded schedules, and unfinished critical work.
2. Predict the likelihood of meeting deadlines given the current pace vs remaining work.
3. Generate realistic, actionable intervention plans (e.g. scoping down, finding more time).
4. Recommend concrete schedule adjustments and reprioritizations.

Output exactly according to the requested JSON schema."""

RESCUE_USER_PROMPT_TEMPLATE = """
AT-RISK TASKS:
{tasks_json}

USER AVAILABILITY:
{availability_json}

Analyze the situation and generate an emergency recovery plan.
"""

RESCUE_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_detected": {"type": "boolean", "description": "True if there is a genuine risk of missing deadlines"},
        "risk_level": {"type": "string", "enum": ["High", "Medium", "Low", "None"], "description": "Severity of the risk"},
        "success_probability": {
            "type": "integer", 
            "description": "0-100 score estimating the likelihood of success if the recovery plan is followed"
        },
        "recovery_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "A specific, actionable recovery step"}
                },
                "required": ["action"]
            }
        },
        "recommended_schedule_adjustments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Name of the task"},
                    "new_time_block": {"type": "string", "description": "Suggested new time block, e.g. 18:00-21:00"}
                },
                "required": ["task", "new_time_block"]
            }
        },
        "reasoning": {
            "type": "string",
            "description": "Explanation of why the risk exists and why the plan will work"
        }
    },
    "required": [
        "risk_detected", 
        "risk_level", 
        "success_probability", 
        "recovery_plan", 
        "recommended_schedule_adjustments", 
        "reasoning"
    ]
}

class RescueAgent:
    """Agent responsible for detecting deadline risks and formulating recovery plans."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def generate_recovery_plan(self, tasks: List[Dict[str, Any]], availability: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates an emergency recovery plan and evaluates deadline risk.
        
        Args:
            tasks: list of task dicts (title, deadline, estimated_hours, completed_hours, priority_score)
            availability: dict containing daily_available_hours and any constraints
            
        Returns:
            dict: Structured recovery plan containing risk levels, probability, and actions.
        """
        if not tasks:
            return {
                "risk_detected": False,
                "risk_level": "None",
                "success_probability": 100,
                "recovery_plan": [],
                "recommended_schedule_adjustments": [],
                "reasoning": "No active tasks require rescue."
            }

        user_prompt = RESCUE_USER_PROMPT_TEMPLATE.format(
            tasks_json=json.dumps(tasks, indent=2),
            availability_json=json.dumps(availability, indent=2)
        )
        
        logger.warning("🚨 Rescue Agent analyzing situation for %d tasks", len(tasks))
        
        try:
            result = self.gemini.generate_structured(
                system_prompt=RESCUE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema=RESCUE_SCHEMA,
                temperature=0.3  # Slightly higher than Priority/Planning for creative problem-solving
            )
            return result
        except Exception as exc:
            logger.error("Rescue Agent failed to generate recovery plan: %s", exc)
            raise
