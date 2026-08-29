"""
DeadlineOS Business OS — Collection Reminder Service
====================================================
Generates tone-aware payment reminders with human-in-the-loop review.
"""

from database.db import db
from datetime import datetime, timezone, date
from decimal import Decimal
from models.business import Invoice, CollectionReminder
from services.business.audit_service import AuditService
from services.ai.provider import get_default_ai_provider
from utils.errors import APIError
import json


class ReminderService:
    @staticmethod
    def draft_reminder(
        workspace_id: str,
        user_id: str,
        invoice_id: str,
        tone: str = 'POLITE',
        ip_address: str = None,
        user_agent: str = None
    ) -> CollectionReminder:
        valid_tones = {'GENTLE', 'POLITE', 'URGENT', 'LEGAL'}
        tone_normalized = tone.upper() if tone else 'POLITE'
        if tone_normalized not in valid_tones:
            tone_normalized = 'POLITE'

        invoice = Invoice.query.filter_by(id=invoice_id, workspace_id=workspace_id).first()
        if not invoice:
            raise APIError("Invoice not found in workspace.", code="INVOICE_NOT_FOUND", status=404)

        if invoice.status == 'VOID':
            raise APIError("Cannot draft reminder for a void invoice.", code="INVOICE_VOID", status=400)

        balance = Decimal(str(invoice.balance_due))
        if balance <= Decimal('0.00'):
            raise APIError("Invoice has zero balance due.", code="INVOICE_PAID", status=400)

        today = date.today()
        days_overdue = max(0, (today - invoice.due_date).days)
        partner_name = invoice.partner.name if invoice.partner else "Valued Client"
        recipient_email = invoice.partner.email if invoice.partner else None

        # Build grounded prompt
        system_instruction = f"""You are a professional credit management assistant for DeadlineOS Business OS.
Synthesize a payment reminder email for an overdue invoice.

MANDATORY RULES:
1. Tone must be strictly: {tone_normalized}.
2. Use EXACT facts: Invoice #{invoice.invoice_number}, Amount Due: ₹{balance:.2f}, Due Date: {invoice.due_date.isoformat()}, Days Overdue: {days_overdue}.
3. DO NOT invent late fees, interest, or arbitrary legal claims.
4. Output a JSON object with schema:
{{
  "subject": "Email subject line",
  "message_body": "Full professional email body"
}}"""

        user_content = f"Draft a {tone_normalized} reminder to {partner_name} for invoice #{invoice.invoice_number} with balance ₹{balance:.2f} overdue by {days_overdue} days."

        provider = get_default_ai_provider()
        subject = f"Payment Reminder: Invoice #{invoice.invoice_number}"
        message_body = f"Dear {partner_name},\n\nThis is a friendly reminder that invoice #{invoice.invoice_number} for ₹{balance:.2f} was due on {invoice.due_date.isoformat()}.\n\nPlease arrange payment at your earliest convenience.\n\nThank you."

        try:
            res = provider.generate(prompt=user_content, system_instruction=system_instruction, temperature=0.2)
            raw = res.get('text', '') if isinstance(res, dict) else str(res)
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            subject = parsed.get('subject', subject)
            message_body = parsed.get('message_body', message_body)
        except Exception:
            pass

        reminder = CollectionReminder(
            workspace_id=workspace_id,
            invoice_id=invoice_id,
            partner_id=invoice.partner_id,
            tone=tone_normalized,
            subject=subject,
            message_body=message_body,
            recipient_email=recipient_email,
            status='DRAFT',
            created_by_user_id=user_id
        )
        db.session.add(reminder)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='REMINDER_DRAFTED',
            entity_type='COLLECTION_REMINDER',
            entity_id=reminder.id,
            after_state={'invoice_id': invoice_id, 'tone': tone_normalized, 'status': 'DRAFT'},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return reminder

    @staticmethod
    def send_reminder(
        workspace_id: str,
        user_id: str,
        reminder_id: str,
        custom_message: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> CollectionReminder:
        reminder = CollectionReminder.query.filter_by(id=reminder_id, workspace_id=workspace_id).first()
        if not reminder:
            raise APIError("Collection reminder not found.", code="REMINDER_NOT_FOUND", status=404)

        if reminder.status != 'DRAFT':
            raise APIError(f"Cannot dispatch reminder in {reminder.status} status.", code="INVALID_STATE_TRANSITION", status=400)

        if custom_message and custom_message.strip():
            reminder.message_body = custom_message.strip()

        reminder.status = 'SENT'
        reminder.sent_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='REMINDER_DISPATCHED',
            entity_type='COLLECTION_REMINDER',
            entity_id=reminder.id,
            before_state={'status': 'DRAFT'},
            after_state={'status': 'SENT', 'sent_at': reminder.sent_at.isoformat()},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return reminder

    @staticmethod
    def get_reminders(workspace_id: str, invoice_id: str = None) -> list:
        query = CollectionReminder.query.filter_by(workspace_id=workspace_id)
        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)
        return [r.to_dict() for r in query.order_by(CollectionReminder.created_at.desc()).all()]
