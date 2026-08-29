"""
DeadlineOS Business OS — Cross-Workspace Consolidation Endpoints
================================================================
Deterministic consolidated financial overview across multiple authorized workspaces.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from utils.auth import require_auth
from services.business.consolidation_service import ConsolidationService

consolidation_bp = Blueprint('biz_consolidation', __name__)


@consolidation_bp.route('/consolidation/overview', methods=['GET', 'POST'])
@require_auth
def get_consolidated_financial_overview():
    workspace_ids = None
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        workspace_ids = data.get('workspace_ids')
    else:
        raw_ids = request.args.get('workspace_ids')
        if raw_ids:
            workspace_ids = [w.strip() for w in raw_ids.split(',') if w.strip()]

    try:
        overview = ConsolidationService.get_consolidated_overview(
            user_id=g.user_id,
            workspace_ids=workspace_ids
        )
        return success_response(data={'overview': overview})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
