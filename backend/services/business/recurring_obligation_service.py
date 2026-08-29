"""
DeadlineOS Business OS — Recurring Obligation Service
=====================================================
Manages recurring contracts, retainer schedules, and deterministic due-date stepping.
"""

from database.db import db
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
import calendar
from models.business import RecurringObligation, CommercialPartner
from services.business.audit_service import AuditService
from utils.errors import APIError


class RecurringObligationService:
    @staticmethod
    def calculate_next_due_date(current_date: date, frequency: str) -> date:
        """
        Calculates the next due date using deterministic calendar step mathematics
        with explicit month-end day clamping (e.g. Jan 31 -> Feb 28).
        """
        freq = frequency.upper()
        if freq == 'WEEKLY':
            return current_date + timedelta(days=7)
        elif freq == 'BIWEEKLY':
            return current_date + timedelta(days=14)
        elif freq == 'MONTHLY':
            year = current_date.year
            month = current_date.month + 1
            if month > 12:
                month = 1
                year += 1
            max_day = calendar.monthrange(year, month)[1]
            day = min(current_date.day, max_day)
            return date(year, month, day)
        elif freq == 'QUARTERLY':
            year = current_date.year
            month = current_date.month + 3
            while month > 12:
                month -= 12
                year += 1
            max_day = calendar.monthrange(year, month)[1]
            day = min(current_date.day, max_day)
            return date(year, month, day)
        elif freq == 'ANNUALLY':
            year = current_date.year + 1
            month = current_date.month
            max_day = calendar.monthrange(year, month)[1]
            day = min(current_date.day, max_day)
            return date(year, month, day)
        else:
            return current_date + timedelta(days=30)

    @staticmethod
    def create_obligation(workspace_id: str, user_id: str, data: dict, ip_address: str = None, user_agent: str = None) -> RecurringObligation:
        title = data.get('title')
        obligation_type = data.get('obligation_type')
        frequency = data.get('frequency', 'MONTHLY')
        amount_raw = data.get('amount')
        start_date_str = data.get('start_date')
        partner_id = data.get('partner_id')
        notes = data.get('notes')
        auto_generate = data.get('auto_generate', True)

        if not title or not title.strip():
            raise APIError("Title is required.", code="MISSING_TITLE", status=400)
        if obligation_type not in ('RECEIVABLE', 'PAYABLE', 'TAX_COMPLIANCE', 'PAYROLL'):
            raise APIError("Invalid obligation_type.", code="INVALID_OBLIGATION_TYPE", status=400)
        if frequency not in ('WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUALLY'):
            raise APIError("Invalid frequency.", code="INVALID_FREQUENCY", status=400)

        try:
            amount = Decimal(str(amount_raw))
            if amount <= Decimal('0.00'):
                raise ValueError()
        except Exception:
            raise APIError("Amount must be a positive decimal.", code="INVALID_AMOUNT", status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
        except Exception:
            raise APIError("Invalid start_date format (YYYY-MM-DD).", code="INVALID_DATE", status=400)

        end_date = None
        if data.get('end_date'):
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except Exception:
                raise APIError("Invalid end_date format (YYYY-MM-DD).", code="INVALID_DATE", status=400)

        if partner_id:
            partner = CommercialPartner.query.filter_by(id=partner_id, workspace_id=workspace_id).first()
            if not partner:
                raise APIError("Partner not found in workspace.", code="PARTNER_NOT_FOUND", status=404)

        obligation = RecurringObligation(
            workspace_id=workspace_id,
            partner_id=partner_id,
            title=title.strip(),
            obligation_type=obligation_type,
            frequency=frequency,
            amount=amount,
            currency=data.get('currency', 'INR'),
            start_date=start_date,
            end_date=end_date,
            next_due_date=start_date,
            auto_generate=auto_generate,
            status='ACTIVE',
            notes=notes,
            created_by_user_id=user_id
        )
        db.session.add(obligation)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='RECURRING_OBLIGATION_CREATED',
            entity_type='RECURRING_OBLIGATION',
            entity_id=obligation.id,
            after_state=obligation.to_dict(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return obligation

    @staticmethod
    def get_obligations(workspace_id: str, obligation_type: str = None, status: str = None) -> list:
        query = RecurringObligation.query.filter_by(workspace_id=workspace_id)
        if obligation_type:
            query = query.filter_by(obligation_type=obligation_type)
        if status:
            query = query.filter_by(status=status)
        return [o.to_dict() for o in query.order_by(RecurringObligation.next_due_date.asc()).all()]

    @staticmethod
    def get_obligation(workspace_id: str, obligation_id: str) -> RecurringObligation:
        obligation = RecurringObligation.query.filter_by(id=obligation_id, workspace_id=workspace_id).first()
        if not obligation:
            raise APIError("Recurring obligation not found.", code="OBLIGATION_NOT_FOUND", status=404)
        return obligation

    @staticmethod
    def pause_obligation(workspace_id: str, user_id: str, obligation_id: str, ip_address: str = None, user_agent: str = None) -> RecurringObligation:
        obligation = RecurringObligationService.get_obligation(workspace_id, obligation_id)
        if obligation.status != 'ACTIVE':
            raise APIError(f"Cannot pause obligation in {obligation.status} status.", code="INVALID_STATE", status=400)
        obligation.status = 'PAUSED'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='RECURRING_OBLIGATION_PAUSED',
            entity_type='RECURRING_OBLIGATION',
            entity_id=obligation.id,
            after_state={'status': 'PAUSED'},
            ip_address=ip_address,
            user_agent=user_agent
        )
        return obligation

    @staticmethod
    def resume_obligation(workspace_id: str, user_id: str, obligation_id: str, ip_address: str = None, user_agent: str = None) -> RecurringObligation:
        obligation = RecurringObligationService.get_obligation(workspace_id, obligation_id)
        if obligation.status != 'PAUSED':
            raise APIError(f"Cannot resume obligation in {obligation.status} status.", code="INVALID_STATE", status=400)
        obligation.status = 'ACTIVE'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='RECURRING_OBLIGATION_RESUMED',
            entity_type='RECURRING_OBLIGATION',
            entity_id=obligation.id,
            after_state={'status': 'ACTIVE'},
            ip_address=ip_address,
            user_agent=user_agent
        )
        return obligation

    @staticmethod
    def cancel_obligation(workspace_id: str, user_id: str, obligation_id: str, ip_address: str = None, user_agent: str = None) -> RecurringObligation:
        obligation = RecurringObligationService.get_obligation(workspace_id, obligation_id)
        obligation.status = 'CANCELLED'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='RECURRING_OBLIGATION_CANCELLED',
            entity_type='RECURRING_OBLIGATION',
            entity_id=obligation.id,
            after_state={'status': 'CANCELLED'},
            ip_address=ip_address,
            user_agent=user_agent
        )
        return obligation
