"""
DeadlineOS Business OS — Payment Allocation Endpoints
=====================================================
Handles linking payments/transactions to open invoices.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.allocation_service import AllocationService

allocations_bp = Blueprint('biz_allocations', __name__)


@allocations_bp.route('/allocations', methods=['POST'])
@require_workspace('transaction:create')
def allocate_payment():
    data = request.get_json(silent=True) or {}
    transaction_id = data.get('transaction_id')
    allocations_list = data.get('allocations', [])

    if not transaction_id or not allocations_list:
        return error_response("Fields 'transaction_id' and 'allocations' are required.", "VALIDATION_ERROR", 400)

    try:
        allocs = AllocationService.allocate_payment(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            transaction_id=transaction_id,
            allocations_data=allocations_list,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"allocations": [a.serialize() for a in allocs]},
            message="Payment allocated successfully to invoices.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
