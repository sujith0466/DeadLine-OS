"""
DeadlineOS Business OS — Commercial Partner Endpoints
=====================================================
Handles Customer and Supplier registration, listing, search, and updates.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.partner_service import PartnerService

partners_bp = Blueprint('biz_partners', __name__)


@partners_bp.route('/partners', methods=['GET'])
@require_workspace('partners:read')
def list_partners():
    partner_type = request.args.get('type')
    search = request.args.get('search')
    status = request.args.get('status', 'ACTIVE')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        partners, total = PartnerService.get_partners(
            workspace_id=g.workspace_id,
            partner_type=partner_type,
            search=search,
            status=status,
            limit=limit,
            offset=offset
        )
        return success_response(data={"partners": partners, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@partners_bp.route('/partners', methods=['POST'])
@require_workspace('partners:create')
def create_partner():
    data = request.get_json() or {}
    name = data.get('name')
    partner_type = data.get('partner_type')

    if not name or not partner_type:
        return error_response("Fields 'name' and 'partner_type' are required.", "VALIDATION_ERROR", 400)

    try:
        partner = PartnerService.create_partner(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            partner_type=partner_type,
            name=name,
            legal_name=data.get('legal_name'),
            phone=data.get('phone'),
            email=data.get('email'),
            tax_identifier=data.get('tax_identifier'),
            credit_period_days=data.get('credit_period_days', 30),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"partner": partner.serialize()},
            message="Commercial partner created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@partners_bp.route('/partners/<partner_id>', methods=['GET'])
@require_workspace('partners:read')
def get_partner(partner_id):
    try:
        partner = PartnerService.get_partner_by_id(g.workspace_id, partner_id)
        return success_response(data={"partner": partner.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@partners_bp.route('/partners/<partner_id>', methods=['PATCH'])
@require_workspace('partners:update')
def update_partner(partner_id):
    data = request.get_json() or {}
    try:
        updated = PartnerService.update_partner(
            workspace_id=g.workspace_id,
            partner_id=partner_id,
            actor_user_id=g.user_id,
            updates=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"partner": updated.serialize()},
            message="Partner updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@partners_bp.route('/partners/<partner_id>/archive', methods=['POST'])
@require_workspace('partners:archive')
def archive_partner(partner_id):
    data = request.get_json() or {}
    reason = data.get('reason')
    try:
        archived = PartnerService.archive_partner(
            workspace_id=g.workspace_id,
            partner_id=partner_id,
            actor_user_id=g.user_id,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"partner": archived.serialize()},
            message="Partner archived successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
