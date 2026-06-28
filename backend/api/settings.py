import json
from flask import Blueprint, request, g, jsonify
from database.db import db
from models.user import User
from models.user_settings import UserSettings
from models.user_session import UserSession
from models.task import Task
from models.goal import Goal
from utils.auth import require_auth
from utils.responses import success_response
from utils.errors import APIError

settings_bp = Blueprint("settings", __name__)

def _update_json_column(column_data, new_data):
    """Helper to merge dicts for JSON columns."""
    if not column_data:
        return new_data
    merged = dict(column_data)
    merged.update(new_data)
    return merged

@settings_bp.route("/settings/profile", methods=["GET"])
@require_auth
def get_profile():
    user = User.query.get(g.user_id)
    if not user: raise APIError("User not found", status=404)
    return success_response(user.serialize())

@settings_bp.route("/settings/profile", methods=["PUT"])
@require_auth
def update_profile():
    data = request.json or {}
    user = User.query.get(g.user_id)
    if not user: raise APIError("User not found", status=404)
    
    # Allowed fields
    allowed = ["full_name", "username", "email", "timezone", "country", "avatar_url"]
    for field in allowed:
        if field in data:
            setattr(user, field, data[field])
            
    db.session.commit()
    return success_response(user.serialize())

@settings_bp.route("/settings/<section>", methods=["GET"])
@require_auth
def get_settings_section(section):
    valid_sections = ["appearance", "notifications", "planner", "ai", "security"]
    if section not in valid_sections:
        raise APIError("Invalid section", status=400)
        
    settings = UserSettings.get_or_create(g.user_id)
    return success_response(getattr(settings, section) or {})

@settings_bp.route("/settings/<section>", methods=["PUT"])
@require_auth
def update_settings_section(section):
    valid_sections = ["appearance", "notifications", "planner", "ai", "security"]
    if section not in valid_sections:
        raise APIError("Invalid section", status=400)
        
    data = request.json or {}
    settings = UserSettings.get_or_create(g.user_id)
    
    current_data = getattr(settings, section)
    updated_data = _update_json_column(current_data, data)
    setattr(settings, section, updated_data)
    
    db.session.commit()
    return success_response(updated_data)

@settings_bp.route("/settings/sessions", methods=["GET"])
@require_auth
def get_sessions():
    sessions = UserSession.query.filter_by(user_id=g.user_id).order_by(UserSession.last_active.desc()).all()
    # Mock current session by picking the most recent if no auth tracking exists
    if sessions:
        sessions[0].is_current = True
    return success_response([s.serialize() for s in sessions])

@settings_bp.route("/settings/sessions", methods=["POST"])
@require_auth
def create_session():
    # Helper to simulate session creation
    data = request.json or {}
    session = UserSession(
        user_id=g.user_id,
        browser=data.get("browser", "Unknown"),
        os=data.get("os", "Unknown"),
        location=data.get("location", "Unknown"),
        ip_address=request.remote_addr
    )
    db.session.add(session)
    db.session.commit()
    return success_response(session.serialize())

@settings_bp.route("/settings/session/<session_id>", methods=["DELETE"])
@require_auth
def delete_session(session_id):
    session = UserSession.query.filter_by(id=session_id, user_id=g.user_id).first()
    if not session: raise APIError("Session not found", status=404)
    db.session.delete(session)
    db.session.commit()
    return success_response({"message": "Session revoked"})

@settings_bp.route("/settings/accounts", methods=["GET"])
@require_auth
def get_accounts():
    # Mocking connected accounts as they usually tie into OAuth providers
    # For a real implementation, this would query Supabase Identities
    return success_response([
        {"provider": "google", "connected": True, "email": "user@gmail.com"},
        {"provider": "github", "connected": False},
        {"provider": "microsoft", "connected": False},
        {"provider": "calendar", "connected": True, "email": "user@gmail.com"}
    ])

@settings_bp.route("/settings/accounts", methods=["PUT"])
@require_auth
def update_accounts():
    return success_response({"message": "OAuth updates require redirect"})

@settings_bp.route("/settings/export", methods=["POST"])
@require_auth
def export_data():
    user = User.query.get(g.user_id)
    settings = UserSettings.query.get(g.user_id)
    tasks = Task.query.filter_by(user_id=g.user_id).all()
    goals = Goal.query.filter_by(user_id=g.user_id).all()
    
    export_payload = {
        "profile": user.serialize() if user else {},
        "settings": settings.serialize() if settings else {},
        "tasks": [t.serialize() for t in tasks],
        "goals": [g.serialize() for g in goals]
    }
    return success_response(export_payload, message="Data exported successfully")

@settings_bp.route("/account", methods=["DELETE"])
@require_auth
def delete_account():
    # In a real app, you would also delete from Supabase Auth
    user = User.query.get(g.user_id)
    if not user: raise APIError("User not found", status=404)
    db.session.delete(user)
    db.session.commit()
    return success_response({"message": "Account deleted successfully"})
