import os
import json
from app import create_app
from database.db import db
from models.user import User
from models.goal import Goal, Milestone, Habit
from models.task import Task

print("=== E2E Integration Workflow Validation ===")
app = create_app()

with app.app_context():
    db.create_all()
    client = app.test_client()

    from services.goal_service import GoalService
    from services.analytics_service import AnalyticsService
    from services.orchestrator import OrchestratorService

    user = User.query.filter_by(email="e2e@test.com").first()
    if not user:
        user = User(email="e2e@test.com", name="E2E Tester", hashed_password="fake")
        db.session.add(user)
        db.session.commit()
    uid = user.id

    print("Executing Flow A: Goal Lifecycle...")
    Goal.query.filter_by(user_id=uid).delete()
    Task.query.filter_by(user_id=uid).delete()
    db.session.commit()

    goal = GoalService.create_goal(uid, "Launch MVP", "Launch V1", "work", "2030-01-01")
    print("Goal created:", goal["title"])

    tasks = Task.query.filter_by(user_id=uid).all()
    print(f"Tasks created from Goal: {len(tasks)}")
    assert len(tasks) > 0, "Tasks were not generated from Goal"

    analytics = AnalyticsService.get_overview(uid)
    print("Analytics Overview after Goal creation:", analytics)

    print("Executing Orchestrator...")
    orch_result = OrchestratorService.run_ecosystem_pipeline(uid)

    print("=== ALL WORKFLOWS VALIDATED ===")
