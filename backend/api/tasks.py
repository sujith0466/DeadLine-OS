"""
DeadlineOS — Tasks Blueprint
================================
Full CRUD API for task management.

Routes
------
GET    /api/tasks               →  List all tasks (with filters)
POST   /api/tasks               →  Create a new task
GET    /api/tasks/<id>          →  Get single task details
PUT    /api/tasks/<id>          →  Update task fields
DELETE /api/tasks/<id>          →  Delete a task
POST   /api/tasks/<id>/progress →  Log progress (hours + completion %)
"""

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from database.db import db
from models.task import Task

logger = logging.getLogger(__name__)

tasks_bp = Blueprint("tasks", __name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

VALID_STATUSES = {"pending", "in_progress", "done", "overdue"}
VALID_CATEGORIES = {"work", "personal", "study", "other"}
VALID_SOURCES = {"manual", "vision", "voice"}


def _task_or_404(task_id: str) -> Task:
    """Return the Task with the given id or raise a 404."""
    task = Task.query.get(task_id)
    if task is None:
        from flask import abort
        abort(404, description=f"Task '{task_id}' not found.")
    return task


# ── Routes ────────────────────────────────────────────────────────────────────

@tasks_bp.route("/tasks", methods=["GET"])
def list_tasks():
    """
    List all tasks.

    Query Parameters
    ----------------
    status   : Filter by status  (pending | in_progress | done | overdue)
    category : Filter by category (work | personal | study)
    sort     : Sort field — deadline (default) | created_at | title
    order    : asc (default) | desc

    Response 200
    ------------
    { "tasks": [...], "count": <int> }
    """
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    sort_field = request.args.get("sort", "deadline")
    order = request.args.get("order", "asc")

    query = Task.query

    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter(Task.status == status_filter)

    if category_filter and category_filter in VALID_CATEGORIES:
        query = query.filter(Task.category == category_filter)

    # Pagination
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))
    offset = (page - 1) * limit

    # Sorting
    sort_column = getattr(Task, sort_field, Task.deadline)
    query = query.order_by(
        sort_column.desc() if order == "desc" else sort_column.asc()
    )

    total_count = query.count()
    tasks = query.offset(offset).limit(limit).all()
    
    return jsonify({
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
        "total": total_count,
        "page": page,
        "limit": limit
    }), 200


@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    """
    Create a new task.

    Request Body (JSON)
    -------------------
    {
        "title":            "<str>  required",
        "description":      "<str>  optional",
        "deadline":         "<ISO 8601 datetime>  required",
        "estimated_hours":  <float>  optional,
        "category":         "<work|personal|study>  optional",
        "source":           "<manual|vision|voice>  optional"
    }

    Response 201
    ------------
    { "task": {...}, "message": "Task created successfully" }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate required fields
    errors = []
    if not data.get("title", "").strip():
        errors.append("'title' is required and cannot be empty.")
    if not data.get("deadline"):
        errors.append("'deadline' is required (ISO 8601 format).")

    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 422

    # Parse deadline
    try:
        deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return jsonify(
            {"error": "Invalid 'deadline' format. Use ISO 8601 (e.g. 2026-06-23T18:00:00Z)."}
        ), 422

    task = Task(
        id=str(uuid.uuid4()),
        title=data["title"].strip(),
        description=data.get("description", "").strip() or None,
        deadline=deadline,
        estimated_hours=float(data.get("estimated_hours", 1.0)),
        category=data.get("category", "work") if data.get("category") in VALID_CATEGORIES else "work",
        status="pending",
        source=data.get("source", "manual") if data.get("source") in VALID_SOURCES else "manual",
        source_file=data.get("source_file"),
    )

    db.session.add(task)
    db.session.commit()

    logger.info("Task created: id=%s title=%r", task.id, task.title)
    return jsonify({"task": task.to_dict(), "message": "Task created successfully"}), 201


@tasks_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id: str):
    """
    Get a single task by ID.

    Response 200
    ------------
    { "task": {...} }
    """
    task = _task_or_404(task_id)
    return jsonify({"task": task.to_dict()}), 200


@tasks_bp.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id: str):
    """
    Update one or more fields of a task.

    Request Body (JSON) — all fields optional
    -----------------------------------------
    {
        "title":           "<str>",
        "description":     "<str>",
        "deadline":        "<ISO 8601 datetime>",
        "estimated_hours": <float>,
        "actual_hours":    <float>,
        "category":        "<work|personal|study>",
        "status":          "<pending|in_progress|done|overdue>"
    }

    Response 200
    ------------
    { "task": {...}, "message": "Task updated" }
    """
    task = _task_or_404(task_id)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    updatable_fields = {
        "title": str,
        "description": str,
        "estimated_hours": float,
        "actual_hours": float,
        "category": str,
        "status": str,
    }

    for field, cast_fn in updatable_fields.items():
        if field in data:
            value = data[field]
            # Status / category validation
            if field == "status" and value not in VALID_STATUSES:
                return jsonify({"error": f"Invalid status '{value}'."}), 422
            if field == "category" and value not in VALID_CATEGORIES:
                return jsonify({"error": f"Invalid category '{value}'."}), 422
            setattr(task, field, cast_fn(value) if value is not None else None)

    if "deadline" in data:
        try:
            task.deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return jsonify({"error": "Invalid 'deadline' format."}), 422

    task.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Task updated: id=%s", task_id)
    return jsonify({"task": task.to_dict(), "message": "Task updated"}), 200


@tasks_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """
    Delete a task by ID.

    Response 200
    ------------
    { "message": "Task deleted", "id": "<task_id>" }
    """
    task = _task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()

    logger.info("Task deleted: id=%s", task_id)
    return jsonify({"message": "Task deleted", "id": task_id}), 200


@tasks_bp.route("/tasks/<task_id>/progress", methods=["POST"])
def log_progress(task_id: str):
    """
    Log a progress update for a task.

    Adds hours worked to actual_hours and optionally updates status.

    Request Body (JSON)
    -------------------
    {
        "hours_logged": <float>   required — hours worked in this session,
        "status":       "<str>"   optional — override status
    }

    Response 200
    ------------
    {
        "task": {...},
        "completion_percentage": <float>,
        "message": "Progress logged"
    }
    """
    task = _task_or_404(task_id)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    hours = data.get("hours_logged")
    if hours is None or not isinstance(hours, (int, float)) or hours < 0:
        return jsonify({"error": "'hours_logged' must be a non-negative number."}), 422

    task.actual_hours = round((task.actual_hours or 0) + float(hours), 2)

    # Optional status override
    new_status = data.get("status")
    if new_status and new_status in VALID_STATUSES:
        task.status = new_status

    task.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info(
        "Progress logged: task_id=%s hours_added=%.2f total_hours=%.2f",
        task_id, hours, task.actual_hours,
    )

    return jsonify(
        {
            "task": task.to_dict(),
            "completion_percentage": task.completion_percentage,
            "message": "Progress logged",
        }
    ), 200
