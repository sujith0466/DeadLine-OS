import logging
from flask import Blueprint, jsonify, request
from services.goal_service import GoalService

logger = logging.getLogger(__name__)
goals_bp = Blueprint("goals", __name__)

@goals_bp.route("/goals", methods=["GET"])
def get_goals():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))
    return jsonify({"status": "success", "data": GoalService.get_goals(page, limit)}), 200

@goals_bp.route("/habits", methods=["GET"])
def get_habits():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))
    return jsonify({"status": "success", "data": GoalService.get_habits(page, limit)}), 200

@goals_bp.route("/goals", methods=["POST"])
def create_goal():
    data = request.json or {}
    title = data.get("title")
    description = data.get("description", "")
    category = data.get("category", "General")
    target_date = data.get("target_date")
    
    if not title:
        return jsonify({"status": "error", "message": "Title is required"}), 400
        
    goal = GoalService.create_goal(title, description, category, target_date)
    return jsonify({"status": "success", "data": goal}), 201

@goals_bp.route("/habits", methods=["POST"])
def create_habit():
    data = request.json or {}
    name = data.get("name")
    category = data.get("category", "General")
    frequency = data.get("frequency", "Daily")
    
    if not name:
        return jsonify({"status": "error", "message": "Name is required"}), 400
        
    habit = GoalService.create_habit(name, category, frequency)
    return jsonify({"status": "success", "data": habit}), 201
