import json
import uuid
import sys
import os
from datetime import datetime, timezone, timedelta

# Ensure we can import the backend app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from database.db import db
from models.goal import Goal, Milestone
from models.user import User

app = create_app()

def run_test():
    with app.app_context():
        # Create a dummy user for the test if it doesn't exist
        test_user_id = str(uuid.uuid4())
        user = User(id=test_user_id, email=f"test_{test_user_id}@example.com")
        db.session.add(user)
        db.session.commit()
        
        from services.goal_service import GoalService
        
        print("Testing GoalService.create_goal directly...")
        try:
            target_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            
            result = GoalService.create_goal(
                user_id=test_user_id,
                title="Conquer the Hackathon",
                description="Win the competition by building an amazing product.",
                category="Career",
                target_date=target_date
            )
            print("Goal created successfully!")
            
            # The result is a dictionary representation of the goal
            goal_id = result.get('id')
            
            milestones = Milestone.query.filter_by(goal_id=goal_id).all()
            print(f"Found {len(milestones)} milestones in database.")
            for m in milestones:
                print(f" - Milestone: {m.title}, User: {m.user_id}")
                assert m.user_id == test_user_id, "Milestone user_id does not match!"
                
            print("\nSUCCESS: All entities created correctly without null user_ids.")
            
        except Exception as e:
            print(f"\nERROR OCCURRED: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
