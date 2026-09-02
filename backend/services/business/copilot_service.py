"""
DeadlineOS Business OS — Business Copilot Service (Phase C2.6)
=============================================================
Zero-Bypass Conversational AI Assistant grounded strictly in verified
deterministic financial AND operational intelligence telemetry.
"""

from database.db import db
from datetime import datetime, timezone, date
from decimal import Decimal
from models.business import (
    Invoice,
    BusinessTransaction,
    CommercialPartner,
    BusinessPurchaseOrder,
    BusinessGoodsReceipt,
    BusinessOperationalAlert,
    BusinessTask,
)
from services.business.financial_truth_service import FinancialTruthService
from services.business.invoice_service import InvoiceService
from services.business.transaction_service import TransactionService
from services.business.operational_intelligence_service import OperationalIntelligenceService
from services.business.operational_alert_service import OperationalAlertService
from services.business.audit_service import AuditService
from services.ai.provider import get_default_ai_provider
from utils.errors import APIError
import json


class CopilotService:
    @staticmethod
    def assemble_context(workspace_id: str) -> dict:
        """
        Assembles comprehensive deterministic financial and operational telemetry.
        """
        # ── 1. Financial Context ──────────────────────────────────────────────
        cash_pos = FinancialTruthService.get_cash_position(workspace_id, window_days=30)
        runway = FinancialTruthService.calculate_runway_days(workspace_id)

        invoices, _ = InvoiceService.get_invoices(workspace_id, invoice_type='RECEIVABLE', limit=5)
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

        payables, _ = InvoiceService.get_invoices(workspace_id, invoice_type='PAYABLE', limit=5)
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

        # ── 2. Operational Intelligence Context ───────────────────────────────
        try:
            op_summary = OperationalIntelligenceService.get_operational_summary(workspace_id)
            inv_forecast = OperationalIntelligenceService.get_inventory_forecast(workspace_id, window_days=30)
            forecast_list = inv_forecast if isinstance(inv_forecast, list) else inv_forecast.get('forecasts', [])
            reorder_sugg = OperationalIntelligenceService.get_reorder_suggestions(workspace_id)
            supplier_perf = OperationalIntelligenceService.get_supplier_performance_summary(workspace_id)
        except Exception:
            op_summary = {}
            forecast_list = []
            reorder_sugg = []
            supplier_perf = {}

        # ── 3. Procurement & Purchase Orders ──────────────────────────────────
        open_pos = BusinessPurchaseOrder.query.filter(
            BusinessPurchaseOrder.workspace_id == workspace_id,
            BusinessPurchaseOrder.status.in_(['APPROVED', 'SENT_TO_SUPPLIER', 'PARTIALLY_RECEIVED'])
        ).limit(5).all()

        overdue_po_count = BusinessPurchaseOrder.query.filter(
            BusinessPurchaseOrder.workspace_id == workspace_id,
            BusinessPurchaseOrder.status.in_(['APPROVED', 'SENT_TO_SUPPLIER', 'PARTIALLY_RECEIVED']),
            BusinessPurchaseOrder.expected_delivery_date < date.today()
        ).count()

        # ── 4. Operational Alerts Telemetry ───────────────────────────────────
        active_alerts = BusinessOperationalAlert.query.filter(
            BusinessOperationalAlert.workspace_id == workspace_id,
            BusinessOperationalAlert.status.in_(['ACTIVE', 'ACKNOWLEDGED'])
        ).order_by(BusinessOperationalAlert.created_at.desc()).limit(5).all()

        return {
            'workspace_id': workspace_id,
            'current_date': date.today().isoformat(),
            'currency': 'INR',
            # Financial Truth
            'confirmed_cash': cash_pos['confirmed_cash'],
            'committed_inflows': cash_pos['committed_inflows'],
            'committed_outflows': cash_pos['committed_outflows'],
            'projected_position': cash_pos['projected_position'],
            'runway_state': runway['state'],
            'runway_days': runway['runway_days'],
            'open_receivables': open_receivables,
            'open_payables': open_payables,
            # Operational Truth
            'operational_summary': {
                'total_active_skus': op_summary.get('total_active_skus', 0),
                'total_inventory_valuation': op_summary.get('total_inventory_valuation', '0.00'),
                'dead_stock_valuation': op_summary.get('dead_stock_valuation', '0.00'),
                'overall_otif_percentage': op_summary.get('overall_otif_percentage', 0.0),
            },
            'inventory_risks': {
                'critical_risk_items': len([f for f in forecast_list if f.get('stockout_risk') == 'CRITICAL_RISK']),
                'warning_risk_items': len([f for f in forecast_list if f.get('stockout_risk') == 'WARNING']),
                'reorder_suggestions_count': len(reorder_sugg),
                'top_reorders': reorder_sugg[:3]
            },
            'procurement_status': {
                'open_po_count': len(open_pos),
                'overdue_po_count': overdue_po_count,
                'open_pos': [
                    {'po_number': po.po_number, 'amount': str(po.total_amount), 'expected_delivery': str(po.expected_delivery_date), 'status': po.status}
                    for po in open_pos
                ]
            },
            'active_operational_alerts': [
                {'type': a.alert_type, 'severity': a.severity, 'title': a.title, 'status': a.status}
                for a in active_alerts
            ]
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

        # 1. Assemble verified financial & operational context
        context = CopilotService.assemble_context(workspace_id)

        system_instruction = """You are the DeadlineOS Business Financial & Operational Copilot. You assist business owners, operational managers, and founders with clear, actionable insights based strictly on their verified operational numbers and financial reality.

MANDATORY RULES:
1. CITE THE EXACT FIGURES provided in the Verified Context (cash, inventory valuation, stockout risks, open POs, alerts). Do not invent or estimate numbers.
2. State all currency amounts in Indian Rupees (INR / ₹).
3. If asked about inventory, procurement, suppliers, or alerts, cite the grounded operational metrics.
4. If asked about runway or cash reality, cite confirmed cash and deterministic runway days.
5. Provide structured, executive-ready advice with actionable recommendations.
6. Return your answer as a JSON object matching this schema:
{
  "summary": "Direct, concise answer to the question",
  "insights": ["Key factual bullet point 1", "Key factual bullet point 2"],
  "suggested_actions": [
    {"title": "Action title", "action_type": "ALERT | REORDER | TASK | REVIEW", "details": "Description"}
  ]
}"""

        user_content = f"""User Question: {prompt.strip()}

Verified Financial & Operational Context:
{json.dumps(context, indent=2)}"""

        # 2. Call AI provider with fallback
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
            critical_risks = context['inventory_risks']['critical_risk_items']
            overdue_pos = context['procurement_status']['overdue_po_count']
            response_text = json.dumps({
                "summary": f"Confirmed Cash: ₹{context['confirmed_cash']} ({context['runway_days'] or 'calculating'} runway days). Active Inventory Valuation: ₹{context['operational_summary']['total_inventory_valuation']}.",
                "insights": [
                    f"Stockout critical risks: {critical_risks} items",
                    f"Overdue purchase orders: {overdue_pos} POs",
                    f"Active operational alerts: {len(context['active_operational_alerts'])}"
                ],
                "suggested_actions": [
                    {"title": "Review Stockout Alerts", "action_type": "ALERT", "details": "Address items with imminent stockout risk in the Operations hub."}
                ]
            })

        # 3. Parse JSON or wrap safely
        parsed_result = None
        try:
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
                "insights": [
                    f"Inventory Valuation: ₹{context['operational_summary']['total_inventory_valuation']}",
                    f"Active Alerts: {len(context['active_operational_alerts'])}"
                ],
                "suggested_actions": []
            }

        # 4. Log audit event
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
                'runway_days': context['runway_days'],
                'inventory_valuation': context['operational_summary']['total_inventory_valuation'],
                'critical_stockout_risks': context['inventory_risks']['critical_risk_items'],
                'overdue_pos': context['procurement_status']['overdue_po_count'],
                'active_alerts_count': len(context['active_operational_alerts'])
            }
        }
