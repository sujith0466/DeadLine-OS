"""
DeadlineOS Business OS — Accountant Export Engine
=================================================
Generates deterministic CSV ledger streams and cryptographically-hashed
ZIP archive packages for accounting reconciliation.
"""

from database.db import db
from datetime import datetime, timezone, date
from decimal import Decimal
from models.business import Invoice, BusinessTransaction, PaymentAllocation, Workspace
from services.business.financial_truth_service import FinancialTruthService
from services.business.audit_service import AuditService
from utils.errors import APIError
import io
import csv
import json
import zipfile
import hashlib


def sanitize_csv_cell(val) -> str:
    """Escapes formula injection trigger prefixes (=, +, -, @, \t, \r)."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + s
    return s


class ExportService:
    @staticmethod
    def export_invoices_csv(workspace_id: str, start_date: date = None, end_date: date = None) -> str:
        query = Invoice.query.filter_by(workspace_id=workspace_id)
        if start_date:
            query = query.filter(Invoice.issue_date >= start_date)
        if end_date:
            query = query.filter(Invoice.issue_date <= end_date)

        invoices = query.order_by(Invoice.issue_date.asc()).all()

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow([
            'Invoice ID', 'Invoice Number', 'Type', 'Partner Name', 'Issue Date',
            'Due Date', 'Currency', 'Subtotal', 'Tax Amount', 'Discount Amount',
            'Total Amount', 'Paid Amount', 'Balance Due', 'Status'
        ])

        for inv in invoices:
            writer.writerow([
                sanitize_csv_cell(inv.id),
                sanitize_csv_cell(inv.invoice_number),
                sanitize_csv_cell(inv.invoice_type),
                sanitize_csv_cell(inv.partner.name if inv.partner else ""),
                sanitize_csv_cell(inv.issue_date.isoformat() if inv.issue_date else ""),
                sanitize_csv_cell(inv.due_date.isoformat() if inv.due_date else ""),
                sanitize_csv_cell(inv.currency),
                f"{Decimal(str(inv.subtotal)):.2f}",
                f"{Decimal(str(inv.tax_amount)):.2f}",
                f"{Decimal(str(inv.discount_amount)):.2f}",
                f"{Decimal(str(inv.total_amount)):.2f}",
                f"{Decimal(str(inv.paid_amount)):.2f}",
                f"{Decimal(str(inv.balance_due)):.2f}",
                sanitize_csv_cell(inv.status),
            ])

        return output.getvalue()

    @staticmethod
    def export_transactions_csv(workspace_id: str, start_date: date = None, end_date: date = None) -> str:
        query = BusinessTransaction.query.filter_by(workspace_id=workspace_id)
        if start_date:
            query = query.filter(BusinessTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(BusinessTransaction.transaction_date <= end_date)

        txs = query.order_by(BusinessTransaction.transaction_date.asc()).all()

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow([
            'Transaction ID', 'Type', 'Amount', 'Currency', 'Transaction Date',
            'Settlement Date', 'Partner Name', 'Payment Method', 'Reference Number',
            'Status', 'Notes'
        ])

        for t in txs:
            writer.writerow([
                sanitize_csv_cell(t.id),
                sanitize_csv_cell(t.transaction_type),
                f"{Decimal(str(t.amount)):.2f}",
                sanitize_csv_cell(t.currency),
                sanitize_csv_cell(t.transaction_date.isoformat() if t.transaction_date else ""),
                sanitize_csv_cell(t.settlement_date.isoformat() if t.settlement_date else ""),
                sanitize_csv_cell(t.partner.name if t.partner else ""),
                sanitize_csv_cell(t.payment_method),
                sanitize_csv_cell(t.reference_number or ""),
                sanitize_csv_cell(t.status),
                sanitize_csv_cell(t.notes or ""),
            ])

        return output.getvalue()

    @staticmethod
    def export_allocations_csv(workspace_id: str, start_date: date = None, end_date: date = None) -> str:
        query = PaymentAllocation.query.filter_by(workspace_id=workspace_id)
        allocations = query.order_by(PaymentAllocation.created_at.asc()).all()

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow([
            'Allocation ID', 'Transaction ID', 'Invoice ID', 'Invoice Number',
            'Allocated Amount', 'Status', 'Notes', 'Created At'
        ])

        for a in allocations:
            writer.writerow([
                sanitize_csv_cell(a.id),
                sanitize_csv_cell(a.transaction_id),
                sanitize_csv_cell(a.invoice_id),
                sanitize_csv_cell(a.invoice.invoice_number if a.invoice else ""),
                f"{Decimal(str(a.allocated_amount)):.2f}",
                sanitize_csv_cell(a.status),
                sanitize_csv_cell(a.notes or ""),
                sanitize_csv_cell(a.created_at.isoformat() if a.created_at else ""),
            ])

        return output.getvalue()

    @staticmethod
    def generate_accountant_package(
        workspace_id: str,
        user_id: str,
        start_date: date = None,
        end_date: date = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> tuple[bytes, str]:
        # 1. Generate CSV content
        invoices_csv = ExportService.export_invoices_csv(workspace_id, start_date, end_date)
        transactions_csv = ExportService.export_transactions_csv(workspace_id, start_date, end_date)
        allocations_csv = ExportService.export_allocations_csv(workspace_id, start_date, end_date)

        # 2. Generate financial summary
        cash_pos = FinancialTruthService.get_cash_position(workspace_id, window_days=30)
        runway = FinancialTruthService.calculate_runway_days(workspace_id)
        summary_data = {
            'workspace_id': workspace_id,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'confirmed_cash': cash_pos['confirmed_cash'],
            'committed_inflows': cash_pos['committed_inflows'],
            'committed_outflows': cash_pos['committed_outflows'],
            'projected_position': cash_pos['projected_position'],
            'runway_state': runway['state'],
            'runway_days': runway['runway_days'],
        }
        summary_json = json.dumps(summary_data, indent=2)

        # 3. Calculate SHA-256 hashes
        inv_hash = hashlib.sha256(invoices_csv.encode('utf-8')).hexdigest()
        tx_hash = hashlib.sha256(transactions_csv.encode('utf-8')).hexdigest()
        alloc_hash = hashlib.sha256(allocations_csv.encode('utf-8')).hexdigest()
        summary_hash = hashlib.sha256(summary_json.encode('utf-8')).hexdigest()

        # 4. Manifest
        manifest = {
            'workspace_id': workspace_id,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'generated_by_user_id': user_id,
            'filter_date_range': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'file_checksums': {
                'invoices_export.csv': f"sha256:{inv_hash}",
                'transactions_export.csv': f"sha256:{tx_hash}",
                'payment_allocations_export.csv': f"sha256:{alloc_hash}",
                'financial_summary.json': f"sha256:{summary_hash}"
            }
        }
        manifest_json = json.dumps(manifest, indent=2)

        # 5. Build in-memory ZIP archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('manifest.json', manifest_json)
            zipf.writestr('invoices_export.csv', invoices_csv)
            zipf.writestr('transactions_export.csv', transactions_csv)
            zipf.writestr('payment_allocations_export.csv', allocations_csv)
            zipf.writestr('financial_summary.json', summary_json)

        zip_bytes = zip_buffer.getvalue()
        package_sha256 = hashlib.sha256(zip_bytes).hexdigest()

        # 6. Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='ACCOUNTANT_PACKAGE_EXPORTED',
            entity_type='EXPORT_PACKAGE',
            entity_id=package_sha256[:16],
            after_state={'package_sha256': package_sha256, 'file_checksums': manifest['file_checksums']},
            ip_address=ip_address,
            user_agent=user_agent
        )

        filename = f"accountant_package_{workspace_id[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
        return zip_bytes, filename
