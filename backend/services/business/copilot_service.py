"""
DeadlineOS Business OS — Business Copilot Service
=================================================
Zero-Bypass Conversational AI Assistant grounded strictly in verified
deterministic financial facts.
"""

from database.db import db
from datetime import datetime, timezone, date
from decimal import Decimal
from models.business import Invoice, BusinessTransaction, CommercialPartner
from services.business.financial_truth_service import FinancialTruthService
from services.business.invoice_service import InvoiceService
from services.business.transaction_service import TransactionService
from services.business.audit_service import AuditService
from services.ai.provider import get_default_ai_provider
from utils.errors import APIError
import json


class CopilotService:
    @staticmethod
    def assemble_context(workspace_id: str) -> dict:
        """
        Assembles deterministic, verified financial context for the workspace.
        """
        # 1. Real-time cash position & runway
        cash_pos = FinancialTruthService.get_cash_position(workspace_id, window_days=30)
        runway = FinancialTruthService.calculate_runway_days(workspace_id)

        # 2. Outstanding Receivables
        invoices, _ = InvoiceService.get_invoices(workspace_id, invoice_type='RECEIVABLE', limit=10)
        open_receivables = [
            {
                'invoice_number': inv['invoice_number'],
                'partner_name': inv['partner_name'] or 'Unknown Client',
                'balance_due': inv['balance_due'],
                'due_date': inv['due_date'],
                'status': inv['status']
            }
            for inv in invoices if inv['status'] in ('ISSUED', 'PARTIALLY_PAID', 'OVERDUE')
        ]

        # 3. Outstanding Payables
        payables, _ = InvoiceService.get_invoices(workspace_id, invoice_type='PAYABLE', limit=10)
        open_payables = [
            {
                'invoice_number': inv['invoice_number'],
                'partner_name': inv['partner_name'] or 'Unknown Vendor',
                'balance_due': inv['balance_due'],
                'due_date': inv['due_date'],
                'status': inv['status']
            }
            for inv in payables if inv['status'] in ('ISSUED', 'PARTIALLY_PAID', 'OVERDUE')
        ]

        # 4. Recent Transactions
        txs, _ = TransactionService.get_transactions(workspace_id, limit=5)
        recent_txs = [
            {
                'type': t['transaction_type'],
                'amount': t['amount'],
                'date': t['transaction_date'],
                'partner_name': t['partner_name'] or 'General'
            }
            for t in txs
        ]

        return {
            'workspace_id': workspace_id,
            'current_date': date.today().isoformat(),
            'currency': 'INR',
            'confirmed_cash': cash_pos['confirmed_cash'],
            'committed_inflows': cash_pos['committed_inflows'],
            'committed_outflows': cash_pos['committed_outflows'],
            'projected_position': cash_pos['projected_position'],
            'runway_state': runway['state'],
            'runway_days': runway['runway_days'],
            'open_receivables': open_receivables,
            'open_payables': open_payables,
            'recent_transactions': recent_txs
        }

    @staticmethod
    def ask_copilot(
        workspace_id: str,
        user_id: str,
        prompt: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        if not prompt or not prompt.strip():
            raise APIError("Prompt cannot be empty.", code="EMPTY_PROMPT", status=400)

        # 1. Assemble verified financial context
        context = CopilotService.assemble_context(workspace_id)

        system_instruction = """You are the DeadlineOS Business Financial Copilot. You assist business owners and founders with clear, actionable insights based strictly on their verified operational financial numbers.

MANDATORY RULES:
1. CITE THE EXACT FIGURES provided in the Verified Financial Context. Do not invent or estimate numbers.
2. State all currency amounts in Indian Rupees (INR / ₹).
3. If asked about runway or cash reality, cite the provided confirmed cash and deterministic runway days.
4. Provide structured, executive-ready advice with actionable recommendations.
5. Return your answer as a JSON object matching this schema:
{
  "summary": "Direct, concise answer to the question",
  "insights": ["Key financial bullet point 1", "Key financial bullet point 2"],
  "suggested_actions": [
    {"title": "Action title", "action_type": "REMINDER | REVIEW | STAGE", "details": "Description"}
  ]
}"""

        user_content = f"""User Question: {prompt.strip()}

Verified Financial Context:
{json.dumps(context, indent=2)}"""

        # 3. Call AI provider with fallback
        provider = get_default_ai_provider()
        response_text = ""
        try:
            res = provider.generate(
                prompt=user_content,
                system_instruction=system_instruction,
                temperature=0.1
            )
            response_text = res.get('text', '') if isinstance(res, dict) else str(res)
        except Exception:
            # Fallback deterministic response
            response_text = json.dumps({
                "summary": f"Your current Confirmed Cash is ₹{context['confirmed_cash']} with {context['runway_days'] or 'calculating'} runway days.",
                "insights": [
                    f"Committed inflows: ₹{context['committed_inflows']}",
                    f"Committed outflows: ₹{context['committed_outflows']}"
                ],
                "suggested_actions": []
            })

        # 4. Parse JSON or wrap safely
        parsed_result = None
        try:
            # Strip markdown fences if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed_result = json.loads(cleaned.strip())
        except Exception:
            parsed_result = {
                "summary": response_text.strip() or f"Confirmed Cash: ₹{context['confirmed_cash']}",
                "insights": [f"Projected Position: ₹{context['projected_position']}"],
                "suggested_actions": []
            }

        # 5. Log audit event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='COPILOT_QUERY',
            entity_type='COPILOT',
            entity_id='query',
            before_state={'prompt': prompt.strip()},
            after_state={'summary': parsed_result.get('summary')},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            'query': prompt.strip(),
            'response': parsed_result,
            'context_summary': {
                'confirmed_cash': context['confirmed_cash'],
                'projected_position': context['projected_position'],
                'runway_days': context['runway_days']
            }
        }
