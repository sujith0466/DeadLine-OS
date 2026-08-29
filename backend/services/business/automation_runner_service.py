"""
DeadlineOS Business OS — Automation Runner Service
==================================================
Idempotent batch execution runner for recurring financial generation.
"""

from database.db import db
from datetime import datetime, timezone, date
from decimal import Decimal
from models.business import RecurringObligation, AutomationExecutionLog
from services.business.recurring_obligation_service import RecurringObligationService
from services.business.invoice_service import InvoiceService
from services.business.audit_service import AuditService
from utils.errors import APIError


class AutomationRunnerService:
    @staticmethod
    def trigger_obligation(
        workspace_id: str,
        user_id: str,
        obligation_id: str,
        target_date: date = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        obligation = RecurringObligation.query.filter_by(id=obligation_id, workspace_id=workspace_id).first()
        if not obligation:
            raise APIError("Recurring obligation not found.", code="OBLIGATION_NOT_FOUND", status=404)

        if obligation.status != 'ACTIVE':
            raise APIError(f"Cannot trigger obligation in {obligation.status} status.", code="OBLIGATION_NOT_ACTIVE", status=400)

        exec_date = target_date or obligation.next_due_date

        # 1. Check cycle idempotency
        existing_log = AutomationExecutionLog.query.filter_by(
            workspace_id=workspace_id,
            obligation_id=obligation_id,
            execution_date=exec_date,
            status='SUCCESS'
        ).first()

        if existing_log:
            return {
                'status': 'SKIPPED',
                'message': f"Execution for date {exec_date.isoformat()} already completed.",
                'log_id': existing_log.id,
                'entity_id': existing_log.generated_entity_id
            }

        # 2. Generate invoice if obligation is RECEIVABLE or PAYABLE
        generated_id = None
        generated_type = None

        if obligation.obligation_type in ('RECEIVABLE', 'PAYABLE'):
            invoice_res = InvoiceService.create_invoice(
                workspace_id=workspace_id,
                user_id=user_id,
                data={
                    'invoice_type': obligation.obligation_type,
                    'partner_id': obligation.partner_id,
                    'issue_date': exec_date.isoformat(),
                    'due_date': exec_date.isoformat(),
                    'currency': obligation.currency,
                    'total_amount': str(obligation.amount),
                    'items': [{
                        'description': f"Recurring {obligation.title} ({obligation.frequency})",
                        'quantity': '1',
                        'unit_price': str(obligation.amount)
                    }]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            generated_id = invoice_res.id
            generated_type = 'INVOICE'

        # 3. Advance next due date
        next_due = RecurringObligationService.calculate_next_due_date(exec_date, obligation.frequency)
        if obligation.end_date and next_due > obligation.end_date:
            obligation.status = 'COMPLETED'
        obligation.next_due_date = next_due

        # 4. Record execution log
        log = AutomationExecutionLog(
            workspace_id=workspace_id,
            obligation_id=obligation.id,
            execution_type='INVOICE_GENERATION' if generated_type == 'INVOICE' else 'STATUS_CHECK',
            execution_date=exec_date,
            status='SUCCESS',
            generated_entity_type=generated_type,
            generated_entity_id=generated_id,
            details=f"Generated {generated_type or 'obligation'} for cycle {exec_date.isoformat()}."
        )
        db.session.add(log)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='AUTOMATION_EXECUTED',
            entity_type='AUTOMATION_RUNNER',
            entity_id=log.id,
            after_state={'obligation_id': obligation.id, 'generated_id': generated_id, 'next_due_date': next_due.isoformat()},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            'status': 'SUCCESS',
            'log_id': log.id,
            'obligation_id': obligation.id,
            'generated_entity_type': generated_type,
            'generated_entity_id': generated_id,
            'next_due_date': next_due.isoformat()
        }

    @staticmethod
    def run_batch_automations(workspace_id: str, user_id: str, as_of_date: date = None) -> dict:
        target_today = as_of_date or date.today()

        obligations = RecurringObligation.query.filter(
            RecurringObligation.workspace_id == workspace_id,
            RecurringObligation.status == 'ACTIVE',
            RecurringObligation.auto_generate == True,
            RecurringObligation.next_due_date <= target_today
        ).all()

        results = []
        for obl in obligations:
            try:
                res = AutomationRunnerService.trigger_obligation(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    obligation_id=obl.id,
                    target_date=obl.next_due_date
                )
                results.append(res)
            except Exception as e:
                results.append({
                    'status': 'FAILED',
                    'obligation_id': obl.id,
                    'error': str(e)
                })

        return {
            'workspace_id': workspace_id,
            'as_of_date': target_today.isoformat(),
            'executed_count': len(results),
            'results': results
        }

    @staticmethod
    def get_execution_logs(workspace_id: str, obligation_id: str = None, limit: int = 50) -> list:
        query = AutomationExecutionLog.query.filter_by(workspace_id=workspace_id)
        if obligation_id:
            query = query.filter_by(obligation_id=obligation_id)
        return [l.to_dict() for l in query.order_by(AutomationExecutionLog.created_at.desc()).limit(limit).all()]
