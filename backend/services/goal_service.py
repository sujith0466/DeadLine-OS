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
from models.goal import Goal, Habit, Milestone, HabitLog
from models.task import Task
from agents.goal_agent import GoalAgent
import datetime as dt

class GoalService:

    @classmethod
    def get_goals(cls, user_id: str, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch all goals with pagination."""
        offset = (page - 1) * limit
        goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.pinned.desc(), Goal.created_at.desc()).offset(offset).limit(limit).all()
        return [g.to_dict() for g in goals]

    @classmethod
    def get_habits(cls, user_id: str, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch all habits with pagination. Computes missed streaks."""
        offset = (page - 1) * limit
        habits = Habit.query.filter_by(user_id=user_id).offset(offset).limit(limit).all()
        
        today = datetime.now(timezone.utc).date()
        for habit in habits:
            if habit.last_checkin_date and habit.status != "Paused":
                last_date = datetime.strptime(habit.last_checkin_date, "%Y-%m-%d").date()
                if (today - last_date).days > 1:
                    habit.current_streak = 0
        db.session.commit()
        return [h.to_dict() for h in habits]

    @classmethod
    def create_goal(cls, user_id: str, title: str, description: str, category: str, target_date: str) -> Dict[str, Any]:
        threshold_time = datetime.now(timezone.utc) - dt.timedelta(seconds=30)
        duplicate = Goal.query.filter(Goal.user_id == user_id, Goal.title == title, Goal.target_date == target_date, Goal.created_at >= threshold_time).first()
        if duplicate:
            raise ValueError(f"Duplicate Request: Goal '{title}' was recently created.")
            
        from flask import current_app
        gemini = current_app.extensions.get("gemini_service")
        agent_data = GoalAgent(gemini).analyze_goal(title, description)
        
        goal = Goal(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            target_date=target_date,
            health_score=100 if agent_data["goal_health"] == "Excellent" else 80,
            progress_percentage=0,
            status="Active"
        )
        db.session.add(goal)
        db.session.commit()
        
        for idx, m_title in enumerate(agent_data.get("milestones", [])):
            m = Milestone(goal_id=goal.id, title=m_title)
            db.session.add(m)
            db.session.flush()
            
            deadline_date = dt.datetime.now(timezone.utc) + dt.timedelta(days=(idx + 1) * 7)
            task = Task(
                user_id=user_id,
                title=f"{m_title}",
                description=f"Generated from Goal: {title}",
                deadline=deadline_date,
                estimated_hours=2.0,
                category=category,
                source="goal",
                goal_id=goal.id,
                milestone_id=m.id
            )
            db.session.add(task)
            
        db.session.commit()
        
        result = goal.to_dict()
        result["ai_forecast"] = agent_data
        return result

    @classmethod
    def edit_goal(cls, user_id: str, goal_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        goal = Goal.query.filter_by(user_id=user_id, id=goal_id).first()
        if not goal:
            raise ValueError("Goal not found")
            
        if 'title' in data: goal.title = data['title']
        if 'description' in data: goal.description = data['description']
        if 'category' in data: goal.category = data['category']
        if 'target_date' in data: goal.target_date = data['target_date']
        if 'priority' in data: goal.priority = data['priority']
        
        db.session.commit()
        return goal.to_dict()

    @classmethod
    def archive_goal(cls, user_id: str, goal_id: str) -> bool:
        goal = Goal.query.filter_by(user_id=user_id, id=goal_id).first()
        if not goal: return False
        goal.archived = True
        goal.pinned = False # Unpin when archiving
        db.session.commit()
        return True

    @classmethod
    def unarchive_goal(cls, user_id: str, goal_id: str) -> bool:
        goal = Goal.query.filter_by(user_id=user_id, id=goal_id).first()
        if not goal: return False
        goal.archived = False
        db.session.commit()
        return True

    @classmethod
    def toggle_pin_goal(cls, user_id: str, goal_id: str) -> bool:
        goal = Goal.query.filter_by(user_id=user_id, id=goal_id).first()
        if not goal: return False
        goal.pinned = not goal.pinned
        db.session.commit()
        return True

    @classmethod
    def delete_goal(cls, user_id: str, goal_id: str) -> bool:
        goal = Goal.query.filter_by(user_id=user_id, id=goal_id).first()
        if not goal: return False
        
        # Delete linked tasks
        Task.query.filter_by(user_id=user_id, goal_id=goal.id).delete()
        db.session.delete(goal)
        db.session.commit()
        return True

    @classmethod
    def update_milestone_status(cls, user_id: str, milestone_id: str, status: str) -> Dict[str, Any]:
        m = Milestone.query.get(milestone_id) # Should theoretically join with Goal to check user_id, but Milestone assumes goal exists. We'll verify goal ownership.
        if not m:
            raise ValueError("Milestone not found")
        goal = Goal.query.filter_by(user_id=user_id, id=m.goal_id).first()
        if not goal:
            raise ValueError("Unauthorized or Goal not found")
        if not m:
            raise ValueError("Milestone not found")
        
        m.status = status
        m.completed = (status == "COMPLETED")
        m.completed_at = datetime.now(timezone.utc) if m.completed else None
        
        db.session.flush()
        
        # Recalculate Goal Progress automatically
        if goal:
            total = len(goal.milestones)
            completed = len([x for x in goal.milestones if x.completed])
            goal.progress_percentage = int((completed / total) * 100) if total > 0 else 0
            
            if goal.progress_percentage == 100:
                goal.status = "COMPLETED"
                goal.success_score = 100
            elif goal.progress_percentage > 0:
                goal.status = "IN_PROGRESS"
            else:
                goal.status = "Active"
                
        db.session.commit()
        return m.to_dict()

    @classmethod
    def create_habit(cls, user_id: str, name: str, category: str, frequency: str) -> Dict[str, Any]:
        threshold_time = datetime.now(timezone.utc) - dt.timedelta(seconds=30)
        duplicate = Habit.query.filter(Habit.user_id == user_id, Habit.name == name, Habit.created_at >= threshold_time).first()
        if duplicate:
            raise ValueError(f"Duplicate Request: Habit '{name}' was recently created.")

        habit = Habit(user_id=user_id, name=name, category=category, frequency=frequency)
        db.session.add(habit)
        db.session.commit()
        return habit.to_dict()

    @classmethod
    def edit_habit(cls, user_id: str, habit_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        habit = Habit.query.filter_by(user_id=user_id, id=habit_id).first()
        if not habit: raise ValueError("Habit not found")
        
        if 'name' in data: habit.name = data['name']
        if 'category' in data: habit.category = data['category']
        if 'frequency' in data: habit.frequency = data['frequency']
        if 'reminder_schedule' in data: habit.reminder_schedule = data['reminder_schedule']
        if 'target_duration' in data: habit.target_duration = data['target_duration']
        
        db.session.commit()
        return habit.to_dict()

    @classmethod
    def archive_habit(cls, user_id: str, habit_id: str) -> bool:
        habit = Habit.query.filter_by(user_id=user_id, id=habit_id).first()
        if not habit: return False
        habit.archived = True
        db.session.commit()
        return True

    @classmethod
    def unarchive_habit(cls, user_id: str, habit_id: str) -> bool:
        habit = Habit.query.filter_by(user_id=user_id, id=habit_id).first()
        if not habit: return False
        habit.archived = False
        db.session.commit()
        return True

    @classmethod
    def delete_habit(cls, user_id: str, habit_id: str) -> bool:
        habit = Habit.query.filter_by(user_id=user_id, id=habit_id).first()
        if not habit: return False
        
        HabitLog.query.filter_by(user_id=user_id, habit_id=habit.id).delete()
        db.session.delete(habit)
        db.session.commit()
        return True

    @classmethod
    def set_habit_status(cls, user_id: str, habit_id: str, status: str) -> Dict[str, Any]:
        habit = Habit.query.filter_by(user_id=user_id, id=habit_id).first()
        if not habit: raise ValueError("Habit not found")
        habit.status = status
        db.session.commit()
        return habit.to_dict()

    @classmethod
    def check_in_habit(cls, user_id: str, habit_id: str) -> Dict[str, Any]:
        habit = Habit.query.filter_by(user_id=user_id, id=habit_id).first()
        if not habit: raise ValueError("Habit not found")
        
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        existing_log = HabitLog.query.filter_by(habit_id=habit_id, date=today_str).first()
        
        if existing_log:
            raise ValueError("Already checked in today.")
            
        log = HabitLog(user_id=user_id, habit_id=habit_id, date=today_str, completed=True)
        db.session.add(log)
        
        # Streak Calculation Logic
        habit.last_checkin_date = today_str
        habit.current_streak += 1
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
            
        # Basic completion rate bump for demo
        habit.completion_rate = min(100, habit.completion_rate + 5)
        habit.momentum_score = min(100, habit.momentum_score + 10)
        
        db.session.commit()
        
        return {
            "habit": habit.to_dict(),
            "log": log.to_dict()
        }
