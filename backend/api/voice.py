import logging
from flask import Blueprint, jsonify, request, current_app
from services.voice_service import VoiceService

logger = logging.getLogger(__name__)
voice_bp = Blueprint("voice", __name__)

@voice_bp.route("/voice/process", methods=["POST"])
def process_voice():
    data = request.json or {}
    transcript = data.get("transcript")
    
    if not transcript:
        return jsonify({"status": "error", "message": "Transcript is required"}), 400
        
    gemini = current_app.extensions.get("gemini_service")
    result = VoiceService.process_voice_command(transcript, gemini)
    return jsonify({"status": "success", "data": result}), 200
