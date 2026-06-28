from flask import Blueprint, request, g
from marshmallow import Schema, fields, validate
from database.db import db
from models.user import User
from utils.auth import require_auth
from utils.responses import success_response
from utils.errors import APIError
from utils.validation import validate_schema

users_bp = Blueprint("users", __name__)

class UserProfileUpdateSchema(Schema):
    full_name = fields.String(validate=validate.Length(max=255))
    username = fields.String(validate=validate.Length(max=100))
    avatar_url = fields.URL(validate=validate.Length(max=512))
    timezone = fields.String(validate=validate.Length(max=100))
    country = fields.String(validate=validate.Length(max=100))
    working_hours_start = fields.String(validate=validate.Regexp(r'^\d{2}:\d{2}$'))
    working_hours_end = fields.String(validate=validate.Regexp(r'^\d{2}:\d{2}$'))
    focus_hours_start = fields.String(validate=validate.Regexp(r'^\d{2}:\d{2}$'), allow_none=True)
    focus_hours_end = fields.String(validate=validate.Regexp(r'^\d{2}:\d{2}$'), allow_none=True)
    daily_capacity = fields.Float(validate=validate.Range(min=0.5, max=24.0))
    preferred_planning_mode = fields.String(validate=validate.OneOf(["balanced", "aggressive", "safe"]))
    theme_preference = fields.String(validate=validate.OneOf(["light", "dark", "system"]))

@users_bp.route("/users/me", methods=["GET"])
@require_auth
def get_my_profile():
    """Retrieve the authenticated user's profile."""
    user = User.query.get(g.user_id)
    if not user:
        raise APIError("User profile not found", status=404)
    return success_response(user.serialize())

@users_bp.route("/users/me", methods=["PATCH"])
@require_auth
@validate_schema(UserProfileUpdateSchema)
def update_my_profile(validated_data):
    """Update the authenticated user's profile."""
    user = User.query.get(g.user_id)
    if not user:
        raise APIError("User profile not found", status=404)
        
    for key, value in validated_data.items():
        setattr(user, key, value)
        
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise APIError("Failed to update profile due to a conflict.", status=409, details={"error": str(e)})
        
    return success_response(user.serialize(), message="Profile updated successfully")
