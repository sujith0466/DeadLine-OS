"""
DeadlineOS — Goal Agent
=======================
Analyzes long-term goals and generates milestones, blockers, and forecasts.
"""

from typing import Dict, Any, List
from services.gemini_service import GeminiService
from models.goal import Goal, Habit
import json

class GoalAgent:
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def analyze_goal(self, title: str, description: str) -> Dict[str, Any]:
        """Analyzes a new or existing goal."""
        
        prompt = f"""
        You are the Goal Agent for an AI Productivity Operating System.
        Analyze the following goal:
        Title: {title}
        Description: {description}

        Generate a structured response with:
        1. goal_health (String: "Excellent", "Good", "At Risk", "Critical")
        2. completion_probability (Integer 0-100)
        3. milestones (Array of Strings: 3-5 logical checkpoints)
        4. blockers (Array of Strings: potential risks)
        5. recommendations (Array of Strings: actionable advice)
        """
        
        schema = {
            "type": "OBJECT",
            "properties": {
                "goal_health": {"type": "STRING"},
                "completion_probability": {"type": "INTEGER"},
                "milestones": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "blockers": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "recommendations": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["goal_health", "completion_probability", "milestones", "blockers", "recommendations"]
        }
        
        try:
            return self.gemini.generate_structured(prompt, f"{title} {description}", schema)
        except Exception as e:
            import logging
            logging.error(f"GoalAgent Error: {e}")
            return {
                "goal_health": "Good",
                "completion_probability": 75,
                "milestones": ["Define scope", "Begin execution", "Complete first draft"],
                "blockers": ["Time management"],
                "recommendations": ["Break down further."]
            }
