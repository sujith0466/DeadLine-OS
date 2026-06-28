import logging
from flask import Blueprint, jsonify, request, g
from services.goal_service import GoalService
from services.intervention_engine import InterventionEngine
from utils.auth import require_auth

logger = logging.getLogger(__name__)
goals_bp = Blueprint("goals", __name__)

@goals_bp.route("/goals", methods=["GET"])
@require_auth
def get_goals():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))
    return jsonify({"status": "success", "data": GoalService.get_goals(g.user_id, page, limit)}), 200

@goals_bp.route("/habits", methods=["GET"])
@require_auth
def get_habits():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))
    return jsonify({"status": "success", "data": GoalService.get_habits(g.user_id, page, limit)}), 200

@goals_bp.route("/goals", methods=["POST"])
@require_auth
def create_goal():
    data = request.json or {}
    title = data.get("title")
    description = data.get("description", "")
    category = data.get("category", "General")
    target_date = data.get("target_date")
    
    if not title:
        return jsonify({"status": "error", "message": "Title is required"}), 400
        
    try:
        goal = GoalService.create_goal(g.user_id, title, description, category, target_date)
        return jsonify({"status": "success", "data": goal}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 409

@goals_bp.route("/habits", methods=["POST"])
@require_auth
def create_habit():
    data = request.json or {}
    name = data.get("name")
    category = data.get("category", "General")
    frequency = data.get("frequency", "Daily")
    
    if not name:
        return jsonify({"status": "error", "message": "Name is required"}), 400
        
    try:
        habit = GoalService.create_habit(g.user_id, name, category, frequency)
        return jsonify({"status": "success", "data": habit}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 409

@goals_bp.route("/goals/<goal_id>", methods=["PUT"])
@require_auth
def edit_goal(goal_id):
    try:
        res = GoalService.edit_goal(g.user_id, goal_id, request.json or {})
        InterventionEngine.trigger_evaluation()
        return jsonify({"status": "success", "data": res}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404

@goals_bp.route("/goals/<goal_id>", methods=["DELETE"])
@require_auth
def delete_goal(goal_id):
    if GoalService.delete_goal(g.user_id, goal_id):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Goal not found"}), 404

@goals_bp.route("/goals/<goal_id>/archive", methods=["POST"])
@require_auth
def archive_goal(goal_id):
    if GoalService.archive_goal(g.user_id, goal_id):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Goal not found"}), 404

@goals_bp.route("/goals/<goal_id>/unarchive", methods=["POST"])
@require_auth
def unarchive_goal(goal_id):
    if GoalService.unarchive_goal(g.user_id, goal_id):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Goal not found"}), 404

@goals_bp.route("/goals/<goal_id>/pin", methods=["POST"])
@require_auth
def toggle_pin_goal(goal_id):
    if GoalService.toggle_pin_goal(g.user_id, goal_id):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Goal not found"}), 404

@goals_bp.route("/milestones/<milestone_id>/status", methods=["PUT"])
@require_auth
def update_milestone_status(milestone_id):
    data = request.json or {}
    status = data.get("status")
    if not status: return jsonify({"status": "error", "message": "Status required"}), 400
    try:
        res = GoalService.update_milestone_status(g.user_id, milestone_id, status)
        InterventionEngine.trigger_evaluation()
        return jsonify({"status": "success", "data": res}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404

@goals_bp.route("/habits/<habit_id>", methods=["PUT"])
@require_auth
def edit_habit(habit_id):
    try:
        return jsonify({"status": "success", "data": GoalService.edit_habit(g.user_id, habit_id, request.json or {})}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404

@goals_bp.route("/habits/<habit_id>", methods=["DELETE"])
@require_auth
def delete_habit(habit_id):
    if GoalService.delete_habit(g.user_id, habit_id):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Habit not found"}), 404

@goals_bp.route("/habits/<habit_id>/archive", methods=["POST"])
@require_auth
def archive_habit(habit_id):
    if GoalService.archive_habit(g.user_id, habit_id):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Habit not found"}), 404

@goals_bp.route("/habits/<habit_id>/unarchive", methods=["POST"])
@require_auth
def unarchive_habit(habit_id):
    if GoalService.unarchive_habit(g.user_id, habit_id):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Habit not found"}), 404

@goals_bp.route("/habits/<habit_id>/status", methods=["POST"])
@require_auth
def set_habit_status(habit_id):
    data = request.json or {}
    status = data.get("status")
    if not status: return jsonify({"status": "error", "message": "Status required"}), 400
    try:
        return jsonify({"status": "success", "data": GoalService.set_habit_status(g.user_id, habit_id, status)}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404

@goals_bp.route("/habits/<habit_id>/checkin", methods=["POST"])
@require_auth
def check_in_habit(habit_id):
    try:
        res = GoalService.check_in_habit(g.user_id, habit_id)
        InterventionEngine.trigger_evaluation()
        return jsonify({"status": "success", "data": res}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
