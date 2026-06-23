import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from services.intervention_engine import InterventionEngine

logger = logging.getLogger(__name__)
interventions_bp = Blueprint("interventions", __name__)

@interventions_bp.route("/interventions", methods=["GET"])
def get_interventions():
    """Retrieve active interventions."""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))
    return jsonify({
        "status": "success", 
        "data": InterventionEngine.get_active_interventions(page, limit)
    }), 200

@interventions_bp.route("/interventions/run", methods=["POST"])
def run_interventions():
    """Manually trigger the engine to scan for new interventions."""
    results = InterventionEngine.run_engine()
    return jsonify({
        "status": "success", 
        "message": f"Engine completed sweep. Found {len(results)} active interventions.",
        "data": results
    }), 200

@interventions_bp.route("/interventions/resolve", methods=["POST"])
def resolve_intervention():
    """Mark a specific intervention as resolved."""
    data = request.json or {}
    intervention_id = data.get("id")
    
    if not intervention_id:
        return jsonify({"status": "error", "message": "ID required"}), 400
        
    success = InterventionEngine.resolve_intervention(intervention_id)
    if success:
        return jsonify({"status": "success", "message": "Intervention resolved."}), 200
    return jsonify({"status": "error", "message": "Intervention not found."}), 404

@interventions_bp.route("/interventions/<intervention_id>/execute", methods=["POST"])
def execute_intervention(intervention_id: str):
    from models.intervention import Intervention
    from services.orchestrator import OrchestratorService
    from services.telemetry_service import TelemetryService
    from database.db import db
    import time
    
    t0 = time.time()
    
    intervention = Intervention.query.get(intervention_id)
    if not intervention:
        return jsonify({"status": "error", "message": "Intervention not found"}), 404
        
    action_type = intervention.recommended_action.get("action_type")
    target_task_id = intervention.recommended_action.get("target_task_id")
    target_task_title = intervention.recommended_action.get("target_task")
    
    # Actually perform the action
    if action_type == "calendar_reschedule":
        from models.task import Task
        task = Task.query.get(target_task_id) if target_task_id else Task.query.filter_by(title=target_task_title).first()
        if task:
            task.deadline = datetime.now(timezone.utc) + timedelta(days=1)
            db.session.commit()
            OrchestratorService.add_event("Intervention Engine", f"Rescheduled task {task.title}", "success", {"task_id": task.id})
    elif action_type == "focus_block_injection":
        OrchestratorService.add_event("Intervention Engine", "Injected Focus Block into Calendar", "success")
        # In a real system, would call CalendarService.create_event()
    elif action_type == "invoke_planning_agent":
        from agents.planning_agent import PlanningAgent
        from flask import current_app
        from models.task import Task
        gemini = current_app.extensions.get("gemini_service")
        planning = PlanningAgent(gemini)
        tasks = [t.to_dict() for t in Task.query.filter(Task.status != 'done').all()]
        planning.generate_schedule(tasks, {"daily_available_hours": 8})
        OrchestratorService.add_event("Planning Agent", "Restructured schedule per intervention", "success")
    elif action_type == "coach_challenge":
        OrchestratorService.add_event("Coach Agent", "Issued challenge to user", "success")
        
    intervention.resolved = True
    intervention.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    
    TelemetryService.log_execution("Intervention Engine", f"Execute {action_type}", "success", t0, 100)
    
    return jsonify({
        "status": "success",
        "message": "Intervention executed successfully",
        "action_type": action_type
    }), 200

@interventions_bp.route("/interventions/<intervention_id>/simulate", methods=["POST"])
def simulate_intervention(intervention_id: str):
    from models.intervention import Intervention
    from models.task import Task
    from services.availability_service import AvailabilityService
    from agents.digital_twin_agent import DigitalTwinAgent
    from flask import current_app
    from database.db import db
    from models.telemetry import TwinSimulationLog
    import time
    
    intervention = Intervention.query.get(intervention_id)
    if not intervention:
        return jsonify({"status": "error", "message": "Intervention not found"}), 404
        
    action_type = intervention.recommended_action.get("action_type")
    
    # Map action to a Twin scenario
    scenario_map = {
        "calendar_reschedule": "DELAY_TASK",
        "focus_block_injection": "INCREASE_WORKLOAD",
        "invoke_planning_agent": "EXECUTE_INTERVENTION",
        "coach_challenge": "EXECUTE_INTERVENTION"
    }
    
    scenario = {
        "action": scenario_map.get(action_type, "EXECUTE_INTERVENTION"),
        "task": intervention.recommended_action.get("target_task", "General Action"),
        "delay_days": 1
    }
    
    gemini = current_app.extensions.get("gemini_service")
    twin_agent = DigitalTwinAgent(gemini)
    
    tasks = [t.to_dict() for t in Task.query.filter(Task.status != 'done').all()]
    availability = AvailabilityService.get_current_availability()
    
    result = twin_agent.simulate_scenario(tasks, scenario, availability)
    
    # Add custom metrics for intervention
    current_risk = result.get("current_state", {}).get("risk_score", 50)
    projected_risk = result.get("projected_state", {}).get("risk_score", 50)
    if isinstance(projected_risk, str):
        projected_risk = 50 # fallback
    
    result["risk_reduction"] = max(0, current_risk - projected_risk)
    result["capacity_gain"] = result.get("capacity_impact", 0) * -1 if action_type == "calendar_reschedule" else 2
    
    # Persist the log
    log = TwinSimulationLog(
        scenario_type=scenario.get("action"),
        current_success_probability=result.get("current_state", {}).get("success_probability"),
        projected_success_probability=result.get("projected_state", {}).get("success_probability"),
        current_risk_score=current_risk,
        projected_risk_score=projected_risk,
        capacity_impact=result.get("capacity_impact"),
        schedule_stability=result.get("schedule_stability"),
        scenario_payload=scenario,
        simulation_result=result
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "data": result
    }), 200
