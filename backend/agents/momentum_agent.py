import logging
from models.task import Task
from models.intelligence import ExecutionProfile, WeeklyReview
from database.db import db
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MomentumAgent:
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def analyze_momentum(self) -> dict:
        """
        Analyzes the current task execution metadata to generate an ExecutionProfile.
        Returns momentum_score, burnout_risk, and consistency_score.
        """
        tasks = Task.query.all()
        
        completed = [t for t in tasks if t.status == 'done']
        pending = [t for t in tasks if t.status != 'done']
        
        overdue_count = 0
        now = datetime.now(timezone.utc)
        for t in pending:
            if t.deadline and t.deadline.tzinfo:
                if t.deadline < now:
                    overdue_count += 1
            elif t.deadline:
                if t.deadline.replace(tzinfo=timezone.utc) < now:
                    overdue_count += 1

        total = len(tasks)
        if total == 0:
            momentum = 50
            consistency = 50
            burnout = 10
        else:
            completion_rate = len(completed) / total
            momentum = min(100, int(completion_rate * 100))
            
            # Simple heuristic
            consistency = min(100, max(0, 100 - (overdue_count * 10)))
            burnout = min(100, int((len(pending) / max(1, total)) * 50))
            
        profile = ExecutionProfile.query.first()
        if not profile:
            profile = ExecutionProfile()
            db.session.add(profile)
            
        profile.momentum_score = momentum
        profile.consistency_score = consistency
        profile.burnout_risk = burnout
        db.session.commit()
        
        return profile.to_dict()

    def generate_weekly_review(self) -> dict:
        """
        Generates a qualitative weekly review using Gemini.
        """
        profile = self.analyze_momentum()
        
        # Fallback Gemini usage
        sys_prompt = "You are the DeadlineOS System Intelligence. Analyze this execution profile and provide a short 2-sentence weekly review."
        user_prompt = f"Profile: {profile}. Generate feedback."
        
        try:
            res = self.gemini.generate_structured(sys_prompt, user_prompt, {"type": "object", "properties": {"feedback": {"type": "string"}}}, temperature=0.3)
            feedback = res.get("feedback", "Keep up the good work.")
        except:
            feedback = "System operating optimally."
            
        review = WeeklyReview(
            tasks_completed=10, # mock for now
            tasks_overdue=2,
            ai_feedback=feedback
        )
        db.session.add(review)
        db.session.commit()
        
        return review.to_dict()
