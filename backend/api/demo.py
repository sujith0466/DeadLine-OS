from flask import Blueprint, jsonify
import os
import requests
from database.db import db
from models.user import User

from app import limiter

demo_bp = Blueprint("demo", __name__)

@demo_bp.route("/demo/start", methods=["POST"])
@limiter.limit("10 per minute")
def start_demo():
    """Authenticate the permanent demo account and return the session."""
    email = os.environ.get("DEMO_USER_EMAIL")
    password = os.environ.get("DEMO_USER_PASSWORD")
    supabase_url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")

    if not all([email, password, supabase_url, anon_key]):
        return jsonify({"error": "Demo configuration missing on server"}), 500

    # Call Supabase to authenticate
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json"
    }
    res = requests.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers=headers,
        timeout=10
    )
    if res.status_code != 200:
        return jsonify({"error": f"Failed to authenticate demo user: {res.text}"}), 401
    
    session_data = res.json()
    demo_user_id = session_data.get("user", {}).get("id")
    
    # Ensure local user exists just in case
    user = db.session.get(User, demo_user_id)
    if not user:
        new_user = User(
            id=demo_user_id,
            email=email,
            username="demo_user",
            full_name="Demo User"
        )
        db.session.add(new_user)
        db.session.commit()
    
    return jsonify({
        "access_token": session_data.get("access_token"),
        "refresh_token": session_data.get("refresh_token"),
        "user": session_data.get("user")
    })
