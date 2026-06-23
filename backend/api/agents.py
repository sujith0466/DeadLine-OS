"""
DeadlineOS — Agents Blueprint (Stub)
=======================================
Placeholder routes for all six DeadlineOS agents.

Each route is fully wired and returns a structured stub response so
the frontend can be developed in parallel before the real agent logic
is implemented in Phase 3.

Routes
------
POST /api/agents/prioritize          →  Priority Agent
POST /api/agents/plan                →  Planning Agent
POST /api/agents/rescue/<task_id>    →  Rescue Agent
POST /api/agents/accountability      →  Accountability Agent
POST /api/agents/coach               →  Coach Agent
POST /api/agents/twin/simulate       →  Digital Twin Agent
GET  /api/agents/status              →  Running agent status overview
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app

from agents.priority_agent import PriorityAgent
from agents.planning_agent import PlanningAgent
from agents.rescue_agent import RescueAgent
from agents.digital_twin_agent import DigitalTwinAgent
from agents.vision_agent import VisionAgent
from agents.accountability_agent import AccountabilityAgent
from agents.coach_agent import CoachAgent
from agents.reflection_agent import ReflectionAgent
from models.task import Task
import time
from services.telemetry_service import TelemetryService

logger = logging.getLogger(__name__)

agents_bp = Blueprint("agents", __name__)

# ── Status tracker (in-memory, per-process) ───────────────────────────────────
# In production this would be stored in Redis or the DB.
_agent_status: dict = {
    "priority": {"state": "idle", "last_run": None},
    "planning": {"state": "idle", "last_run": None},
    "rescue": {"state": "idle", "last_run": None},
    "accountability": {"state": "idle", "last_run": None},
    "coach": {"state": "idle", "last_run": None},
    "twin": {"state": "idle", "last_run": None},
    "vision": {"state": "idle", "last_run": None},
    "reflection": {"state": "idle", "last_run": None},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_agent_state(agent: str, state: str) -> None:
    _agent_status[agent]["state"] = state
    if state == "done":
        _agent_status[agent]["last_run"] = _now_iso()


# ── Routes ────────────────────────────────────────────────────────────────────

@agents_bp.route("/agents/status", methods=["GET"])
def agent_status():
    """
    Return the current state of all agents using hybrid logic:
    Registered Agents + Recent Activity.
    """
    from services.orchestrator import OrchestratorService
    
    # 12 official agents registered in the system
    registered_agents = [
        "vision", "priority", "planning", "accountability", 
        "coach", "rescue", "twin", "reflection", 
        "goal", "document", "voice", "intervention"
    ]
    
    feed = OrchestratorService.get_feed()
    recent_events = feed[:50]  # Check last 50 events for activity
    
    recently_active = set()
    for ev in recent_events:
        agent_name = ev.get("agent", "").lower()
        for ra in registered_agents:
            if ra in agent_name:
                recently_active.add(ra)
                break
                
    # Check states from memory
    running_agents = [k for k, v in _agent_status.items() if v["state"] == "running"]
    
    online_agents = len(registered_agents)
    active_agents = len(set(running_agents).union(recently_active))
    
    # Ensure at least 1 active agent for demo purposes if empty
    if active_agents == 0:
        active_agents = 1
        recently_active.add("intervention")

    return jsonify({
        "status": "success",
        "data": {
            "online_agents": online_agents,
            "active_agents": active_agents,
            "recently_active": list(recently_active),
            "states": _agent_status
        }
    }), 200


@agents_bp.route("/agents/prioritize", methods=["POST"])
def run_priority_agent():
    """
    Trigger the Priority Agent for one or more tasks.

    Request Body (JSON)
    -------------------
    {
        "task_ids": ["<uuid>", ...]    optional — defaults to all pending tasks
    }

    Response 200 (stub)
    -------------------
    {
        "agent": "priority",
        "status": "queued",
        "message": "Priority Agent will be implemented in Phase 3."
    }
    """
    data = request.get_json(silent=True) or {}
    gemini = current_app.extensions.get("gemini_service")
    if not gemini:
        return jsonify({"error": "GeminiService not available"}), 503

    priority_agent = PriorityAgent(gemini)
    active_tasks_count = Task.query.filter(Task.status != "done").count()

    # Handle direct ad-hoc task input (e.g. from frontend form or test)
    if "title" in data and "deadline" in data:
        try:
            _set_agent_state("priority", "running")
            logger.info("Priority Agent triggered for direct input: %s", data["title"])
            result = priority_agent.analyze_task(data, active_tasks_count)
            _set_agent_state("priority", "done")
            return jsonify(result), 200
        except Exception as e:
            _set_agent_state("priority", "error")
            logger.error("Priority Agent error on direct input: %s", e)
            return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503

    # Handle batch processing by task_ids
    task_ids = data.get("task_ids", [])
    logger.info("Priority Agent triggered | task_ids=%s", task_ids or "all")
    _set_agent_state("priority", "running")

    if not task_ids:
        tasks = Task.query.filter(Task.status != "done").all()
    else:
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()

    results = []
    for task in tasks:
        task_data = {
            "title": task.title,
            "description": task.description or "",
            "deadline": task.deadline.isoformat() if task.deadline else "None",
            "estimated_hours": task.estimated_hours or 1.0
        }
        try:
            analysis = priority_agent.analyze_task(task_data, active_tasks_count)
            results.append({
                "task_id": task.id,
                "analysis": analysis
            })
        except Exception as e:
            logger.error("Failed to prioritize task %s: %s", task.id, e)
            results.append({
                "task_id": task.id,
                "error": str(e)
            })

    _set_agent_state("priority", "done")
    return jsonify({
        "agent": "priority",
        "status": "success",
        "results": results,
        "timestamp": _now_iso(),
    }), 200


@agents_bp.route("/agents/plan", methods=["POST"])
def run_planning_agent():
    """
    Trigger the Planning Agent to generate a daily schedule.

    Request Body (JSON)
    -------------------
    {
        "date": "<YYYY-MM-DD>"    optional — defaults to today
    }

    Response 202 (stub)
    -------------------
    {
        "agent": "planning",
        "status": "queued",
        "date": "<YYYY-MM-DD>",
        "message": "Planning Agent will be implemented in Phase 3."
    }
    """
    data = request.get_json(silent=True) or {}
    gemini = current_app.extensions.get("gemini_service")
    if not gemini:
        return jsonify({"error": "GeminiService not available"}), 503

    planning_agent = PlanningAgent(gemini)

    # Allow direct input mapping to spec for explicit testing
    tasks = data.get("tasks", [])
    availability = data.get("availability", {})

    # If not provided, fallback to default behavior (e.g. today's pending tasks)
    if not tasks:
        # DB fetch fallback logic here if needed
        pass
    if not availability:
        availability = {
            "daily_available_hours": 8,
            "preferred_work_hours": {"start": "09:00", "end": "17:00"}
        }

    try:
        t0 = time.time()
        _set_agent_state("planning", "running")
        logger.info("Planning Agent triggered with %d tasks", len(tasks))
        result = planning_agent.generate_plan(tasks, availability)
        TelemetryService.log_execution("Planning Agent", "Generate Plan", "success", t0, 85)
        _set_agent_state("planning", "done")
        
        return jsonify({
            "agent": "planning",
            "status": "success",
            "data": result,
            "timestamp": _now_iso(),
        }), 200
    except Exception as e:
        _set_agent_state("planning", "error")
        logger.error("Planning Agent error: %s", e)
        return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503


@agents_bp.route("/agents/rescue", methods=["POST"])
def run_rescue_agent_general():
    """
    Trigger Rescue Mode for a set of tasks based on a JSON payload.

    Request Body (JSON)
    -------------------
    {
        "tasks": [{...}],
        "availability": {...}
    }

    Response 200
    ------------
    {
        "agent": "rescue",
        ...
    }
    """
    data = request.get_json(silent=True) or {}
    gemini = current_app.extensions.get("gemini_service")
    if not gemini:
        return jsonify({"error": "GeminiService not available"}), 503

    rescue_agent = RescueAgent(gemini)

    tasks = data.get("tasks", [])
    availability = data.get("availability", {})

    if not tasks:
        # Fallback to DB fetch for demo purposes if needed
        pass
    if not availability:
        availability = {"daily_available_hours": 3}

    try:
        t0 = time.time()
        _set_agent_state("rescue", "running")
        logger.warning("🚨 Rescue Agent triggered for %d tasks", len(tasks))
        result = rescue_agent.generate_recovery_plan(tasks, availability)
        TelemetryService.log_execution("Rescue Agent", "Recovery Plan", "success", t0, 92)
        _set_agent_state("rescue", "done")
        
        return jsonify({
            "agent": "rescue",
            "status": "success",
            "data": result,
            "timestamp": _now_iso(),
        }), 200
    except Exception as e:
        _set_agent_state("rescue", "error")
        logger.error("Rescue Agent error: %s", e)
        return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503


@agents_bp.route("/agents/rescue/<task_id>", methods=["POST"])
def run_rescue_agent_by_id(task_id: str):
    """
    Trigger Rescue Mode for a specific at-risk task.
    """
    logger.warning("🚨 Rescue Agent triggered | task_id=%s", task_id)
    _set_agent_state("rescue", "queued")

    return jsonify(
        {
            "agent": "rescue",
            "status": "queued",
            "task_id": task_id,
            "message": "Rescue Agent by ID will use DB logic.",
            "timestamp": _now_iso(),
        }
    ), 202


@agents_bp.route("/agents/digital-twin", methods=["POST"])
def run_digital_twin():
    """
    Trigger the Digital Twin Agent to simulate future workload outcomes
    based on what-if scenarios. Uses real DB state, not frontend mocks.
    """
    data = request.get_json(silent=True) or {}
    gemini = current_app.extensions.get("gemini_service")
    if not gemini:
        return jsonify({"error": "GeminiService not available"}), 503

    from services.availability_service import AvailabilityService
    from models.task import Task
    from models.telemetry import TwinSimulationLog
    from database.db import db
    import json

    twin_agent = DigitalTwinAgent(gemini)

    # 1. Fetch Real Context
    tasks = [t.to_dict() for t in Task.query.filter(Task.status != 'done').all()]
    availability = AvailabilityService.get_current_availability()
    scenario = data.get("scenario", {})

    if not scenario:
        return jsonify({"error": "No scenario provided"}), 400

    try:
        t0 = time.time()
        _set_agent_state("twin", "running")
        logger.info("Twin Agent simulating scenario '%s' with %d real tasks", scenario.get("action"), len(tasks))
        
        # 2. Simulate
        result = twin_agent.simulate_scenario(tasks, scenario, availability)
        
        TelemetryService.log_execution("Digital Twin Agent", "Simulation", "success", t0, 90)
        
        # 3. Persist Log
        log = TwinSimulationLog(
            scenario_type=scenario.get("action"),
            current_success_probability=result.get("current_state", {}).get("success_probability"),
            projected_success_probability=result.get("success_probability"),
            current_risk_score=result.get("current_state", {}).get("risk_score"),
            projected_risk_score=result.get("projected_state", {}).get("risk_level") == 'Critical' and 90 or 50, # fallback parsing if needed
            capacity_impact=result.get("capacity_impact"),
            schedule_stability=result.get("schedule_stability"),
            scenario_payload=scenario,
            simulation_result=result
        )
        db.session.add(log)
        db.session.commit()

        _set_agent_state("twin", "done")
        
        return jsonify({
            "agent": "twin",
            "status": "success",
            "data": result,
            "timestamp": _now_iso(),
        }), 200
    except Exception as e:
        _set_agent_state("twin", "error")
        logger.error("Twin Agent error: %s", e)
        return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503


@agents_bp.route("/agents/vision", methods=["POST"])
def run_vision_agent():
    """
    Trigger the Vision Agent to extract tasks from an uploaded image.

    Request (multipart/form-data)
    -----------------------------
    image : The image file (jpg, jpeg, png, webp).

    Response 200
    ------------
    {
        "agent": "vision",
        ...
    }
    """
    gemini = current_app.extensions.get("gemini_service")
    if not gemini:
        return jsonify({"error": "GeminiService not available"}), 503

    if "image" not in request.files:
        return jsonify({"error": "No image file provided in the request"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    mime_type = file.mimetype
    allowed_mimes = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if mime_type not in allowed_mimes:
        return jsonify({"error": f"Unsupported file type: {mime_type}. Allowed: {', '.join(allowed_mimes)}"}), 400

    try:
        t0 = time.time()
        image_bytes = file.read()
        vision_agent = VisionAgent(gemini)

        _set_agent_state("vision", "running")
        logger.info("Vision Agent triggered for image upload (%s)", mime_type)
        
        result = vision_agent.extract_tasks_from_image(image_bytes, mime_type)
        
        TelemetryService.log_execution("Vision Agent", "Image Upload Extraction", "success", t0, 95)
        
        # PERSISTENCE
        from models.task import Task
        from database.db import db
        from services.orchestrator import OrchestratorService
        from datetime import datetime, timezone, timedelta
        
        inserted_tasks = []
        extracted_tasks = result.get("tasks", [])
        
        # 1. Gather all titles to pre-fetch duplicates
        titles = [t_data.get("title", "Vision Extracted Task") for t_data in extracted_tasks]
        existing_tasks_records = Task.query.filter(Task.title.in_(titles)).all()
        existing_titles = {t.title for t in existing_tasks_records}

        for t_data in extracted_tasks:
            task_title = t_data.get("title", "Vision Extracted Task")
            # Duplicate check using pre-fetched set
            if task_title in existing_titles:
                continue
                
            try:
                dt_str = t_data.get("deadline")
                deadline = datetime.fromisoformat(dt_str) if dt_str and dt_str != "None" else datetime.now(timezone.utc) + timedelta(days=1)
            except:
                deadline = datetime.now(timezone.utc) + timedelta(days=1)
                
            priority = t_data.get("priority", "Medium")
            
            t = Task(
                title=task_title,
                deadline=deadline,
                description=f"Priority: {priority} (Extracted by Vision Agent)",
                source="vision",
                status="pending",
                ai_confidence=95 # Default vision extraction confidence
            )
            inserted_tasks.append(t)
            
        if inserted_tasks:
            db.session.add_all(inserted_tasks)
            
        db.session.commit()
        result["inserted_task_ids"] = [t.id for t in inserted_tasks]
        
        OrchestratorService.add_event("Vision Agent", "Extracted and saved tasks", "success", {"count": len(inserted_tasks)})

        _set_agent_state("vision", "done")
        
        return jsonify({
            "agent": "vision",
            "status": "success",
            "data": result,
            "timestamp": _now_iso(),
        }), 200
    except Exception as e:
        logger.error("Vision Agent failed: %s", e, exc_info=True)
        _set_agent_state("vision", "idle")
        return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503


@agents_bp.route("/agents/accountability", methods=["POST"])
def run_accountability():
    """Trigger the Accountability Agent."""
    _set_agent_state("accountability", "running")
    gemini = current_app.extensions.get("gemini_service")
    try:
        t0 = time.time()
        data = request.json or {}
        agent = AccountabilityAgent(gemini)
        result = agent.generate_metrics(
            data.get("active_tasks", []),
            data.get("completed_tasks", []),
            data.get("overdue_tasks", [])
        )
        TelemetryService.log_execution("Accountability Agent", "Generate Metrics", "success", t0, 80)
        return jsonify({"agent": "accountability", "status": "success", "data": result}), 200
    except Exception as e:
        logger.error("Accountability Agent failed: %s", e)
        return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503
    finally:
        _set_agent_state("accountability", "idle")


@agents_bp.route("/agents/coach", methods=["POST"])
def run_coach():
    """Trigger the Coach Agent."""
    _set_agent_state("coach", "running")
    gemini = current_app.extensions.get("gemini_service")
    try:
        t0 = time.time()
        data = request.json or {}
        agent = CoachAgent(gemini)
        result = agent.generate_coaching(
            data.get("active_tasks", []),
            data.get("metrics", {})
        )
        TelemetryService.log_execution("Coach Agent", "Generate Coaching", "success", t0, 88)
        return jsonify({"agent": "coach", "status": "success", "data": result}), 200
    except Exception as e:
        logger.error("Coach Agent failed: %s", e)
        return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503
    finally:
        _set_agent_state("coach", "idle")


@agents_bp.route("/agents/reflection", methods=["POST"])
def run_reflection():
    """Trigger the Reflection Agent."""
    _set_agent_state("reflection", "running")
    gemini = current_app.extensions.get("gemini_service")
    try:
        t0 = time.time()
        data = request.json or {}
        agent = ReflectionAgent(gemini)
        result = agent.generate_reflection(
            data.get("tasks", []),
            data.get("twin_simulation", {})
        )
        TelemetryService.log_execution("Reflection Agent", "Generate Reflection", "success", t0, 85)
        return jsonify({"agent": "reflection", "status": "success", "data": result}), 200
    except Exception as e:
        logger.error("Reflection Agent failed: %s", e)
        return jsonify({"error": "AI Service Temporarily Unavailable: " + str(e), "status": 503}), 503
    finally:
        _set_agent_state("reflection", "idle")
