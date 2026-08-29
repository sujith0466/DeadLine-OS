"""
DeadlineOS Business OS — Copilot Endpoints
==========================================
Zero-Bypass Conversational AI API.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.copilot_service import CopilotService

copilot_bp = Blueprint('biz_copilot', __name__)


@copilot_bp.route('/copilot/query', methods=['POST'])
@require_workspace('transaction:read')
def ask_copilot():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt')

    try:
        res = CopilotService.ask_copilot(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            prompt=prompt,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data=res,
            message="Copilot insight generated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
