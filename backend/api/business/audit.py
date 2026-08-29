"""
DeadlineOS Business OS — Audit Endpoints
========================================
Provides read-only access to immutable workspace audit history.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from middleware.business_context import require_workspace
from services.business.audit_service import AuditService

audit_bp = Blueprint('biz_audit', __name__)


@audit_bp.route('/audit', methods=['GET'])
@require_workspace('audit:read')
def get_audit_logs():
    """
    Retrieves audit logs scoped to the active workspace.
    """
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        events, total = AuditService.get_events(
            workspace_id=g.workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset
        )
        return success_response(data={"events": events, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
