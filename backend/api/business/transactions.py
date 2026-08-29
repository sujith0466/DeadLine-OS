"""
DeadlineOS Business OS — Transaction Endpoints
==============================================
Handles operational event ledger ingestion and formal reversals.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.transaction_service import TransactionService

transactions_bp = Blueprint('biz_transactions', __name__)


@transactions_bp.route('/transactions', methods=['GET'])
@require_workspace('transaction:read')
def list_transactions():
    transaction_type = request.args.get('transaction_type')
    status = request.args.get('status')
    partner_id = request.args.get('partner_id')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        txs, total = TransactionService.get_transactions(
            workspace_id=g.workspace_id,
            transaction_type=transaction_type,
            status=status,
            partner_id=partner_id,
            limit=limit,
            offset=offset
        )
        return success_response(data={"transactions": txs, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@transactions_bp.route('/transactions', methods=['POST'])
@require_workspace('transaction:create')
def record_transaction():
    data = request.get_json(silent=True) or {}
    try:
        tx = TransactionService.record_transaction(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"transaction": tx.serialize()},
            message="Transaction recorded successfully in ledger.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@transactions_bp.route('/transactions/<transaction_id>', methods=['GET'])
@require_workspace('transaction:read')
def get_transaction(transaction_id):
    try:
        tx = TransactionService.get_transaction_by_id(g.workspace_id, transaction_id)
        return success_response(data={"transaction": tx.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@transactions_bp.route('/transactions/<transaction_id>/reverse', methods=['POST'])
@require_workspace('transaction:reverse')
def reverse_transaction(transaction_id):
    data = request.get_json(silent=True) or {}
    reason = data.get('reason')
    try:
        tx = TransactionService.reverse_transaction(
            workspace_id=g.workspace_id,
            transaction_id=transaction_id,
            user_id=g.user_id,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"transaction": tx.serialize()},
            message="Transaction reversed with append-only counter-adjustment."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
