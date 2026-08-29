"""
DeadlineOS Business OS — Invoice Endpoints
==========================================
Handles invoice creation, query, issuance, and voiding.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.invoice_service import InvoiceService

invoices_bp = Blueprint('biz_invoices', __name__)


@invoices_bp.route('/invoices', methods=['GET'])
@require_workspace('transaction:read')
def list_invoices():
    status = request.args.get('status')
    invoice_type = request.args.get('invoice_type')
    partner_id = request.args.get('partner_id')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        invoices, total = InvoiceService.get_invoices(
            workspace_id=g.workspace_id,
            status=status,
            invoice_type=invoice_type,
            partner_id=partner_id,
            limit=limit,
            offset=offset
        )
        return success_response(data={"invoices": invoices, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@invoices_bp.route('/invoices', methods=['POST'])
@require_workspace('transaction:create')
def create_invoice():
    data = request.get_json(silent=True) or {}
    try:
        invoice = InvoiceService.create_invoice(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"invoice": invoice.serialize()},
            message="Invoice created successfully in DRAFT status.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@invoices_bp.route('/invoices/<invoice_id>', methods=['GET'])
@require_workspace('transaction:read')
def get_invoice(invoice_id):
    try:
        invoice = InvoiceService.get_invoice_by_id(g.workspace_id, invoice_id)
        return success_response(data={"invoice": invoice.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@invoices_bp.route('/invoices/<invoice_id>/issue', methods=['POST'])
@require_workspace('transaction:create')
def issue_invoice(invoice_id):
    try:
        invoice = InvoiceService.issue_invoice(
            workspace_id=g.workspace_id,
            invoice_id=invoice_id,
            user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"invoice": invoice.serialize()},
            message="Invoice issued and arithmetic frozen."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@invoices_bp.route('/invoices/<invoice_id>/void', methods=['POST'])
@require_workspace('transaction:reverse')
def void_invoice(invoice_id):
    data = request.get_json(silent=True) or {}
    reason = data.get('reason')
    try:
        invoice = InvoiceService.void_invoice(
            workspace_id=g.workspace_id,
            invoice_id=invoice_id,
            user_id=g.user_id,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"invoice": invoice.serialize()},
            message="Invoice voided successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
