import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

def write_file(path, content):
    full_path = os.path.join(BACKEND_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created/Updated: {path}")

def patch_app_py():
    app_path = os.path.join(BACKEND_DIR, 'app.py')
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'import services.domain_listeners' not in content:
        # Import listeners at the top so they register
        # We can add it right after importing api routes
        import_stmt = "\n# Register Domain Listeners\nimport services.domain_listeners\n"
        content = content.replace("from api.runtime import runtime_bp", "from api.runtime import runtime_bp" + import_stmt)
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated app.py to import domain_listeners")


def main():
    print("--- Milestone 6: Domain Adoption ---")

    domain_listeners_code = '''import logging
from services.runtime.event_bus import activity_started, activity_completed
from models.task import Task
from models.goal import Goal
from database.db import db

logger = logging.getLogger(__name__)

@activity_started.connect
def handle_activity_started(sender, **kwargs):
    payload = kwargs.get('payload', {})
    entity_id = payload.get('entity_id')
    entity_type = payload.get('entity_type', '').upper()
    
    if not entity_id or not entity_type:
        return

    logger.info(f"DomainListener: Received activity_started for {entity_type} {entity_id}")
    
    try:
        if entity_type == 'TASK':
            task = db.session.get(Task, entity_id)
            if task and task.status != 'done':
                task.status = 'in_progress'
                db.session.add(task)
                db.session.commit()
        elif entity_type == 'GOAL':
            goal = db.session.get(Goal, entity_id)
            if goal and goal.status != 'Completed':
                goal.status = 'In Progress'
                db.session.add(goal)
                db.session.commit()
    except Exception as e:
        logger.error(f"Failed to update domain model on activity start: {e}")
        db.session.rollback()

@activity_completed.connect
def handle_activity_completed(sender, **kwargs):
    payload = kwargs.get('payload', {})
    entity_id = payload.get('entity_id')
    entity_type = payload.get('entity_type', '').upper()
    
    if not entity_id or not entity_type:
        return

    logger.info(f"DomainListener: Received activity_completed for {entity_type} {entity_id}")
    
    try:
        if entity_type == 'TASK':
            task = db.session.get(Task, entity_id)
            if task and task.status != 'done':
                task.status = 'done'
                db.session.add(task)
                db.session.commit()
        elif entity_type == 'GOAL':
            goal = db.session.get(Goal, entity_id)
            if goal and goal.status != 'Completed':
                goal.status = 'Completed'
                db.session.add(goal)
                db.session.commit()
    except Exception as e:
        logger.error(f"Failed to update domain model on activity complete: {e}")
        db.session.rollback()
'''
    write_file('services/domain_listeners.py', domain_listeners_code)

    test_domain_listeners_code = '''import pytest
from app import create_app
from database.db import db
from models.user import User
from models.task import Task
from models.goal import Goal
from services.runtime.event_bus import activity_started, activity_completed
import uuid
import datetime

@pytest.fixture
def app_with_db():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        # Create test user
        user = User(id=str(uuid.uuid4()), email="domain@example.com")
        db.session.add(user)
        db.session.commit()
        
        yield app, user
        db.session.remove()
        db.drop_all()

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
'''
    write_file('tests/test_domain_listeners.py', test_domain_listeners_code)
    
    patch_app_py()


if __name__ == "__main__":
    main()
