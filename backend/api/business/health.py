"""
DeadlineOS Business OS — Health & Telemetry Endpoint
===================================================
Non-mutating diagnostic health probe for Business OS subsystem monitoring.
"""

from flask import Blueprint
from utils.responses import success_response, error_response
from services.business.health_service import BusinessHealthService

health_bp = Blueprint('biz_health', __name__)


@health_bp.route('/health', methods=['GET'])
def get_business_health():
    try:
        health_data = BusinessHealthService.check_health()
        status_code = 200 if health_data['status'] == 'HEALTHY' else 503
        return success_response(data=health_data, status_code=status_code)
    except Exception as e:
        return error_response(str(e), "HEALTH_CHECK_FAILED", 503)
