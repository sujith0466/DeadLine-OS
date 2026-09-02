"""
DeadlineOS Business OS — Exchange Rates REST API Blueprint (Phase C3.1)
=======================================================================
RESTful endpoints for recording foreign exchange rates, querying historical provenance,
and converting monetary amounts across supported global currencies.
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime
from decimal import Decimal
from services.business.exchange_rate_service import ExchangeRateService
from utils.auth import require_auth
from middleware.business_context import require_workspace
from utils.errors import APIError

exchange_rates_bp = Blueprint('exchange_rates', __name__)


@exchange_rates_bp.route('', methods=['POST'])
@require_auth
@require_workspace('currency:write')
def record_rate():
    data = request.get_json() or {}
    fx = ExchangeRateService.record_exchange_rate(
        workspace_id=g.workspace_id,
        actor_user_id=g.user_id,
        data=data,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    return jsonify({
        'status': 'success',
        'message': 'Exchange rate recorded successfully.',
        'data': {'exchange_rate': fx.serialize()}
    }), 201


@exchange_rates_bp.route('/history', methods=['GET'])
@require_auth
@require_workspace('currency:read')
def get_rate_history():
    from_curr = request.args.get('from_currency')
    to_curr = request.args.get('to_currency')
    limit = min(int(request.args.get('limit', 50)), 100)

    rates = ExchangeRateService.list_exchange_rates(
        workspace_id=g.workspace_id,
        from_currency=from_curr,
        to_currency=to_curr,
        limit=limit
    )
    return jsonify({
        'status': 'success',
        'data': {
            'exchange_rates': rates,
            'total_count': len(rates)
        }
    }), 200


@exchange_rates_bp.route('/convert', methods=['POST'])
@require_auth
@require_workspace('currency:read')
def convert_amount():
    data = request.get_json() or {}
    amount = data.get('amount')
    from_curr = data.get('from_currency')
    to_curr = data.get('to_currency')

    if not amount or not from_curr or not to_curr:
        raise APIError("Fields 'amount', 'from_currency', and 'to_currency' are required.", code="MISSING_FIELDS", status=400)

    eff_date = None
    if data.get('effective_date'):
        try:
            eff_date = datetime.strptime(str(data['effective_date']), '%Y-%m-%d').date()
        except ValueError:
            eff_date = None

    result = ExchangeRateService.convert_amount(
        workspace_id=g.workspace_id,
        amount=amount,
        from_currency=from_curr,
        to_currency=to_curr,
        effective_date=eff_date
    )
    return jsonify({
        'status': 'success',
        'data': {'conversion': result}
    }), 200


@exchange_rates_bp.route('/currencies', methods=['GET'])
@require_auth
@require_workspace('currency:read')
def get_currencies():
    return jsonify({
        'status': 'success',
        'data': {'supported_currencies': sorted(list(ExchangeRateService.SUPPORTED_CURRENCIES))}
    }), 200
