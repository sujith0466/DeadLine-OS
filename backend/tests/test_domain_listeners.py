import pytest
from database.db import db
from models.user import User
from models.task import Task
from models.goal import Goal
from services.runtime.event_bus import activity_started, activity_completed
import uuid
import datetime

@pytest.fixture
def app_with_db(app):
    with app.app_context():
        # Create test user
        user_id = str(uuid.uuid4())
        user = User(id=user_id, email=f"domain_{user_id}@example.com")
        db.session.add(user)
        db.session.commit()
        yield app, user

def test_task_status_updates(app_with_db):
    app, user = app_with_db
    
    with app.app_context():
        # Setup initial task
        task = Task(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title="Test Task",
            deadline=datetime.datetime.now(datetime.timezone.utc),
            status="pending"
        )
        db.session.add(task)
        db.session.commit()
        
        task_id = task.id
        
        # Simulate activity_started
        activity_started.send('test', payload={'entity_id': task_id, 'entity_type': 'TASK'})
        
        # Fetch fresh and assert
        task = db.session.get(Task, task_id)
        assert task.status == 'in_progress'
        
        # Simulate activity_completed
        activity_completed.send('test', payload={'entity_id': task_id, 'entity_type': 'TASK'})
        
        task = db.session.get(Task, task_id)
        assert task.status == 'done'

def test_goal_status_updates(app_with_db):
    app, user = app_with_db
    
    with app.app_context():
        # Setup initial goal
        goal = Goal(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title="Test Goal",
            status="Active"
        )
        db.session.add(goal)
        db.session.commit()
        
        goal_id = goal.id
        
        # Simulate activity_started
        activity_started.send('test', payload={'entity_id': goal_id, 'entity_type': 'GOAL'})
        
        # Fetch fresh and assert
        goal = db.session.get(Goal, goal_id)
        assert goal.status == 'In Progress'
        
        # Simulate activity_completed
        activity_completed.send('test', payload={'entity_id': goal_id, 'entity_type': 'GOAL'})
        
        goal = db.session.get(Goal, goal_id)
        assert goal.status == 'Completed'
