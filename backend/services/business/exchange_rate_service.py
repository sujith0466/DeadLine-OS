"""
DeadlineOS Business OS — Exchange Rate Service (Phase C3.1)
===========================================================
Encapsulates multi-currency logic, exchange rate registry management,
7-day historical lookback, provenance tracking, and deterministic Decimal conversion.
"""

from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from database.db import db
from models.business import Workspace, BusinessExchangeRate, AuditEvent
from utils.errors import APIError
from services.business.audit_service import AuditService


class ExchangeRateService:
    """
    Manages currency pairs, exchange rates, and deterministic multi-currency conversion.
    """
    SUPPORTED_CURRENCIES = {
        'INR', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'SGD', 'AED', 'CAD', 'AUD', 'CHF', 'HKD'
    }

    @staticmethod
    def _normalize_currency(curr: str) -> str:
        if not curr or not isinstance(curr, str):
            raise APIError("Currency code must be a valid 3-letter string.", code="INVALID_CURRENCY", status=400)
        code = curr.strip().upper()
        if len(code) != 3 or code not in ExchangeRateService.SUPPORTED_CURRENCIES:
            raise APIError(
                f"Unsupported currency code '{code}'. Supported currencies: {sorted(list(ExchangeRateService.SUPPORTED_CURRENCIES))}",
                code="UNSUPPORTED_CURRENCY",
                status=400
            )
        return code

    @classmethod
    def record_exchange_rate(
        cls,
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessExchangeRate:
        """
        Records or updates an authoritative exchange rate for a currency pair and date.
        """
        ws = db.session.get(Workspace, workspace_id)
        if not ws:
            raise APIError("Workspace not found.", code="NOT_FOUND", status=404)

        from_curr = cls._normalize_currency(data.get('from_currency'))
        to_curr = cls._normalize_currency(data.get('to_currency', ws.base_currency))

        if from_curr == to_curr:
            raise APIError("From and To currencies must be distinct for exchange rate recording.", code="IDENTICAL_CURRENCIES", status=400)

        # Validate Rate
        raw_rate = data.get('rate')
        try:
            rate = Decimal(str(raw_rate)).quantize(Decimal('0.000001'))
        except (InvalidOperation, TypeError, ValueError):
            raise APIError("Exchange rate must be a valid positive decimal number.", code="INVALID_RATE", status=400)

        if rate <= Decimal('0.000000'):
            raise APIError("Exchange rate must be strictly greater than zero.", code="RATE_MUST_BE_POSITIVE", status=400)

        # Parse Effective Date
        raw_date = data.get('effective_date')
        if raw_date:
            try:
                eff_date = datetime.strptime(str(raw_date), '%Y-%m-%d').date()
            except ValueError:
                eff_date = datetime.now(timezone.utc).date()
        else:
            eff_date = datetime.now(timezone.utc).date()

        rate_source = data.get('rate_source', 'MANUAL_OVERRIDE')
        valid_sources = {'SYSTEM_DEFAULT', 'CENTRAL_BANK', 'CUSTOMS_RATE', 'MANUAL_OVERRIDE'}
        if rate_source not in valid_sources:
            rate_source = 'MANUAL_OVERRIDE'

        # Check existing rate for the date
        existing = BusinessExchangeRate.query.filter_by(
            workspace_id=workspace_id,
            from_currency=from_curr,
            to_currency=to_curr,
            effective_date=eff_date
        ).first()

        if existing:
            existing.rate = rate
            existing.rate_source = rate_source
            existing.notes = data.get('notes', existing.notes)
            existing.created_by_user_id = actor_user_id
            fx_record = existing
            action = 'EXCHANGE_RATE_UPDATED'
        else:
            fx_record = BusinessExchangeRate(
                workspace_id=workspace_id,
                from_currency=from_curr,
                to_currency=to_curr,
                rate=rate,
                effective_date=eff_date,
                rate_source=rate_source,
                notes=data.get('notes'),
                created_by_user_id=actor_user_id
            )
            db.session.add(fx_record)
            action = 'EXCHANGE_RATE_RECORDED'

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type='EXCHANGE_RATE',
            entity_id=fx_record.id,
            after_state=fx_record.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return fx_record

    @classmethod
    def get_exchange_rate(
        cls,
        workspace_id: str,
        from_currency: str,
        to_currency: str,
        effective_date: date = None,
        allow_lookback: bool = True
    ) -> Decimal:
        """
        Determines the authoritative exchange rate between two currencies.
        Supports 1:1 identity, direct rate lookup, 7-day historical lookback, and inverse pairs.
        """
        from_curr = cls._normalize_currency(from_currency)
        to_curr = cls._normalize_currency(to_currency)

        if from_curr == to_curr:
            return Decimal('1.000000')

        if effective_date is None:
            effective_date = datetime.now(timezone.utc).date()

        # 1. Direct rate on exact date
        rate_entry = BusinessExchangeRate.query.filter(
            BusinessExchangeRate.workspace_id == workspace_id,
            BusinessExchangeRate.from_currency == from_curr,
            BusinessExchangeRate.to_currency == to_curr,
            BusinessExchangeRate.effective_date == effective_date
        ).first()

        if rate_entry:
            return rate_entry.rate

        # 2. Lookback window up to 7 days
        if allow_lookback:
            start_date = effective_date - timedelta(days=7)
            recent_entry = BusinessExchangeRate.query.filter(
                BusinessExchangeRate.workspace_id == workspace_id,
                BusinessExchangeRate.from_currency == from_curr,
                BusinessExchangeRate.to_currency == to_curr,
                BusinessExchangeRate.effective_date <= effective_date,
                BusinessExchangeRate.effective_date >= start_date
            ).order_by(BusinessExchangeRate.effective_date.desc()).first()

            if recent_entry:
                return recent_entry.rate

        # 3. Check inverted pair (e.g. from INR to USD if USD to INR exists)
        inv_entry = BusinessExchangeRate.query.filter(
            BusinessExchangeRate.workspace_id == workspace_id,
            BusinessExchangeRate.from_currency == to_curr,
            BusinessExchangeRate.to_currency == from_curr,
            BusinessExchangeRate.effective_date <= effective_date,
            BusinessExchangeRate.effective_date >= (effective_date - timedelta(days=7) if allow_lookback else effective_date)
        ).order_by(BusinessExchangeRate.effective_date.desc()).first()

        if inv_entry and inv_entry.rate > Decimal('0.000000'):
            return (Decimal('1.0') / inv_entry.rate).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

        raise APIError(
            f"No exchange rate found for {from_curr} -> {to_curr} within 7 days of {effective_date.isoformat()}. Please record an exchange rate.",
            code="MISSING_EXCHANGE_RATE",
            status=400
        )

    @classmethod
    def convert_amount(
        cls,
        workspace_id: str,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        effective_date: date = None
    ) -> dict:
        """
        Converts an amount with exact Decimal precision and deterministic financial rounding.
        """
        try:
            amt = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise APIError("Amount must be a valid decimal number.", code="INVALID_AMOUNT", status=400)

        rate = cls.get_exchange_rate(workspace_id, from_currency, to_currency, effective_date)
        converted = (amt * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'original_amount': str(amt),
            'from_currency': from_currency.strip().upper(),
            'to_currency': to_currency.strip().upper(),
            'exchange_rate': str(rate),
            'effective_date': effective_date.isoformat() if effective_date else datetime.now(timezone.utc).date().isoformat(),
            'converted_amount': str(converted)
        }

    @classmethod
    def list_exchange_rates(
        cls,
        workspace_id: str,
        from_currency: str = None,
        to_currency: str = None,
        limit: int = 50
    ) -> list:
        query = BusinessExchangeRate.query.filter_by(workspace_id=workspace_id)
        if from_currency:
            query = query.filter_by(from_currency=from_currency.strip().upper())
        if to_currency:
            query = query.filter_by(to_currency=to_currency.strip().upper())
        rates = query.order_by(BusinessExchangeRate.effective_date.desc()).limit(limit).all()
        return [r.serialize() for r in rates]
