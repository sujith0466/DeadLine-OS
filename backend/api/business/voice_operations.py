"""
DeadlineOS Business OS — Voice Operations API Endpoints (Phase C2.5)
===================================================================
REST API for processing spoken operations transcripts and retrieving
voice staging history.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.voice_operations_service import VoiceOperationsService

voice_ops_bp = Blueprint('biz_voice_operations', __name__)


@voice_ops_bp.route('/process', methods=['POST'])
@require_workspace('staging:create')
def process_voice_operation():
    """
    Translates an operational voice transcript into a verified staged candidate.
    Zero-Bypass: Returns StagedExtraction in NEEDS_REVIEW status.
    """
    data = request.get_json(silent=True) or {}
    transcript = data.get('transcript', '').strip()
    audio_duration = data.get('audio_duration_seconds')
    context_hints = data.get('context_hints', {})

    if not transcript:
        return error_response("Field 'transcript' is required and cannot be empty.", code="VALIDATION_ERROR", status_code=400)

    try:
        result = VoiceOperationsService.process_voice_operation(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            transcript=transcript,
            audio_duration_seconds=float(audio_duration) if audio_duration is not None else None,
            context_hints=context_hints,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data=result,
            message="Voice operation processed and staged for review.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@voice_ops_bp.route('/history', methods=['GET'])
@require_workspace('staging:read')
def list_voice_operations_history():
    """
    Retrieves chronological history of voice-extracted staging operations.
    """
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        items, total = VoiceOperationsService.get_voice_operations_history(
            workspace_id=g.workspace_id,
            limit=limit,
            offset=offset
        )
        return success_response(data={"staged_operations": items, "total_count": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
