import os
import re

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def write_file(path, content):
    full_path = os.path.join(BACKEND_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created/Updated: {path}")

def update_app_py():
    app_py_path = os.path.join(BACKEND_DIR, 'app.py')
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add blueprint import
    if 'from api.runtime import runtime_bp' not in content:
        content = re.sub(
            r'(from api\.settings import settings_bp)',
            r'\1\n    from api.runtime import runtime_bp',
            content
        )

    # Register blueprint
    if 'app.register_blueprint(runtime_bp, url_prefix="/api")' not in content:
        content = re.sub(
            r'(app\.register_blueprint\(settings_bp, url_prefix="/api"\)\n\s+limiter\.exempt\(settings_bp\))',
            r'\1\n\n    app.register_blueprint(runtime_bp, url_prefix="/api")\n    limiter.exempt(runtime_bp)',
            content
        )

    # Update logging
    if 'runtime' not in content:
        content = re.sub(
            r'(Blueprints registered: .*)',
            r'\1, runtime',
            content
        )

    with open(app_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated app.py with runtime_bp")

def main():
    print("--- Milestone 4: Creating Runtime REST API ---")
    
    api_code = '''from flask import Blueprint, request, jsonify
from utils.auth import require_auth
from services.runtime.state_machine import RuntimeStateMachine
from services.runtime.repository import RuntimeRepository
from services.runtime.outbox_dispatcher import OutboxDispatcher
from models.runtime_state import RuntimeState
import logging

runtime_bp = Blueprint('runtime', __name__)
logger = logging.getLogger(__name__)

def _get_active_runtime_for_user(user_id: str):
    # Retrieve the currently running or paused activity for a user
    # Normally this would be a custom query in the repository.
    # For now, we fetch all and filter, or we can use a direct query.
    states = RuntimeState.query.filter(
        RuntimeState.user_id == user_id,
        RuntimeState.status.in_(['RUNNING', 'PAUSED'])
    ).all()
    if states:
        return states[0]
    return None

@runtime_bp.route('/runtime/start', methods=['POST'])
@require_auth
def start_activity(user_id):
    data = request.get_json()
    entity_id = data.get('entity_id')
    entity_type = data.get('entity_type')
    planned_duration_sec = data.get('planned_duration_sec', 1800)
    
    if not entity_id or not entity_type:
        return jsonify({"error": "entity_id and entity_type required"}), 400
        
    # Check for existing active session
    active = _get_active_runtime_for_user(user_id)
    if active and active.entity_id != entity_id:
        return jsonify({"error": "Another activity is currently active"}), 409
        
    try:
        # Load or create state
        state = RuntimeState.query.filter_by(user_id=user_id, entity_id=entity_id).first()
        if not state:
            state = RuntimeState(
                user_id=user_id,
                entity_id=entity_id,
                entity_type=entity_type,
                status='CREATED'
            )
            RuntimeRepository.save(state, None, [])
            
        machine = RuntimeStateMachine(state.id)
        context = {"planned_duration_sec": planned_duration_sec}
        machine.transition_to('RUNNING', context=context)
        
        # Dispatch events immediately
        OutboxDispatcher.dispatch_pending_events()
        
        return jsonify({"message": "Activity started", "runtime_id": state.id}), 200
    except Exception as e:
        logger.error(f"Failed to start activity: {e}")
        return jsonify({"error": str(e)}), 500

@runtime_bp.route('/runtime/pause', methods=['POST'])
@require_auth
def pause_activity(user_id):
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id:
        return jsonify({"error": "entity_id required"}), 400
        
    state = RuntimeState.query.filter_by(user_id=user_id, entity_id=entity_id).first()
    if not state:
        return jsonify({"error": "Activity not found"}), 404
        
    try:
        machine = RuntimeStateMachine(state.id)
        machine.transition_to('PAUSED')
        OutboxDispatcher.dispatch_pending_events()
        return jsonify({"message": "Activity paused"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@runtime_bp.route('/runtime/resume', methods=['POST'])
@require_auth
def resume_activity(user_id):
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id:
        return jsonify({"error": "entity_id required"}), 400
        
    state = RuntimeState.query.filter_by(user_id=user_id, entity_id=entity_id).first()
    if not state:
        return jsonify({"error": "Activity not found"}), 404
        
    try:
        machine = RuntimeStateMachine(state.id)
        machine.transition_to('RUNNING')
        OutboxDispatcher.dispatch_pending_events()
        return jsonify({"message": "Activity resumed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@runtime_bp.route('/runtime/complete', methods=['POST'])
@require_auth
def complete_activity(user_id):
    data = request.get_json()
    entity_id = data.get('entity_id')
    completion_source = data.get('completion_source', 'MANUAL')
    
    if not entity_id:
        return jsonify({"error": "entity_id required"}), 400
        
    state = RuntimeState.query.filter_by(user_id=user_id, entity_id=entity_id).first()
    if not state:
        return jsonify({"error": "Activity not found"}), 404
        
    try:
        machine = RuntimeStateMachine(state.id)
        target_state = f"COMPLETED_{completion_source.upper()}"
        machine.transition_to(target_state)
        OutboxDispatcher.dispatch_pending_events()
        return jsonify({"message": "Activity completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@runtime_bp.route('/runtime/active', methods=['GET'])
@require_auth
def get_active_activity(user_id):
    state = _get_active_runtime_for_user(user_id)
    if not state:
        return jsonify({"active": False}), 200
        
    return jsonify({
        "active": True,
        "runtime_id": state.id,
        "entity_id": state.entity_id,
        "entity_type": state.entity_type,
        "status": state.status
    }), 200
'''
    write_file('api/runtime.py', api_code)

    test_code = '''import pytest
from app import create_app
from database.db import db
from models.user import User
import uuid

@pytest.fixture
def test_client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test user
            user = User(id=str(uuid.uuid4()), email="test@example.com", auth_provider="local", auth_id="123")
            db.session.add(user)
            db.session.commit()
            
            yield client, user.id
            db.session.remove()
            db.drop_all()

def test_runtime_api_flow(test_client):
    client, user_id = test_client
    
    headers = {"Authorization": f"Bearer {user_id}"}
    
    # 1. Check active (should be None)
    res = client.get('/api/runtime/active', headers=headers)
    assert res.status_code == 200
    assert res.json['active'] is False
    
    # 2. Start
    res = client.post('/api/runtime/start', json={
        "entity_id": "task-123",
        "entity_type": "TASK"
    }, headers=headers)
    assert res.status_code == 200
    assert "runtime_id" in res.json
    
    # 3. Check active
    res = client.get('/api/runtime/active', headers=headers)
    assert res.status_code == 200
    assert res.json['active'] is True
    assert res.json['status'] == 'RUNNING'
    
    # 4. Pause
    res = client.post('/api/runtime/pause', json={
        "entity_id": "task-123"
    }, headers=headers)
    assert res.status_code == 200
    
    # 5. Resume
    res = client.post('/api/runtime/resume', json={
        "entity_id": "task-123"
    }, headers=headers)
    assert res.status_code == 200
    
    # 6. Complete
    res = client.post('/api/runtime/complete', json={
        "entity_id": "task-123"
    }, headers=headers)
    assert res.status_code == 200
    
    # 7. Check active (should be None again)
    res = client.get('/api/runtime/active', headers=headers)
    assert res.status_code == 200
    assert res.json['active'] is False
'''
    write_file('tests/test_runtime_api.py', test_code)
    
    update_app_py()

    print("Runtime REST API logic generated.")

if __name__ == "__main__":
    main()
