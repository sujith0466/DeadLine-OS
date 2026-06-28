import logging
from flask import Blueprint, jsonify, request, current_app
from services.orchestrator import OrchestratorService
from utils.auth import require_auth

logger = logging.getLogger(__name__)
orchestration_bp = Blueprint("orchestration", __name__)

@orchestration_bp.route("/orchestration/feed", methods=["GET"])
@require_auth
def get_activity_feed():
    """Returns the global AI Activity feed."""
    return jsonify({
        "status": "success",
        "feed": OrchestratorService.get_feed()
    }), 200

@orchestration_bp.route("/orchestration/pipeline", methods=["POST"])
@require_auth
def run_pipeline():
    """
    Triggers the full multi-agent orchestration pipeline starting with an image.
    Accepts multipart/form-data.
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
        image_bytes = file.read()
        orchestrator = OrchestratorService(gemini)
        
        # In a real app we'd parse availability from form data, 
        # but for this demo we'll inject a default availability
        availability = {"daily_available_hours": 6, "preferred_work_hours": {"start": "09:00", "end": "21:00"}}
        
        result = orchestrator.run_pipeline(image_bytes, mime_type, availability)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error("Orchestration pipeline failed: %s", e)
        return jsonify({"error": str(e)}), 500

@orchestration_bp.route("/orchestration/execute", methods=["POST"])
@require_auth
def execute_system_state():
    """
    Evaluates current system state using existing active database records.
    Does not require file uploads.
    """
    gemini = current_app.extensions.get("gemini_service")
    if not gemini:
        return jsonify({"error": "GeminiService not available"}), 503

    try:
        orchestrator = OrchestratorService(gemini)
        result = orchestrator.evaluate_system_state(g.user_id)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error("System Orchestration Evaluation failed: %s", e)
        return jsonify({"error": str(e)}), 500
