"""
DeadlineOS — Priority Agent
=============================
Analyzes tasks using Gemini to determine urgency, importance, 
estimated effort, risk of delay, and a priority score.
"""

import datetime
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

PRIORITY_SYSTEM_PROMPT = """You are the Priority Agent in DeadlineOS, an AI Chief-of-Staff system.
Analyze the given task and return a precise priority assessment as structured JSON.
Consider: Eisenhower Matrix (urgency × importance), deadline proximity, effort required, and downstream dependencies.
Always reason step-by-step before outputting the final JSON."""

PRIORITY_USER_PROMPT_TEMPLATE = """
Task: {title}
Description: {description}
Deadline: {deadline} (current time: {now})
Estimated Hours: {estimated_hours}
Current workload: {active_tasks_count} tasks pending

Return this EXACT JSON structure:
{{
  "priority_score": <0-100 integer>,
  "urgency": "<High|Medium|Low>",
  "importance": "<High|Medium|Low>",
  "estimated_hours": <number>,
  "risk_level": "<High|Medium|Low>",
  "reasoning": "<1-2 sentence explanation>"
}}
"""

PRIORITY_SCHEMA = {
    "type": "object",
    "properties": {
        "priority_score": {"type": "integer", "description": "0-100 score based on urgency and importance"},
        "urgency": {"type": "string", "enum": ["High", "Medium", "Low"]},
        "importance": {"type": "string", "enum": ["High", "Medium", "Low"]},
        "estimated_hours": {"type": "number", "description": "Estimated hours to complete"},
        "risk_level": {"type": "string", "enum": ["High", "Medium", "Low"]},
        "reasoning": {"type": "string", "description": "Brief reasoning for the priority score"}
    },
    "required": ["priority_score", "urgency", "importance", "estimated_hours", "risk_level", "reasoning"]
}

class PriorityAgent:
    """Agent responsible for analyzing tasks and calculating priority metrics."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def analyze_task(self, task_data: Dict[str, Any], active_tasks_count: int = 0) -> Dict[str, Any]:
        """
        Analyzes task urgency, importance, risk, and priority score.
        
        Args:
            task_data: dict containing title, description, deadline, estimated_hours
            active_tasks_count: current number of pending tasks for context
            
        Returns:
            dict: Structured priority analysis
        """
        title = task_data.get("title", "Untitled Task")
        description = task_data.get("description", "No description provided")
        deadline = task_data.get("deadline", "No deadline")
        estimated_hours = task_data.get("estimated_hours", 1.0)
        
        # Get current time in ISO format to calculate deadline proximity
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        user_prompt = PRIORITY_USER_PROMPT_TEMPLATE.format(
            title=title,
            description=description,
            deadline=deadline,
            now=now,
            estimated_hours=estimated_hours,
            active_tasks_count=active_tasks_count
        )
        
        logger.info("Priority Agent analyzing task: %s (Deadline: %s)", title, deadline)
        
        try:
            result = self.gemini.generate_structured(
                system_prompt=PRIORITY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema=PRIORITY_SCHEMA,
                temperature=0.2  # Low temperature for analytical consistency
            )
            return result
        except Exception as exc:
            logger.error("Priority Agent failed to analyze task %r: %s", title, exc)
            raise
