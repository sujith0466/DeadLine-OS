"""
DeadlineOS Business OS — Polymorphic Bridge Endpoints
=====================================================
Exposes read-only cross-domain schedule feed of business obligations.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.auth import require_auth
from services.business.bridge_service import BridgeService

bridge_bp = Blueprint('biz_bridge', __name__)


@bridge_bp.route('/bridge/feed', methods=['GET'])
@require_auth
def get_bridge_feed():
    window_days = int(request.args.get('window_days', 14))
    try:
        feed = BridgeService.get_user_unified_feed(g.user_id, window_days=window_days)
        return success_response(data={"virtual_obligations": feed, "count": len(feed)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
