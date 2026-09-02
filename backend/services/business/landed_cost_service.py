"""
DeadlineOS Business OS — Landed Cost Service (Phase C3.4)
==========================================================
Encapsulates landed cost voucher lifecycle, multi-currency cost intake,
proportional value/quantity allocation, deterministic residual-cent rule,
voucher immutability, and reversal provenance.
"""

from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from database.db import db
from models.business import (
    Workspace,
    BusinessPurchaseOrder,
    BusinessGoodsReceipt,
    BusinessGoodsReceiptLine,
    BusinessProduct,
    BusinessLandedCostVoucher,
    BusinessLandedCostVoucherItem,
    BusinessLandedCostAllocation,
    AuditEvent
)
from services.business.exchange_rate_service import ExchangeRateService
from services.business.audit_service import AuditService
from utils.errors import APIError


class LandedCostService:
    """
    Core domain service for enterprise landed cost allocation.
    """
    VALID_CATEGORIES = {
        'FREIGHT', 'CUSTOMS', 'DUTIES', 'INSURANCE', 'HANDLING',
        'BROKERAGE', 'PORT_CHARGES', 'STORAGE', 'OTHER'
    }
    VALID_BASES = {'VALUE', 'QUANTITY'}

    @classmethod
    def _generate_voucher_number(cls, workspace_id: str) -> str:
        """Generates a monotonic, collision-free voucher number for the workspace."""
        today_str = datetime.now(timezone.utc).strftime('%Y%m')
        prefix = f"LCV-{today_str}-"
        last = BusinessLandedCostVoucher.query.filter(
            BusinessLandedCostVoucher.workspace_id == workspace_id,
            BusinessLandedCostVoucher.voucher_number.like(f"{prefix}%")
        ).order_by(BusinessLandedCostVoucher.voucher_number.desc()).first()

        if last and last.voucher_number.startswith(prefix):
            try:
                seq = int(last.voucher_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    def create_voucher(
        cls,
        workspace_id: str,
        actor_user_id: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessLandedCostVoucher:
        """
        Creates a new draft Landed Cost Voucher.
        """
        ws = db.session.get(Workspace, workspace_id)
        if not ws:
            raise APIError("Workspace not found.", code="WORKSPACE_NOT_FOUND", status=404)

        base_curr = ws.base_currency or 'INR'
        raw_curr = (data.get('currency') or base_curr).strip().upper()
        if raw_curr not in ExchangeRateService.SUPPORTED_CURRENCIES:
            raise APIError(f"Unsupported currency code '{raw_curr}'.", code="UNSUPPORTED_CURRENCY", status=400)

        # Parse Effective Date
        raw_date = data.get('effective_date')
        if raw_date:
            try:
                eff_date = datetime.strptime(str(raw_date).split('T')[0], '%Y-%m-%d').date()
            except ValueError:
                eff_date = datetime.now(timezone.utc).date()
        else:
            eff_date = datetime.now(timezone.utc).date()

        # Validate Exchange Rate
        if raw_curr == base_curr:
            fx_rate = Decimal('1.000000')
        else:
            if data.get('exchange_rate'):
                try:
                    fx_rate = Decimal(str(data['exchange_rate'])).quantize(Decimal('0.000001'))
                    if fx_rate <= Decimal('0.000000'):
                        raise ValueError()
                except (InvalidOperation, ValueError, TypeError):
                    raise APIError("Invalid exchange rate provided.", code="INVALID_RATE", status=400)
            else:
                fx_rate = ExchangeRateService.get_exchange_rate(workspace_id, raw_curr, base_curr, eff_date)

        # Validate Allocation Basis
        basis = (data.get('allocation_basis') or 'VALUE').strip().upper()
        if basis not in cls.VALID_BASES:
            raise APIError(f"Invalid allocation basis '{basis}'. Supported: {sorted(list(cls.VALID_BASES))}", code="INVALID_ALLOCATION_BASIS", status=400)

        # Validate optional PO link
        po_id = data.get('purchase_order_id')
        if po_id:
            po = BusinessPurchaseOrder.query.filter_by(id=po_id, workspace_id=workspace_id).first()
            if not po:
                raise APIError("Purchase Order not found in this workspace.", code="PO_NOT_FOUND", status=404)

        # Validate optional GRN link
        grn_id = data.get('goods_receipt_id')
        if grn_id:
            grn = BusinessGoodsReceipt.query.filter_by(id=grn_id, workspace_id=workspace_id).first()
            if not grn:
                raise APIError("Goods Receipt not found in this workspace.", code="GRN_NOT_FOUND", status=404)
            if not po_id:
                po_id = grn.purchase_order_id

        voucher_num = cls._generate_voucher_number(workspace_id)

        voucher = BusinessLandedCostVoucher(
            workspace_id=workspace_id,
            voucher_number=voucher_num,
            reference_number=data.get('reference_number'),
            purchase_order_id=po_id,
            goods_receipt_id=grn_id,
            currency=raw_curr,
            base_currency=base_curr,
            exchange_rate=fx_rate,
            effective_date=eff_date,
            allocation_basis=basis,
            status='DRAFT',
            notes=data.get('notes'),
            created_by_user_id=actor_user_id
        )
        db.session.add(voucher)
        db.session.flush()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LANDED_COST_VOUCHER_CREATED",
            entity_type="business_landed_cost_voucher",
            entity_id=voucher.id,
            after_state=voucher.serialize(),
            reason=f"Created Landed Cost Voucher {voucher_num} in DRAFT",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return voucher

    @classmethod
    def get_voucher(
        cls,
        workspace_id: str,
        voucher_id: str,
        include_items: bool = True,
        include_allocations: bool = True
    ) -> BusinessLandedCostVoucher:
        """
        Retrieves a Landed Cost Voucher by ID with workspace isolation.
        """
        voucher = BusinessLandedCostVoucher.query.filter_by(
            id=voucher_id,
            workspace_id=workspace_id
        ).first()
        if not voucher:
            raise APIError("Landed Cost Voucher not found in this workspace.", code="VOUCHER_NOT_FOUND", status=404)
        return voucher

    @classmethod
    def list_vouchers(
        cls,
        workspace_id: str,
        status: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        goods_receipt_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Lists and filters landed cost vouchers.
        """
        q = BusinessLandedCostVoucher.query.filter_by(workspace_id=workspace_id)
        if status:
            q = q.filter_by(status=status.strip().upper())
        if purchase_order_id:
            q = q.filter_by(purchase_order_id=purchase_order_id)
        if goods_receipt_id:
            q = q.filter_by(goods_receipt_id=goods_receipt_id)
        if search:
            s_term = f"%{search.strip()}%"
            q = q.filter(
                (BusinessLandedCostVoucher.voucher_number.ilike(s_term)) |
                (BusinessLandedCostVoucher.reference_number.ilike(s_term)) |
                (BusinessLandedCostVoucher.notes.ilike(s_term))
            )

        total = q.count()
        vouchers = q.order_by(BusinessLandedCostVoucher.created_at.desc()).offset(offset).limit(limit).all()
        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'vouchers': [v.serialize() for v in vouchers]
        }

    @classmethod
    def add_cost_item(
        cls,
        workspace_id: str,
        voucher_id: str,
        actor_user_id: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessLandedCostVoucherItem:
        """
        Adds an itemized cost expenditure to a DRAFT landed cost voucher.
        """
        voucher = cls.get_voucher(workspace_id, voucher_id)
        if not voucher.can_edit():
            raise APIError(f"Cannot add cost items to voucher in '{voucher.status}' status. Must be DRAFT.", code="VOUCHER_IMMUTABLE", status=400)

        cat = (data.get('cost_category') or '').strip().upper()
        if cat not in cls.VALID_CATEGORIES:
            raise APIError(f"Invalid cost category '{cat}'. Allowed: {sorted(list(cls.VALID_CATEGORIES))}", code="INVALID_COST_CATEGORY", status=400)

        desc = (data.get('description') or '').strip()
        if not desc:
            raise APIError("Field 'description' is required.", code="MISSING_DESCRIPTION", status=400)

        # Parse Amount
        try:
            amount = Decimal(str(data.get('amount'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if amount <= Decimal('0.00'):
                raise ValueError()
        except (InvalidOperation, TypeError, ValueError):
            raise APIError("Amount must be a strictly positive number.", code="INVALID_AMOUNT", status=400)

        # Currency & FX conversion
        curr = (data.get('currency') or voucher.currency).strip().upper()
        if curr not in ExchangeRateService.SUPPORTED_CURRENCIES:
            raise APIError(f"Unsupported currency '{curr}'.", code="UNSUPPORTED_CURRENCY", status=400)

        if curr == voucher.base_currency:
            fx_rate = Decimal('1.000000')
            base_amount = amount
        else:
            if data.get('exchange_rate'):
                try:
                    fx_rate = Decimal(str(data['exchange_rate'])).quantize(Decimal('0.000001'))
                    if fx_rate <= Decimal('0.000000'):
                        raise ValueError()
                except (InvalidOperation, ValueError, TypeError):
                    raise APIError("Invalid item exchange rate.", code="INVALID_RATE", status=400)
            else:
                fx_rate = ExchangeRateService.get_exchange_rate(workspace_id, curr, voucher.base_currency, voucher.effective_date)
            base_amount = (amount * fx_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        item = BusinessLandedCostVoucherItem(
            workspace_id=workspace_id,
            voucher_id=voucher.id,
            cost_category=cat,
            description=desc,
            amount=amount,
            currency=curr,
            exchange_rate=fx_rate,
            base_currency_amount=base_amount,
            external_reference=data.get('external_reference'),
            notes=data.get('notes')
        )
        db.session.add(item)
        db.session.flush()

        # Recalculate voucher totals
        cls._recalculate_voucher_totals(voucher)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LANDED_COST_ITEM_ADDED",
            entity_type="business_landed_cost_voucher_item",
            entity_id=item.id,
            after_state=item.serialize(),
            reason=f"Added {cat} cost ({curr} {amount} -> {voucher.base_currency} {base_amount}) to {voucher.voucher_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return item

    @classmethod
    def remove_cost_item(
        cls,
        workspace_id: str,
        voucher_id: str,
        item_id: str,
        actor_user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Removes a cost item from a DRAFT landed cost voucher.
        """
        voucher = cls.get_voucher(workspace_id, voucher_id)
        if not voucher.can_edit():
            raise APIError(f"Cannot remove cost items from voucher in '{voucher.status}' status. Must be DRAFT.", code="VOUCHER_IMMUTABLE", status=400)

        item = BusinessLandedCostVoucherItem.query.filter_by(
            id=item_id,
            voucher_id=voucher.id,
            workspace_id=workspace_id
        ).first()
        if not item:
            raise APIError("Cost item not found on this voucher.", code="ITEM_NOT_FOUND", status=404)

        prev_state = item.serialize()
        db.session.delete(item)
        db.session.flush()

        cls._recalculate_voucher_totals(voucher)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LANDED_COST_ITEM_REMOVED",
            entity_type="business_landed_cost_voucher_item",
            entity_id=item_id,
            before_state=prev_state,
            reason=f"Removed cost item {item_id} from {voucher.voucher_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

    @classmethod
    def _recalculate_voucher_totals(cls, voucher: BusinessLandedCostVoucher):
        """Re-aggregates total source and base currency sums across all items."""
        items = BusinessLandedCostVoucherItem.query.filter_by(voucher_id=voucher.id).all()
        total_base = sum((i.base_currency_amount for i in items), Decimal('0.00')).quantize(Decimal('0.01'))
        
        # Source total: if all items share voucher currency, sum them; otherwise calculate via exchange rate
        same_curr_items = [i for i in items if i.currency == voucher.currency]
        if len(same_curr_items) == len(items):
            total_source = sum((i.amount for i in items), Decimal('0.00')).quantize(Decimal('0.01'))
        else:
            total_source = (total_base / voucher.exchange_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        voucher.total_cost_base_currency = total_base
        voucher.total_cost_source_currency = total_source
        db.session.flush()

    @classmethod
    def _get_eligible_receipt_lines(cls, voucher: BusinessLandedCostVoucher) -> List[Dict[str, Any]]:
        """
        Resolves accepted physical delivery lines linked to the voucher's GRN or PO.
        """
        if voucher.goods_receipt_id:
            grn_lines = BusinessGoodsReceiptLine.query.filter_by(
                goods_receipt_id=voucher.goods_receipt_id
            ).all()
        elif voucher.purchase_order_id:
            # All GRN lines associated with approved receipts under this PO
            grn_lines = BusinessGoodsReceiptLine.query.join(
                BusinessGoodsReceipt, BusinessGoodsReceipt.id == BusinessGoodsReceiptLine.goods_receipt_id
            ).filter(
                BusinessGoodsReceipt.purchase_order_id == voucher.purchase_order_id,
                BusinessGoodsReceipt.status == 'COMPLETED'
            ).all()
        else:
            raise APIError("Landed cost voucher has neither a Goods Receipt nor a Purchase Order association.", code="NO_ASSOCIATED_PROCUREMENT", status=400)

        # Filter lines with accepted physical inventory
        eligible = []
        for line in grn_lines:
            acc_qty = Decimal(str(line.accepted_quantity))
            if acc_qty > Decimal('0.00'):
                unit_cost = Decimal(str(line.unit_cost))
                line_val = (acc_qty * unit_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                eligible.append({
                    'id': line.id,
                    'product_id': line.product_id,
                    'accepted_quantity': acc_qty,
                    'unit_cost': unit_cost,
                    'line_base_value': line_val,
                })

        if not eligible:
            raise APIError("No accepted physical receipt lines found for landed cost allocation.", code="NO_ACCEPTED_LINES", status=400)
        return eligible

    @classmethod
    def calculate_allocation(
        cls,
        total_cost: Decimal,
        lines: List[Dict[str, Any]],
        basis: str
    ) -> List[Dict[str, Any]]:
        """
        Deterministic proportional allocation engine with exact residual-cent rule.
        """
        total_cost = total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if total_cost <= Decimal('0.00'):
            raise APIError("Total allocatable cost must be strictly positive.", code="ZERO_OR_NEGATIVE_COST", status=400)

        if basis == 'QUANTITY':
            total_basis = sum((l['accepted_quantity'] for l in lines), Decimal('0.00'))
        else:  # 'VALUE'
            total_basis = sum((l['line_base_value'] for l in lines), Decimal('0.00'))

        if total_basis <= Decimal('0.00'):
            raise APIError(f"Total allocation basis ({basis}) is zero. Cannot apportion cost.", code="ZERO_ALLOCATION_BASIS", status=400)

        allocated_lines = []
        sum_rounded = Decimal('0.00')

        for idx, l in enumerate(lines):
            metric = l['accepted_quantity'] if basis == 'QUANTITY' else l['line_base_value']
            weight = (metric / total_basis).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
            raw_share = (total_cost * metric) / total_basis
            rounded_share = raw_share.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            sum_rounded += rounded_share

            qty = l['accepted_quantity']
            allocated_lines.append({
                'goods_receipt_line_id': l['id'],
                'product_id': l['product_id'],
                'accepted_quantity': qty,
                'line_base_value': l['line_base_value'],
                'allocation_weight': weight,
                'allocated_cost_base_currency': rounded_share,
                'metric': metric,
                'index': idx
            })

        # Deterministic residual-cent rule: Assign residual cents to largest-weight line (tiebreak: lowest index)
        residual = total_cost - sum_rounded
        if residual != Decimal('0.00'):
            target_line = min(allocated_lines, key=lambda x: (-x['metric'], x['index']))
            target_line['allocated_cost_base_currency'] += residual

        # Calculate per-unit landed cost
        for al in allocated_lines:
            qty = al['accepted_quantity']
            cost = al['allocated_cost_base_currency']
            al['landed_cost_per_unit'] = (cost / qty).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP) if qty > Decimal('0.00') else Decimal('0.0000')

        # Reconciliation assertion
        final_sum = sum((al['allocated_cost_base_currency'] for al in allocated_lines), Decimal('0.00'))
        if final_sum != total_cost:
            raise APIError(f"Allocation reconciliation failure: sum {final_sum} != total {total_cost}", code="RECONCILIATION_ERROR", status=500)

        return allocated_lines

    @classmethod
    def preview_allocation(
        cls,
        workspace_id: str,
        voucher_id: str,
        allocation_basis: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Previews line-level allocations without modifying database records.
        """
        voucher = cls.get_voucher(workspace_id, voucher_id, include_items=True)
        basis = (allocation_basis or voucher.allocation_basis or 'VALUE').strip().upper()
        if basis not in cls.VALID_BASES:
            raise APIError(f"Invalid allocation basis '{basis}'.", code="INVALID_ALLOCATION_BASIS", status=400)

        if voucher.total_cost_base_currency <= Decimal('0.00'):
            raise APIError("Voucher has no itemized costs to allocate.", code="ZERO_COST_VOUCHER", status=400)

        lines = cls._get_eligible_receipt_lines(voucher)
        allocations = cls.calculate_allocation(voucher.total_cost_base_currency, lines, basis)

        return {
            'voucher_id': voucher.id,
            'voucher_number': voucher.voucher_number,
            'allocation_basis': basis,
            'total_cost_base_currency': str(voucher.total_cost_base_currency),
            'line_count': len(allocations),
            'allocations': [
                {
                    'goods_receipt_line_id': a['goods_receipt_line_id'],
                    'product_id': a['product_id'],
                    'accepted_quantity': str(a['accepted_quantity']),
                    'line_base_value': str(a['line_base_value']),
                    'allocation_weight': str(a['allocation_weight']),
                    'allocated_cost_base_currency': str(a['allocated_cost_base_currency']),
                    'landed_cost_per_unit': str(a['landed_cost_per_unit']),
                }
                for a in allocations
            ]
        }

    @classmethod
    def execute_allocation(
        cls,
        workspace_id: str,
        voucher_id: str,
        actor_user_id: str,
        allocation_basis: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessLandedCostVoucher:
        """
        Persists authoritative line allocations and advances voucher to ALLOCATED.
        """
        # Row-level lock on voucher
        voucher = BusinessLandedCostVoucher.query.filter_by(
            id=voucher_id,
            workspace_id=workspace_id
        ).with_for_update().first()

        if not voucher:
            raise APIError("Landed Cost Voucher not found.", code="VOUCHER_NOT_FOUND", status=404)

        if not voucher.can_allocate():
            raise APIError(f"Voucher in status '{voucher.status}' cannot be allocated. Must be DRAFT or ALLOCATED.", code="VOUCHER_IMMUTABLE", status=400)

        basis = (allocation_basis or voucher.allocation_basis or 'VALUE').strip().upper()
        if basis not in cls.VALID_BASES:
            raise APIError(f"Invalid allocation basis '{basis}'.", code="INVALID_ALLOCATION_BASIS", status=400)

        # Ensure totals are accurate
        cls._recalculate_voucher_totals(voucher)
        if voucher.total_cost_base_currency <= Decimal('0.00'):
            raise APIError("Voucher has no itemized costs to allocate.", code="ZERO_COST_VOUCHER", status=400)

        lines = cls._get_eligible_receipt_lines(voucher)
        allocations_data = cls.calculate_allocation(voucher.total_cost_base_currency, lines, basis)

        # Clear prior allocations if re-allocating
        BusinessLandedCostAllocation.query.filter_by(voucher_id=voucher.id).delete()
        db.session.flush()

        # Persist derived allocations
        for ad in allocations_data:
            alloc = BusinessLandedCostAllocation(
                workspace_id=workspace_id,
                voucher_id=voucher.id,
                goods_receipt_line_id=ad['goods_receipt_line_id'],
                product_id=ad['product_id'],
                accepted_quantity=ad['accepted_quantity'],
                line_base_value=ad['line_base_value'],
                allocation_weight=ad['allocation_weight'],
                allocated_cost_base_currency=ad['allocated_cost_base_currency'],
                landed_cost_per_unit=ad['landed_cost_per_unit']
            )
            db.session.add(alloc)

        voucher.allocation_basis = basis
        voucher.allocated_total_base_currency = voucher.total_cost_base_currency
        voucher.status = 'ALLOCATED'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LANDED_COST_ALLOCATED",
            entity_type="business_landed_cost_voucher",
            entity_id=voucher.id,
            after_state=voucher.serialize(include_allocations=True),
            reason=f"Allocated {voucher.base_currency} {voucher.total_cost_base_currency} across {len(allocations_data)} lines via {basis}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return voucher

    @classmethod
    def approve_voucher(
        cls,
        workspace_id: str,
        voucher_id: str,
        actor_user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessLandedCostVoucher:
        """
        Formally approves a landed cost voucher, locking it into an immutable state.
        Restricted to OWNER and ADMIN.
        """
        voucher = BusinessLandedCostVoucher.query.filter_by(
            id=voucher_id,
            workspace_id=workspace_id
        ).with_for_update().first()

        if not voucher:
            raise APIError("Landed Cost Voucher not found.", code="VOUCHER_NOT_FOUND", status=404)

        if voucher.status == 'APPROVED':
            raise APIError("Voucher is already approved and immutable.", code="VOUCHER_ALREADY_APPROVED", status=400)

        if voucher.status != 'ALLOCATED':
            raise APIError(f"Only ALLOCATED vouchers can be approved. Current status: '{voucher.status}'.", code="INVALID_VOUCHER_STATUS", status=400)

        if voucher.allocated_total_base_currency != voucher.total_cost_base_currency:
            raise APIError("Allocated total does not match total landed cost. Re-allocation required.", code="ALLOCATION_MISMATCH", status=400)

        voucher.status = 'APPROVED'
        voucher.approved_by_user_id = actor_user_id
        voucher.approved_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LANDED_COST_APPROVED",
            entity_type="business_landed_cost_voucher",
            entity_id=voucher.id,
            after_state=voucher.serialize(),
            reason=f"Approved Landed Cost Voucher {voucher.voucher_number} ({voucher.base_currency} {voucher.total_cost_base_currency})",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return voucher

    @classmethod
    def reverse_voucher(
        cls,
        workspace_id: str,
        voucher_id: str,
        actor_user_id: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessLandedCostVoucher:
        """
        Reverses an approved Landed Cost Voucher with full provenance.
        Restricted to OWNER and ADMIN.
        """
        voucher = BusinessLandedCostVoucher.query.filter_by(
            id=voucher_id,
            workspace_id=workspace_id
        ).with_for_update().first()

        if not voucher:
            raise APIError("Landed Cost Voucher not found.", code="VOUCHER_NOT_FOUND", status=404)

        if not voucher.can_reverse():
            raise APIError(f"Only APPROVED vouchers can be reversed. Current status: '{voucher.status}'.", code="VOUCHER_NOT_REVERSIBLE", status=400)

        if not reason or not reason.strip():
            raise APIError("Reversal reason is mandatory.", code="MISSING_REVERSAL_REASON", status=400)

        voucher.status = 'REVERSED'
        voucher.reversal_reason = reason.strip()
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LANDED_COST_REVERSED",
            entity_type="business_landed_cost_voucher",
            entity_id=voucher.id,
            after_state=voucher.serialize(),
            reason=f"Reversed Landed Cost Voucher {voucher.voucher_number}. Reason: {reason.strip()}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return voucher
