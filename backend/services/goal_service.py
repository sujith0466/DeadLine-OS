"""
DeadlineOS — Goal Service
=========================
Manages DB interactions for Goals, Habits, and Milestones.
Generates Demo Mode data if DB is empty.
"""

import os
from typing import Dict, Any, List
from datetime import datetime, timezone
from database.db import db
from models.goal import Goal, Habit, Milestone
from agents.goal_agent import GoalAgent

class GoalService:

    @classmethod
    def get_goals(cls, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch all goals with pagination."""
        offset = (page - 1) * limit
        return [g.to_dict() for g in Goal.query.offset(offset).limit(limit).all()]

    @classmethod
    def get_habits(cls, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch all habits with pagination."""
        offset = (page - 1) * limit
        return [h.to_dict() for h in Habit.query.offset(offset).limit(limit).all()]

    @classmethod
    def create_goal(cls, title: str, description: str, category: str, target_date: str) -> Dict[str, Any]:
        """Creates a goal and runs the GoalAgent to generate milestones."""
        from flask import current_app
        gemini = current_app.extensions.get("gemini_service")
        agent_data = GoalAgent(gemini).analyze_goal(title, description)
        
        goal = Goal(
            title=title,
            description=description,
            category=category,
            target_date=target_date,
            health_score=100 if agent_data["goal_health"] == "Excellent" else 80,
            progress_percentage=0
        )
        db.session.add(goal)
        db.session.commit()
        
        # Add generated milestones
        for m_title in agent_data.get("milestones", []):
            m = Milestone(goal_id=goal.id, title=m_title)
            db.session.add(m)
        db.session.commit()
        
        result = goal.to_dict()
        result["ai_forecast"] = agent_data
        return result

    @classmethod
    def create_habit(cls, name: str, category: str, frequency: str) -> Dict[str, Any]:
        habit = Habit(name=name, category=category, frequency=frequency)
        db.session.add(habit)
        db.session.commit()
        return habit.to_dict()


