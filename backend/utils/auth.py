import os
import jwt
from jwt import PyJWKClient
from functools import wraps
from flask import request, jsonify, g
from database.db import db
from models.user import User
import logging
from utils.errors import APIError

logger = logging.getLogger(__name__)

# Global JWKS Client (lazy initialized)
_jwks_client = None

def get_jwks_client():
    global _jwks_client
    if not _jwks_client:
        supabase_url = os.environ.get("SUPABASE_URL")
        if not supabase_url:
            raise ValueError("SUPABASE_URL missing in environment")
        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return jsonify({}), 200

        # 1. Extract Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Unauthorized access attempt: Missing or invalid Authorization header.")
            raise APIError("Missing Authorization header", code="UNAUTHORIZED", status=401)
            
        token = auth_header.split(" ")[1]

        # 2. Decode & Validate Token
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg")
            
            if alg == "HS256":
                # Fallback to symmetric if project uses old HS256
                secret = os.environ.get("SUPABASE_JWT_SECRET")
                if not secret:
                    raise APIError("Auth configuration missing", code="INTERNAL_ERROR", status=500)
                payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
            else:
                # Asymmetric verification (ES256, RS256) via JWKS
                jwks_client = get_jwks_client()
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token, 
                    signing_key.key, 
                    algorithms=["RS256", "ES256"], 
                    options={"verify_aud": False}
                )
        except jwt.ExpiredSignatureError:
            logger.warning("Unauthorized access attempt: Token expired.")
            raise APIError("Token has expired", code="TOKEN_EXPIRED", status=401)
        except Exception as e:
            logger.warning(f"Unauthorized access attempt: Invalid token ({str(e)}).")
            raise APIError("Invalid token", code="INVALID_TOKEN", status=401)

        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id:
            raise APIError("Invalid token payload", code="INVALID_TOKEN", status=401)

        # 3. User Identity Sync (Neon Database)
        # Ensure the user exists in our local database so foreign keys resolve.
        user = User.query.get(user_id)
        if not user:
            logger.info(f"First time login for user {user_id}. Syncing identity to Neon DB.")
            
            # Extract metadata if available
            user_metadata = payload.get("user_metadata", {})
            full_name = user_metadata.get("full_name") or user_metadata.get("name")
            username = user_metadata.get("username")
            
            new_user = User(
                id=user_id,
                email=email or f"{user_id}@placeholder.com",
                username=username,
                full_name=full_name
            )
            try:
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to sync user identity: {e}")
                raise APIError("Failed to sync user identity", code="INTERNAL_ERROR", status=500)

        # 4. Attach user context to global object
        g.user_id = user_id
        
        is_demo_email = False
        if email and email.startswith('demo_') and '@deadlineos.com' in email:
            is_demo_email = True
        elif user and user.email and user.email.startswith('demo_') and '@deadlineos.com' in user.email:
            is_demo_email = True
            
        g.is_demo = is_demo_email
        
        return f(*args, **kwargs)
    return decorated
