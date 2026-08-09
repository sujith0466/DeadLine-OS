from flask import Blueprint, request, jsonify, g
from utils.auth import require_auth
from services.runtime.state_machine import RuntimeStateMachine, RuntimeLifecycleState
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
def start_activity():
    user_id = g.user_id
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
        context = {"planned_duration_sec": planned_duration_sec}
        state = RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.RUNNING, payload=context)
        
        # Dispatch events immediately
        OutboxDispatcher.dispatch_pending_events()
        
        return jsonify({"message": "Activity started", "runtime_id": state.id}), 200
    except Exception as e:
        logger.error(f"Failed to start activity: {e}")
        return jsonify({"error": str(e)}), 500

@runtime_bp.route('/runtime/pause', methods=['POST'])
@require_auth
def pause_activity():
    user_id = g.user_id
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id:
        return jsonify({"error": "entity_id required"}), 400
        
    state = RuntimeState.query.filter_by(user_id=user_id, entity_id=entity_id).first()
    if not state:
        return jsonify({"error": "Activity not found"}), 404
        
    try:
        RuntimeStateMachine.transition(user_id, state.entity_type, entity_id, RuntimeLifecycleState.PAUSED)
        OutboxDispatcher.dispatch_pending_events()
        return jsonify({"message": "Activity paused"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@runtime_bp.route('/runtime/resume', methods=['POST'])
@require_auth
def resume_activity():
    user_id = g.user_id
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id:
        return jsonify({"error": "entity_id required"}), 400
        
    state = RuntimeState.query.filter_by(user_id=user_id, entity_id=entity_id).first()
    if not state:
        return jsonify({"error": "Activity not found"}), 404
        
    try:
        RuntimeStateMachine.transition(user_id, state.entity_type, entity_id, RuntimeLifecycleState.RUNNING)
        OutboxDispatcher.dispatch_pending_events()
        return jsonify({"message": "Activity resumed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@runtime_bp.route('/runtime/complete', methods=['POST'])
@require_auth
def complete_activity():
    user_id = g.user_id
    data = request.get_json()
    entity_id = data.get('entity_id')
    completion_source = data.get('completion_source', 'MANUAL')
    
    if not entity_id:
        return jsonify({"error": "entity_id required"}), 400
        
    state = RuntimeState.query.filter_by(user_id=user_id, entity_id=entity_id).first()
    if not state:
        return jsonify({"error": "Activity not found"}), 404
        
    try:
        target_state = getattr(RuntimeLifecycleState, f"COMPLETED_{completion_source.upper()}")
        RuntimeStateMachine.transition(user_id, state.entity_type, entity_id, target_state)
        OutboxDispatcher.dispatch_pending_events()
        return jsonify({"message": "Activity completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@runtime_bp.route('/runtime/active', methods=['GET'])
@require_auth
def get_active_activity():
    user_id = g.user_id
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
