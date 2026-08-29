"""
DeadlineOS Business OS — Staging & Review Endpoints
===================================================
Handles querying, updating, confirming, and rejecting staged business candidates.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.staging_service import StagingService

staging_bp = Blueprint('biz_staging', __name__)


@staging_bp.route('/staging', methods=['GET'])
@require_workspace('staging:read')
def list_staged_items():
    """
    Lists staged extractions with status and candidate_type filters.
    """
    status = request.args.get('status')
    candidate_type = request.args.get('candidate_type')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        items, total = StagingService.get_staged_items(
            workspace_id=g.workspace_id,
            status=status,
            candidate_type=candidate_type,
            limit=limit,
            offset=offset
        )
        return success_response(data={"staged_items": items, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@staging_bp.route('/staging/<staging_id>', methods=['GET'])
@require_workspace('staging:read')
def get_staged_item(staging_id):
    """
    Retrieves full details of a staged candidate.
    """
    try:
        item = StagingService.get_staged_item_by_id(g.workspace_id, staging_id)
        return success_response(data={"staged_extraction": item.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@staging_bp.route('/staging/<staging_id>', methods=['PATCH'])
@require_workspace('staging:update')
def update_staged_item(staging_id):
    """
    Updates candidate fields (amount, date, partner_id, candidate_type) during human review.
    """
    data = request.get_json(silent=True) or {}
    try:
        updated = StagingService.update_staged_item(
            workspace_id=g.workspace_id,
            staging_id=staging_id,
            actor_user_id=g.user_id,
            updates=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"staged_extraction": updated.serialize()},
            message="Staged candidate updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@staging_bp.route('/staging/<staging_id>/confirm', methods=['POST'])
@require_workspace('staging:confirm')
def confirm_staged_item(staging_id):
    """
    Explicitly confirms the staged candidate as a verified business record.
    """
    try:
        confirmed = StagingService.confirm_staged_item(
            workspace_id=g.workspace_id,
            staging_id=staging_id,
            actor_user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"staged_extraction": confirmed.serialize()},
            message="Candidate confirmed successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@staging_bp.route('/staging/<staging_id>/reject', methods=['POST'])
@require_workspace('staging:reject')
def reject_staged_item(staging_id):
    """
    Rejects the staged candidate with a reason.
    """
    data = request.get_json(silent=True) or {}
    reason = data.get('reason')
    try:
        rejected = StagingService.reject_staged_item(
            workspace_id=g.workspace_id,
            staging_id=staging_id,
            actor_user_id=g.user_id,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"staged_extraction": rejected.serialize()},
            message="Candidate rejected successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
@staging_bp.route('/staging/<staging_id>/commit', methods=['POST'])
@require_workspace('transaction:create')
def commit_staged_item(staging_id):
    """
    Bridges confirmed staging candidate into authoritative Invoice or Transaction ledger.
    """
    data = request.get_json(silent=True) or {}
    target_domain = data.get('target_domain')
    try:
        from services.business.financial_converter_service import FinancialConverterService
        res = FinancialConverterService.commit_staged_item(
            workspace_id=g.workspace_id,
            staging_id=staging_id,
            user_id=g.user_id,
            target_domain=target_domain,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data=res,
            message="Staged candidate successfully committed to financial ledger.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
