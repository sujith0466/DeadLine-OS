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
    """
    GET /api/business/health
    Returns comprehensive deep health and diagnostic telemetry across Business OS subsystems.
    """
    try:
        health_data = BusinessHealthService.check_health()
        status_code = 200 if health_data['status'] in ('HEALTHY', 'DEGRADED') else 503
        return success_response(data=health_data, status_code=status_code)
    except Exception as e:
        return error_response("Health check diagnostics failed", "HEALTH_CHECK_FAILED", 503)


@health_bp.route('/health/liveness', methods=['GET'])
def get_business_liveness():
    """
    GET /api/business/health/liveness
    Returns lightweight process liveness status.
    """
    try:
        liveness_data = BusinessHealthService.check_liveness()
        return success_response(data=liveness_data, status_code=200)
    except Exception as e:
        return error_response("Liveness probe failed", "LIVENESS_FAILED", 503)


@health_bp.route('/health/readiness', methods=['GET'])
def get_business_readiness():
    """
    GET /api/business/health/readiness
    Returns production traffic readiness status.
    """
    try:
        readiness_data = BusinessHealthService.check_readiness()
        status_code = 200 if readiness_data['status'] == 'READY' else 503
        return success_response(data=readiness_data, status_code=status_code)
    except Exception as e:
        return error_response("Readiness probe failed", "READINESS_FAILED", 503)
