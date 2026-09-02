"""
DeadlineOS Business OS — Financial & Operational Converter Gateway
==================================================================
Bridges human-confirmed StagedExtractions into authoritative Invoices,
BusinessTransactions, Stock Movements, or Business Tasks.
"""

from database.db import db
from models.business import StagedExtraction
from services.business.invoice_service import InvoiceService
from services.business.transaction_service import TransactionService
from services.business.inventory_service import InventoryService
from services.business.task_service import TaskService
from services.business.purchase_request_service import PurchaseRequestService
from utils.errors import APIError


class FinancialConverterService:
    @staticmethod
    def commit_staged_item(
        workspace_id: str,
        staging_id: str,
        user_id: str,
        target_domain: str = None,  # INVOICE, TRANSACTION, INVENTORY, TASK, STOCK_TRANSFER, PURCHASE_REQUEST
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        staged = StagedExtraction.query.filter_by(id=staging_id, workspace_id=workspace_id).first()
        if not staged:
            raise APIError("Staged extraction not found.", code="STAGING_ITEM_NOT_FOUND", status=404)
        if staged.status != 'CONFIRMED':
            raise APIError(f"Cannot commit extraction in status '{staged.status}'. Must be CONFIRMED by reviewer first.", code="ITEM_NOT_CONFIRMED", status=400)

        norm = staged.normalized_data or {}

        # Determine target domain
        if target_domain:
            target = target_domain.upper()
        elif staged.candidate_type in ('INVOICE_RECEIVABLE', 'INVOICE_PAYABLE'):
            target = 'INVOICE'
        elif staged.candidate_type in ('INVENTORY_ADJUSTMENT', 'VOICE_INVENTORY_ADJUSTMENT'):
            target = 'INVENTORY'
        elif staged.candidate_type in ('STOCK_TRANSFER', 'VOICE_STOCK_TRANSFER'):
            target = 'STOCK_TRANSFER'
        elif staged.candidate_type in ('PURCHASE_REQUEST', 'VOICE_PURCHASE_REQUEST'):
            target = 'PURCHASE_REQUEST'
        elif staged.candidate_type in ('TASK', 'VOICE_TASK'):
            target = 'TASK'
        else:
            target = 'TRANSACTION'

        if target == 'INVOICE':
            inv_type = 'RECEIVABLE' if staged.candidate_type == 'INVOICE_RECEIVABLE' else 'PAYABLE'
            inv = InvoiceService.create_invoice(
                workspace_id=workspace_id,
                user_id=user_id,
                data={
                    'invoice_type': inv_type,
                    'partner_id': norm.get('partner_id'),
                    'issue_date': norm.get('date'),
                    'due_date': norm.get('date'),
                    'currency': norm.get('currency', 'INR'),
                    'subtotal': norm.get('amount', '0.00'),
                    'notes': norm.get('description')
                },
                staged_extraction_id=staged.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'INVOICE', 'entity': inv.serialize()}

        elif target == 'INVENTORY':
            movement = InventoryService.record_stock_movement(
                workspace_id=workspace_id,
                actor_user_id=user_id,
                data={
                    'product_id': norm.get('product_id'),
                    'location_id': norm.get('location_id'),
                    'movement_type': norm.get('movement_type', 'MANUAL_ADJUSTMENT'),
                    'direction': norm.get('direction', 'IN'),
                    'quantity': norm.get('quantity', '1.00'),
                    'unit_cost': norm.get('unit_cost'),
                    'reason': norm.get('description') or norm.get('reason') or "Committed from human-confirmed staged extraction"
                },
                staged_extraction_id=staged.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'INVENTORY', 'entity': movement.serialize()}

        elif target == 'STOCK_TRANSFER':
            transfer_res = InventoryService.transfer_stock(
                workspace_id=workspace_id,
                actor_user_id=user_id,
                data={
                    'product_id': norm.get('product_id'),
                    'source_location_id': norm.get('source_location_id'),
                    'destination_location_id': norm.get('destination_location_id'),
                    'quantity': norm.get('quantity', '1.00'),
                    'notes': norm.get('reason') or f"Transferred via {staged.source_channel} extraction"
                },
                staged_extraction_id=staged.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'STOCK_TRANSFER', 'entity': transfer_res}

        elif target == 'PURCHASE_REQUEST':
            pr = PurchaseRequestService.create_purchase_request(
                workspace_id=workspace_id,
                actor_user_id=user_id,
                data={
                    'product_id': norm.get('product_id'),
                    'quantity': norm.get('quantity', '1.00'),
                    'estimated_unit_cost': norm.get('estimated_unit_cost', '0.00'),
                    'required_by_date': norm.get('required_by_date'),
                    'supplier_partner_id': norm.get('supplier_partner_id'),
                    'destination_location_id': norm.get('destination_location_id'),
                    'notes': norm.get('notes') or f"Requisition from {staged.source_channel} extraction"
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'PURCHASE_REQUEST', 'entity': pr.serialize()}

        elif target == 'TASK':
            task = TaskService.create_task(
                workspace_id=workspace_id,
                actor_user_id=user_id,
                data={
                    'title': norm.get('title') or norm.get('description') or 'Operational Task',
                    'description': norm.get('description'),
                    'priority': norm.get('priority', 'MEDIUM'),
                    'category': norm.get('category', 'GENERAL'),
                    'assignee_member_id': norm.get('assignee_member_id'),
                    'due_date': norm.get('due_date'),
                    'notes': f"Extracted via channel {staged.source_channel}"
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'TASK', 'entity': task.serialize()}

        else:
            tx = TransactionService.record_transaction(
                workspace_id=workspace_id,
                user_id=user_id,
                data={
                    'transaction_type': 'INCOME' if staged.candidate_type == 'INVOICE_RECEIVABLE' else 'EXPENSE',
                    'amount': norm.get('amount', '0.00'),
                    'currency': norm.get('currency', 'INR'),
                    'transaction_date': norm.get('date'),
                    'partner_id': norm.get('partner_id'),
                    'notes': norm.get('description')
                },
                staged_extraction_id=staged.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'TRANSACTION', 'entity': tx.serialize()}
