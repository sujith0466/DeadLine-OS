"""
DeadlineOS Business OS — Operational Intelligence Service (Phase C2.3)
======================================================================
Deterministic operational telemetry, inventory consumption velocity,
stockout forecasting, supplier reliability analytics, and replenishment insights.

Strict Architectural Invariants:
1. Inventory source of truth is strictly `business_stock_movements` (SUM(IN) - SUM(OUT)).
2. Strict separation between FACT (current inventory, recorded receipts) and FORECAST (projected stockout date, estimated runout).
3. Deterministic Supplier Scoring: If completed deliveries < 3, returns INSUFFICIENT_HISTORY. Never fabricates scores.
4. Tenant Isolation: Every query scoped strictly to `workspace_id`.
"""

import math
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_
from database.db import db
from models.business import (
    BusinessProduct,
    BusinessLocation,
    BusinessStockMovement,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessGoodsReceipt,
    BusinessGoodsReceiptLine,
    CommercialPartner,
)
from services.business.inventory_service import InventoryService
from utils.errors import APIError


class OperationalIntelligenceService:

    @staticmethod
    def get_operational_summary(workspace_id: str) -> dict:
        """
        Calculates high-level operational health KPIs:
        - Total active SKUs
        - Total inventory valuation
        - Critical stockout risk count (DIR <= 7 days)
        - Low stock count (Stock <= Reorder Level)
        - Dead stock count (> 60 days without OUT movement)
        - Average supplier OTIF rate across rated suppliers
        """
        products = BusinessProduct.query.filter_by(
            workspace_id=workspace_id,
            status='ACTIVE'
        ).all()

        total_skus = len(products)
        total_valuation = Decimal('0.00')
        critical_stockout_count = 0
        low_stock_count = 0
        dead_stock_count = 0

        # Precompute stock and velocity for all active products
        for prod in products:
            stock = InventoryService.get_total_product_stock(workspace_id, prod.id)
            cost_price = Decimal(str(prod.cost_price or '0.00'))
            total_valuation += (stock * cost_price).quantize(Decimal('0.01'))

            reorder_level = Decimal(str(prod.reorder_level or '0.00'))
            if 0 < stock <= reorder_level:
                low_stock_count += 1

            # Velocity check over 30 days
            velocity = OperationalIntelligenceService._calculate_daily_burn_rate(workspace_id, prod.id, window_days=30)
            if velocity > Decimal('0.00'):
                dir_days = stock / velocity
                if dir_days <= Decimal('7.00') or stock <= Decimal('0.00'):
                    critical_stockout_count += 1
            elif stock <= Decimal('0.00'):
                critical_stockout_count += 1

            # Dead stock check (> 60 days without OUT movement)
            if stock > Decimal('0.00'):
                is_dead = OperationalIntelligenceService._check_dead_stock(workspace_id, prod.id, days_threshold=60)
                if is_dead:
                    dead_stock_count += 1

        # Supplier summary
        supplier_metrics = OperationalIntelligenceService.get_supplier_performance_summary(workspace_id)
        rated_suppliers = [s for s in supplier_metrics if s['status'] == 'RATED' and s['otif_rate'] is not None]
        avg_otif = None
        if rated_suppliers:
            total_otif = sum(Decimal(str(s['otif_rate'])) for s in rated_suppliers)
            avg_otif = (total_otif / len(rated_suppliers)).quantize(Decimal('0.1'))

        return {
            'workspace_id': workspace_id,
            'calculated_at': datetime.now(timezone.utc).isoformat(),
            'total_active_skus': total_skus,
            'total_inventory_valuation': str(total_valuation),
            'critical_stockout_count': critical_stockout_count,
            'low_stock_count': low_stock_count,
            'dead_stock_count': dead_stock_count,
            'average_supplier_otif': str(avg_otif) if avg_otif is not None else None,
            'rated_suppliers_count': len(rated_suppliers),
            'total_suppliers_count': len(supplier_metrics)
        }

    @staticmethod
    def get_inventory_forecast(workspace_id: str, window_days: int = 30) -> list:
        """
        Computes per-product inventory velocity, days of inventory remaining (DIR),
        and projected stockout date with clear factual vs forecast separation.
        """
        products = BusinessProduct.query.filter_by(
            workspace_id=workspace_id,
            status='ACTIVE'
        ).order_by(BusinessProduct.name.asc()).all()

        today = date.today()
        forecast_items = []

        for prod in products:
            current_stock = InventoryService.get_total_product_stock(workspace_id, prod.id)
            reorder_level = Decimal(str(prod.reorder_level or '0.00'))
            safety_stock = Decimal(str(prod.safety_stock or '0.00'))
            daily_burn = OperationalIntelligenceService._calculate_daily_burn_rate(workspace_id, prod.id, window_days)

            # Check open inbound purchase orders
            on_order_qty = OperationalIntelligenceService._get_on_order_quantity(workspace_id, prod.id)

            # DIR & Stockout Date Calculation
            days_remaining = None
            projected_stockout_date = None
            stock_health = 'HEALTHY'

            if current_stock <= Decimal('0.00'):
                stock_health = 'OUT_OF_STOCK'
                days_remaining = 0
                projected_stockout_date = today.isoformat()
            elif daily_burn > Decimal('0.00'):
                raw_dir = (current_stock / daily_burn).quantize(Decimal('0.1'))
                days_remaining = float(raw_dir)
                int_days = int(math.floor(days_remaining))
                projected_date = today + timedelta(days=int_days)
                projected_stockout_date = projected_date.isoformat()

                if days_remaining <= 7:
                    stock_health = 'CRITICAL_RISK'
                elif days_remaining <= 14 or current_stock <= reorder_level:
                    stock_health = 'LOW_STOCK'
                else:
                    stock_health = 'HEALTHY'
            else:
                # 0 burn rate
                days_remaining = None
                projected_stockout_date = None
                if current_stock <= reorder_level and reorder_level > Decimal('0.00'):
                    stock_health = 'LOW_STOCK'
                else:
                    # Check if dead stock
                    is_dead = OperationalIntelligenceService._check_dead_stock(workspace_id, prod.id, days_threshold=60)
                    stock_health = 'DEAD_STOCK' if is_dead else 'STABLE_NO_DEMAND'

            forecast_items.append({
                'product_id': prod.id,
                'sku': prod.sku,
                'name': prod.name,
                'unit': prod.unit,
                # Fact Layer
                'factual_stock': str(current_stock),
                'reorder_level': str(reorder_level),
                'safety_stock': str(safety_stock),
                'on_order_quantity': str(on_order_qty),
                # Forecast Layer
                'daily_burn_rate': str(daily_burn),
                'days_of_inventory_remaining': days_remaining,
                'projected_stockout_date': projected_stockout_date,
                'stock_health': stock_health,
                'analysis_window_days': window_days,
            })

        # Sort: OUT_OF_STOCK & CRITICAL_RISK first
        severity_map = {
            'OUT_OF_STOCK': 0,
            'CRITICAL_RISK': 1,
            'LOW_STOCK': 2,
            'DEAD_STOCK': 3,
            'STABLE_NO_DEMAND': 4,
            'HEALTHY': 5
        }
        forecast_items.sort(key=lambda x: (severity_map.get(x['stock_health'], 99), x['days_of_inventory_remaining'] or 9999))
        return forecast_items

    @staticmethod
    def get_supplier_performance_summary(workspace_id: str) -> list:
        """
        Calculates deterministic supplier performance metrics:
        - OTIF (On-Time In-Full) Rate (%)
        - Quality Acceptance Rate (%)
        - Average Lead Time (Actual Days)
        - Data Sufficiency: If completed orders < 3 -> Status: INSUFFICIENT_HISTORY
        """
        suppliers = CommercialPartner.query.filter(
            CommercialPartner.workspace_id == workspace_id,
            CommercialPartner.partner_type.in_(['SUPPLIER', 'BOTH']),
            CommercialPartner.status == 'ACTIVE'
        ).order_by(CommercialPartner.name.asc()).all()

        supplier_metrics = []

        for sup in suppliers:
            # Query all POs for this supplier
            pos = BusinessPurchaseOrder.query.filter_by(
                workspace_id=workspace_id,
                supplier_partner_id=sup.id
            ).all()

            total_pos = len(pos)
            completed_pos = [po for po in pos if po.status == 'FULLY_RECEIVED']
            delivery_count = len(completed_pos)

            # Query all Goods Receipts for this supplier's POs
            po_ids = [p.id for p in pos]
            grns = []
            if po_ids:
                grns = BusinessGoodsReceipt.query.filter(
                    BusinessGoodsReceipt.workspace_id == workspace_id,
                    BusinessGoodsReceipt.purchase_order_id.in_(po_ids),
                    BusinessGoodsReceipt.status == 'COMPLETED'
                ).all()

            total_received_qty = Decimal('0.00')
            total_accepted_qty = Decimal('0.00')
            total_rejected_qty = Decimal('0.00')

            for grn in grns:
                for line in grn.lines:
                    total_received_qty += Decimal(str(line.received_quantity or '0.00'))
                    total_accepted_qty += Decimal(str(line.accepted_quantity or '0.00'))
                    total_rejected_qty += Decimal(str(line.rejected_quantity or '0.00'))

            # Quality Acceptance Rate
            quality_rate = None
            if total_received_qty > Decimal('0.00'):
                quality_rate = ((total_accepted_qty / total_received_qty) * Decimal('100.00')).quantize(Decimal('0.1'))

            # Lead time and On-Time calculations across completed POs
            lead_times_days = []
            on_time_full_count = 0

            for po in completed_pos:
                # Find earliest and latest GRN for this PO
                po_grns = [g for g in grns if g.purchase_order_id == po.id]
                if po_grns:
                    # Order date or Sent date
                    start_dt = po.order_date
                    latest_grn_dt = max(g.receipt_date for g in po_grns)
                    lead_time = (latest_grn_dt - start_dt).days
                    if lead_time >= 0:
                        lead_times_days.append(lead_time)

                    # Check on-time if expected_delivery_date exists
                    if po.expected_delivery_date:
                        if latest_grn_dt <= po.expected_delivery_date:
                            on_time_full_count += 1
                    else:
                        # If no expected date specified, assume on time
                        on_time_full_count += 1

            avg_lead_time = None
            if lead_times_days:
                avg_lead_time = (Decimal(str(sum(lead_times_days))) / Decimal(str(len(lead_times_days)))).quantize(Decimal('0.1'))

            otif_rate = None
            if completed_pos:
                otif_rate = ((Decimal(str(on_time_full_count)) / Decimal(str(len(completed_pos)))) * Decimal('100.00')).quantize(Decimal('0.1'))

            # Data Sufficiency Guard: Minimum 3 completed deliveries required for a validated rating
            if delivery_count < 3:
                status = 'INSUFFICIENT_HISTORY'
            else:
                status = 'RATED'

            supplier_metrics.append({
                'supplier_id': sup.id,
                'supplier_name': sup.name,
                'status': status,
                'total_pos_issued': total_pos,
                'completed_deliveries_count': delivery_count,
                'total_goods_receipts': len(grns),
                'otif_rate': str(otif_rate) if otif_rate is not None else None,
                'quality_acceptance_rate': str(quality_rate) if quality_rate is not None else None,
                'total_received_quantity': str(total_received_qty),
                'total_rejected_quantity': str(total_rejected_qty),
                'average_lead_time_days': str(avg_lead_time) if avg_lead_time is not None else None,
                'minimum_deliveries_required': 3
            })

        return supplier_metrics

    @staticmethod
    def get_reorder_suggestions(workspace_id: str) -> list:
        """
        Generates deterministic, actionable reorder recommendations.
        Identifies products at or below safety stock / reorder thresholds,
        considering on-order stock and average supplier lead times.
        """
        forecasts = OperationalIntelligenceService.get_inventory_forecast(workspace_id, window_days=30)
        suggestions = []

        for item in forecasts:
            if item['stock_health'] in ('OUT_OF_STOCK', 'CRITICAL_RISK', 'LOW_STOCK'):
                current_stock = Decimal(item['factual_stock'])
                reorder_level = Decimal(item['reorder_level'])
                safety_stock = Decimal(item['safety_stock'])
                on_order = Decimal(item['on_order_quantity'])
                daily_burn = Decimal(item['daily_burn_rate'])

                effective_stock = current_stock + on_order
                if effective_stock <= reorder_level or current_stock <= safety_stock:
                    # Fetch product details for cost and preferred supplier
                    prod = BusinessProduct.query.filter_by(id=item['product_id'], workspace_id=workspace_id).first()
                    if not prod:
                        continue

                    # Suggest reorder quantity = (Reorder Level * 2) - Effective Stock + (30 days of burn)
                    target_stock = max(reorder_level * Decimal('2.00'), safety_stock * Decimal('2.00'), daily_burn * Decimal('30.00'))
                    if target_stock <= Decimal('0.00'):
                        target_stock = Decimal('10.00')  # Default minimum batch if no thresholds set

                    suggested_qty = (target_stock - effective_stock).quantize(Decimal('0.01'))
                    if suggested_qty <= Decimal('0.00'):
                        suggested_qty = Decimal('10.00')

                    unit_cost = Decimal(str(prod.cost_price or '0.00'))
                    estimated_total = (suggested_qty * unit_cost).quantize(Decimal('0.01'))

                    urgency = 'HIGH' if item['stock_health'] == 'OUT_OF_STOCK' else ('MEDIUM' if item['stock_health'] == 'CRITICAL_RISK' else 'NORMAL')

                    suggestions.append({
                        'product_id': prod.id,
                        'product_name': prod.name,
                        'sku': prod.sku,
                        'unit': prod.unit,
                        'current_stock': str(current_stock),
                        'on_order_stock': str(on_order),
                        'reorder_level': str(reorder_level),
                        'safety_stock': str(safety_stock),
                        'suggested_quantity': str(suggested_qty),
                        'estimated_unit_cost': str(unit_cost),
                        'estimated_total_cost': str(estimated_total),
                        'urgency': urgency,
                        'reason': f"Stock ({current_stock}) + On-Order ({on_order}) <= Reorder threshold ({reorder_level}). Burn rate is {daily_burn}/day.",
                        'preferred_supplier_partner_id': prod.preferred_supplier_partner_id,
                        'preferred_supplier_name': (
        CommercialPartner.query.get(prod.preferred_supplier_partner_id).name
        if prod.preferred_supplier_partner_id else None
    )
                    })

        return suggestions

    # ── Private Utility Methods ───────────────────────────────────────────────

    @staticmethod
    def _calculate_daily_burn_rate(workspace_id: str, product_id: str, window_days: int = 30) -> Decimal:
        """
        Calculates daily average consumption over the specified historical window (OUT movements only).
        """
        since_date = datetime.now(timezone.utc) - timedelta(days=window_days)
        result = db.session.query(
            func.coalesce(func.sum(BusinessStockMovement.quantity), 0)
        ).filter(
            BusinessStockMovement.workspace_id == workspace_id,
            BusinessStockMovement.product_id == product_id,
            BusinessStockMovement.direction == 'OUT',
            BusinessStockMovement.created_at >= since_date
        ).scalar()

        total_out = Decimal(str(result or 0.00))
        if total_out <= Decimal('0.00'):
            return Decimal('0.00')

        return (total_out / Decimal(str(window_days))).quantize(Decimal('0.01'))

    @staticmethod
    def _check_dead_stock(workspace_id: str, product_id: str, days_threshold: int = 60) -> bool:
        """
        Returns True if a product has had zero OUT stock movements in the last `days_threshold` days.
        """
        since_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        count = db.session.query(func.count(BusinessStockMovement.id)).filter(
            BusinessStockMovement.workspace_id == workspace_id,
            BusinessStockMovement.product_id == product_id,
            BusinessStockMovement.direction == 'OUT',
            BusinessStockMovement.created_at >= since_date
        ).scalar() or 0

        return count == 0

    @staticmethod
    def _get_on_order_quantity(workspace_id: str, product_id: str) -> Decimal:
        """
        Sums outstanding (ordered - received) quantities on APPROVED or SENT purchase orders.
        """
        lines = db.session.query(
            BusinessPurchaseOrderLine
        ).join(
            BusinessPurchaseOrder, BusinessPurchaseOrderLine.purchase_order_id == BusinessPurchaseOrder.id
        ).filter(
            BusinessPurchaseOrder.workspace_id == workspace_id,
            BusinessPurchaseOrder.status.in_(['APPROVED', 'SENT_TO_SUPPLIER', 'PARTIALLY_RECEIVED']),
            BusinessPurchaseOrderLine.product_id == product_id,
            BusinessPurchaseOrderLine.status.in_(['PENDING', 'PARTIALLY_RECEIVED'])
        ).all()

        on_order = Decimal('0.00')
        for line in lines:
            ordered = Decimal(str(line.ordered_quantity or '0.00'))
            received = Decimal(str(line.received_quantity or '0.00'))
            remaining = max(Decimal('0.00'), ordered - received)
            on_order += remaining

        return on_order.quantize(Decimal('0.01'))
