"""
DeadlineOS Business OS — Business Tasks Endpoints
==================================================
Handles task creation, querying, updates, member assignment, and status transitions.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.task_service import TaskService

tasks_bp = Blueprint('biz_tasks', __name__)


@tasks_bp.route('/tasks', methods=['GET'])
@require_workspace('tasks:read')
def list_tasks():
    status = request.args.get('status')
    priority = request.args.get('priority')
    assignee_id = request.args.get('assignee_id')
    location_id = request.args.get('location_id')
    product_id = request.args.get('product_id')
    category = request.args.get('category')
    search = request.args.get('search')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        tasks, total = TaskService.get_tasks(
            workspace_id=g.workspace_id,
            status=status,
            priority=priority,
            assignee_member_id=assignee_id,
            location_id=location_id,
            product_id=product_id,
            category=category,
            search=search,
            limit=limit,
            offset=offset
        )
        return success_response(data={"tasks": tasks, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@tasks_bp.route('/tasks', methods=['POST'])
@require_workspace('tasks:create')
def create_task():
    data = request.get_json(silent=True) or {}
    try:
        task = TaskService.create_task(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"task": task.serialize()},
            message="Business task created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@tasks_bp.route('/tasks/<task_id>', methods=['GET'])
@require_workspace('tasks:read')
def get_task(task_id):
    try:
        task = TaskService.get_task_by_id(g.workspace_id, task_id)
        return success_response(data={"task": task.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@tasks_bp.route('/tasks/<task_id>', methods=['PUT'])
@require_workspace('tasks:update')
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    try:
        task = TaskService.update_task(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            task_id=task_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"task": task.serialize()},
            message="Task updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@tasks_bp.route('/tasks/<task_id>/assign', methods=['POST'])
@require_workspace('tasks:assign')
def assign_task(task_id):
    data = request.get_json(silent=True) or {}
    assignee_id = data.get('assignee_member_id')
    try:
        task = TaskService.assign_task(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            task_id=task_id,
            assignee_member_id=assignee_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"task": task.serialize()},
            message="Task assigned successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@tasks_bp.route('/tasks/<task_id>/status', methods=['POST'])
@require_workspace('tasks:update')
def transition_task_status(task_id):
    data = request.get_json(silent=True) or {}
    status = data.get('status')
    reason = data.get('reason')
    if not status:
        return error_response("Field 'status' is required.", "VALIDATION_ERROR", 400)

    try:
        task = TaskService.transition_status(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            task_id=task_id,
            new_status=status,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"task": task.serialize()},
            message=f"Task status transitioned to {status}."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
@require_workspace('tasks:delete')
def delete_task(task_id):
    try:
        TaskService.delete_task(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            task_id=task_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(message="Task deleted successfully.")
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
