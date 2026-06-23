"""
DeadlineOS — Planning Agent
=============================
An elite AI Scheduling Engine that transforms prioritized tasks 
into actionable execution schedules with focus blocks.
"""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

PLANNING_SYSTEM_PROMPT = """You are the Planning Agent in DeadlineOS — an elite executive assistant responsible for ensuring every task is completed before deadlines.
Your goal is to transform prioritized tasks into a realistic, actionable execution schedule.

SCHEDULE RULES:
1. Highest priority score tasks should be scheduled first.
2. Tasks with the nearest deadline must be prioritized.
3. NEVER schedule overlapping tasks.
4. Respect the user's daily available hours and preferred work window.
5. Include short breaks between tasks to maintain productivity.
6. Designate critical, deep-work sessions as "focus_block": true.
7. Return a 'confidence_score' (0-100) estimating the probability of completing all scheduled tasks before their deadlines.

Output exactly according to the requested JSON schema."""

PLANNING_USER_PROMPT_TEMPLATE = """
TASKS TO SCHEDULE:
{tasks_json}

USER AVAILABILITY:
{availability_json}

Generate the optimal schedule.
"""

PLANNING_SCHEMA = {
    "type": "object",
    "properties": {
        "schedule": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD format"},
                    "task": {"type": "string", "description": "Task title exactly as provided"},
                    "start_time": {"type": "string", "description": "HH:MM 24-hour format"},
                    "end_time": {"type": "string", "description": "HH:MM 24-hour format"},
                    "focus_block": {"type": "boolean", "description": "True if this requires deep uninterrupted focus"}
                },
                "required": ["date", "task", "start_time", "end_time", "focus_block"]
            }
        },
        "daily_summary": {
            "type": "string",
            "description": "A 1-2 sentence executive summary of the daily plan"
        },
        "confidence_score": {
            "type": "integer",
            "description": "0-100 score estimating probability of deadline success for this schedule"
        }
    },
    "required": ["schedule", "daily_summary", "confidence_score"]
}

class PlanningAgent:
    """Agent responsible for transforming prioritized tasks into daily schedules."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def generate_plan(self, tasks: List[Dict[str, Any]], availability: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates an actionable daily execution schedule.
        
        Args:
            tasks: list of task dicts (title, deadline, estimated_hours, priority_score)
            availability: dict containing daily_available_hours and preferred_work_hours
            
        Returns:
            dict: Structured schedule containing the timeline, summary, and confidence score.
        """
        if not tasks:
            return {
                "schedule": [],
                "daily_summary": "No tasks to schedule today. Take a break!",
                "confidence_score": 100
            }

        user_prompt = PLANNING_USER_PROMPT_TEMPLATE.format(
            tasks_json=json.dumps(tasks, indent=2),
            availability_json=json.dumps(availability, indent=2)
        )
        
        logger.info("Planning Agent generating schedule for %d tasks", len(tasks))
        
        try:
            result = self.gemini.generate_structured(
                system_prompt=PLANNING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema=PLANNING_SCHEMA,
                temperature=0.2  # Low temperature for highly structured and logical scheduling
            )
            return result
        except Exception as exc:
            logger.error("Planning Agent failed to generate schedule: %s", exc)
            raise
