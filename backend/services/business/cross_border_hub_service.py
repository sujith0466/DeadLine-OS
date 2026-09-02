"""
DeadlineOS Business OS — Cross-Border Hub Service (Phase C3.5)
===============================================================
Unified operational intelligence and correlation engine for cross-border
procurement, international freight, customs clearance, receiving,
batches, serial numbers, landed costs, and deterministic event timelines.
"""

from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from database.db import db
from models.business import (
    Workspace,
    CommercialPartner,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessGoodsReceipt,
    BusinessGoodsReceiptLine,
    BusinessStockMovement,
    BusinessBatch,
    BusinessSerialNumber,
    BusinessLandedCostVoucher,
    BusinessLandedCostAllocation,
    BusinessCrossBorderShipment,
    AuditEvent
)
from services.business.audit_service import AuditService
from services.business.inventory_service import InventoryService
from utils.errors import APIError


class CrossBorderHubService:
    """
    Core domain service for cross-border operations and correlation.
    """
    VALID_STATUSES = {'PLANNED', 'BOOKED', 'IN_TRANSIT', 'CUSTOMS_HOLD', 'CUSTOMS_CLEARED', 'DELIVERED', 'CANCELLED'}
    VALID_CUSTOMS_STATUSES = {'PENDING', 'SUBMITTED', 'INSPECTION', 'CLEARED', 'REJECTED'}
    VALID_MODES = {'OCEAN', 'AIR', 'ROAD', 'RAIL', 'MULTIMODAL'}

    ALLOWED_STATUS_TRANSITIONS = {
        'PLANNED': {'BOOKED', 'CANCELLED'},
        'BOOKED': {'IN_TRANSIT', 'CANCELLED'},
        'IN_TRANSIT': {'CUSTOMS_HOLD', 'CUSTOMS_CLEARED', 'DELIVERED', 'CANCELLED'},
        'CUSTOMS_HOLD': {'CUSTOMS_CLEARED', 'CANCELLED'},
        'CUSTOMS_CLEARED': {'DELIVERED', 'CANCELLED'},
        'DELIVERED': set(),
        'CANCELLED': set()
    }

    ALLOWED_CUSTOMS_TRANSITIONS = {
        'PENDING': {'SUBMITTED', 'INSPECTION', 'CLEARED', 'REJECTED'},
        'SUBMITTED': {'INSPECTION', 'CLEARED', 'REJECTED'},
        'INSPECTION': {'CLEARED', 'REJECTED'},
        'CLEARED': set(),
        'REJECTED': set()
    }

    @classmethod
    def _generate_shipment_number(cls, workspace_id: str) -> str:
        today_str = datetime.now(timezone.utc).strftime('%Y%m')
        prefix = f"SHP-{today_str}-"
        last = BusinessCrossBorderShipment.query.filter(
            BusinessCrossBorderShipment.workspace_id == workspace_id,
            BusinessCrossBorderShipment.shipment_number.like(f"{prefix}%")
        ).order_by(BusinessCrossBorderShipment.shipment_number.desc()).first()

        if last and last.shipment_number.startswith(prefix):
            try:
                seq = int(last.shipment_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    def create_shipment(
        cls,
        workspace_id: str,
        actor_user_id: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessCrossBorderShipment:
        """
        Creates an operational cross-border shipment record.
        """
        ws = db.session.get(Workspace, workspace_id)
        if not ws:
            raise APIError("Workspace not found.", code="WORKSPACE_NOT_FOUND", status=404)

        supplier_id = data.get('supplier_partner_id')
        if not supplier_id:
            raise APIError("supplier_partner_id is required.", code="MISSING_SUPPLIER", status=400)

        supplier = CommercialPartner.query.filter_by(id=supplier_id, workspace_id=workspace_id).first()
        if not supplier:
            raise APIError("Supplier partner not found in this workspace.", code="SUPPLIER_NOT_FOUND", status=404)

        origin = (data.get('origin_country') or '').strip().upper()
        dest = (data.get('destination_country') or '').strip().upper()
        if not origin or len(origin) != 3 or not dest or len(dest) != 3:
            raise APIError("origin_country and destination_country must be valid 3-letter ISO codes.", code="INVALID_COUNTRY_CODE", status=400)

        mode = (data.get('transport_mode') or 'OCEAN').strip().upper()
        if mode not in cls.VALID_MODES:
            raise APIError(f"Invalid transport_mode '{mode}'. Allowed: {sorted(list(cls.VALID_MODES))}", code="INVALID_TRANSPORT_MODE", status=400)

        # Validate linked PO if provided
        po_id = data.get('purchase_order_id')
        if po_id:
            po = BusinessPurchaseOrder.query.filter_by(id=po_id, workspace_id=workspace_id).first()
            if not po:
                raise APIError("Purchase order not found.", code="PO_NOT_FOUND", status=404)

        # Validate linked GRN if provided
        grn_id = data.get('goods_receipt_id')
        if grn_id:
            grn = BusinessGoodsReceipt.query.filter_by(id=grn_id, workspace_id=workspace_id).first()
            if not grn:
                raise APIError("Goods receipt not found.", code="GRN_NOT_FOUND", status=404)

        # Validate linked Landed Cost Voucher if provided
        lcv_id = data.get('landed_cost_voucher_id')
        if lcv_id:
            lcv = BusinessLandedCostVoucher.query.filter_by(id=lcv_id, workspace_id=workspace_id).first()
            if not lcv:
                raise APIError("Landed cost voucher not found.", code="LCV_NOT_FOUND", status=404)

        # Declared customs value
        declared_val = Decimal('0.00')
        if data.get('declared_customs_value') is not None:
            try:
                declared_val = Decimal(str(data['declared_customs_value'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                if declared_val < Decimal('0.00'):
                    raise ValueError()
            except (InvalidOperation, ValueError, TypeError):
                raise APIError("declared_customs_value must be a non-negative decimal.", code="INVALID_DECLARED_VALUE", status=400)

        shipment_num = cls._generate_shipment_number(workspace_id)

        shipment = BusinessCrossBorderShipment(
            workspace_id=workspace_id,
            shipment_number=shipment_num,
            purchase_order_id=po_id,
            goods_receipt_id=grn_id,
            landed_cost_voucher_id=lcv_id,
            supplier_partner_id=supplier_id,
            origin_country=origin,
            destination_country=dest,
            carrier_name=data.get('carrier_name'),
            transport_mode=mode,
            tracking_number=data.get('tracking_number'),
            bill_of_lading_number=data.get('bill_of_lading_number'),
            status='PLANNED',
            customs_reference=data.get('customs_reference'),
            customs_status='PENDING',
            declared_customs_value=declared_val,
            declared_currency=(data.get('declared_currency') or 'USD').strip().upper(),
            port_of_loading=data.get('port_of_loading'),
            port_of_entry=data.get('port_of_entry'),
            notes=data.get('notes'),
            created_by_user_id=actor_user_id
        )

        # Dates parsing
        for date_field in ['estimated_departure_date', 'actual_departure_date', 'estimated_arrival_date', 'actual_arrival_date', 'customs_clearance_date']:
            raw_d = data.get(date_field)
            if raw_d:
                try:
                    setattr(shipment, date_field, datetime.strptime(str(raw_d).split('T')[0], '%Y-%m-%d').date())
                except ValueError:
                    pass

        db.session.add(shipment)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="CROSS_BORDER_SHIPMENT_CREATED",
            entity_type="business_cross_border_shipment",
            entity_id=shipment.id,
            after_state=shipment.serialize(),
            reason=f"Created Cross-Border Shipment {shipment_num} ({origin} -> {dest})",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return shipment

    @classmethod
    def update_shipment_status(
        cls,
        workspace_id: str,
        shipment_id: str,
        actor_user_id: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessCrossBorderShipment:
        """
        Updates shipment operational state and customs status with strict state machine validation.
        """
        shipment = BusinessCrossBorderShipment.query.filter_by(
            id=shipment_id,
            workspace_id=workspace_id
        ).with_for_update().first()

        if not shipment:
            raise APIError("Shipment not found in this workspace.", code="SHIPMENT_NOT_FOUND", status=404)

        prev_state = shipment.serialize()

        # 1. Shipment Status Transition
        new_status = data.get('status')
        if new_status:
            new_status = new_status.strip().upper()
            if new_status not in cls.VALID_STATUSES:
                raise APIError(f"Invalid shipment status '{new_status}'.", code="INVALID_STATUS", status=400)

            if new_status != shipment.status:
                allowed = cls.ALLOWED_STATUS_TRANSITIONS.get(shipment.status, set())
                if new_status not in allowed:
                    raise APIError(
                        f"Illegal status transition from '{shipment.status}' to '{new_status}'. Allowed: {sorted(list(allowed))}",
                        code="ILLEGAL_STATUS_TRANSITION",
                        status=400
                    )
                shipment.status = new_status

        # 2. Customs Status Transition
        new_customs = data.get('customs_status')
        if new_customs:
            new_customs = new_customs.strip().upper()
            if new_customs not in cls.VALID_CUSTOMS_STATUSES:
                raise APIError(f"Invalid customs status '{new_customs}'.", code="INVALID_CUSTOMS_STATUS", status=400)

            if new_customs != shipment.customs_status:
                allowed_c = cls.ALLOWED_CUSTOMS_TRANSITIONS.get(shipment.customs_status, set())
                if new_customs not in allowed_c:
                    raise APIError(
                        f"Illegal customs transition from '{shipment.customs_status}' to '{new_customs}'. Allowed: {sorted(list(allowed_c))}",
                        code="ILLEGAL_CUSTOMS_TRANSITION",
                        status=400
                    )
                shipment.customs_status = new_customs
                if new_customs == 'CLEARED' and not shipment.customs_clearance_date:
                    shipment.customs_clearance_date = datetime.now(timezone.utc).date()

        # Optional updates
        if 'customs_reference' in data:
            shipment.customs_reference = data['customs_reference']
        if 'tracking_number' in data:
            shipment.tracking_number = data['tracking_number']
        if 'bill_of_lading_number' in data:
            shipment.bill_of_lading_number = data['bill_of_lading_number']
        if 'notes' in data:
            shipment.notes = data['notes']

        # Dates updates
        for date_field in ['actual_departure_date', 'actual_arrival_date', 'customs_clearance_date']:
            if data.get(date_field):
                try:
                    setattr(shipment, date_field, datetime.strptime(str(data[date_field]).split('T')[0], '%Y-%m-%d').date())
                except ValueError:
                    pass

        # Linkages
        if 'goods_receipt_id' in data and data['goods_receipt_id']:
            grn = BusinessGoodsReceipt.query.filter_by(id=data['goods_receipt_id'], workspace_id=workspace_id).first()
            if grn:
                shipment.goods_receipt_id = grn.id
        if 'landed_cost_voucher_id' in data and data['landed_cost_voucher_id']:
            lcv = BusinessLandedCostVoucher.query.filter_by(id=data['landed_cost_voucher_id'], workspace_id=workspace_id).first()
            if lcv:
                shipment.landed_cost_voucher_id = lcv.id

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="CROSS_BORDER_SHIPMENT_STATUS_UPDATED",
            entity_type="business_cross_border_shipment",
            entity_id=shipment.id,
            before_state=prev_state,
            after_state=shipment.serialize(),
            reason=f"Updated shipment {shipment.shipment_number} status to {shipment.status} (Customs: {shipment.customs_status})",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return shipment

    @classmethod
    def get_shipment_detail(cls, workspace_id: str, shipment_id: str) -> Dict[str, Any]:
        """
        Retrieves full correlated cross-border shipment intelligence.
        """
        shipment = BusinessCrossBorderShipment.query.filter_by(
            id=shipment_id,
            workspace_id=workspace_id
        ).first()

        if not shipment:
            raise APIError("Shipment not found in this workspace.", code="SHIPMENT_NOT_FOUND", status=404)

        data = shipment.serialize(include_relations=True)

        # Correlate received Batches and Serials if GRN is linked
        batches = []
        serials = []
        if shipment.goods_receipt_id:
            grn_lines = BusinessGoodsReceiptLine.query.filter_by(goods_receipt_id=shipment.goods_receipt_id).all()
            sm_ids = [l.stock_movement_id for l in grn_lines if l.stock_movement_id]
            if sm_ids:
                # Find batches
                b_records = BusinessBatch.query.filter(
                    BusinessBatch.workspace_id == workspace_id,
                    BusinessBatch.goods_receipt_id == shipment.goods_receipt_id
                ).all()
                batches = [b.serialize() for b in b_records]

                # Find serials
                s_records = BusinessSerialNumber.query.filter(
                    BusinessSerialNumber.workspace_id == workspace_id,
                    BusinessSerialNumber.goods_receipt_id == shipment.goods_receipt_id
                ).all()
                serials = [s.serialize() for s in s_records]

        data['batches'] = batches
        data['serials'] = serials
        return data

    @classmethod
    def list_shipments(
        cls,
        workspace_id: str,
        status: Optional[str] = None,
        customs_status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Lists and filters cross-border shipments in the workspace.
        """
        q = BusinessCrossBorderShipment.query.filter_by(workspace_id=workspace_id)
        if status:
            q = q.filter_by(status=status.strip().upper())
        if customs_status:
            q = q.filter_by(customs_status=customs_status.strip().upper())
        if supplier_id:
            q = q.filter_by(supplier_partner_id=supplier_id)
        if search:
            s_term = f"%{search.strip()}%"
            q = q.filter(
                (BusinessCrossBorderShipment.shipment_number.ilike(s_term)) |
                (BusinessCrossBorderShipment.tracking_number.ilike(s_term)) |
                (BusinessCrossBorderShipment.bill_of_lading_number.ilike(s_term)) |
                (BusinessCrossBorderShipment.customs_reference.ilike(s_term)) |
                (BusinessCrossBorderShipment.carrier_name.ilike(s_term))
            )

        total = q.count()
        shipments = q.order_by(BusinessCrossBorderShipment.created_at.desc()).offset(offset).limit(limit).all()
        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'shipments': [s.serialize() for s in shipments]
        }

    @classmethod
    def get_operations_summary(cls, workspace_id: str) -> Dict[str, Any]:
        """
        Aggregates cross-border operations metrics and risk signals.
        """
        today = date.today()

        # Shipment metrics
        in_transit = BusinessCrossBorderShipment.query.filter_by(workspace_id=workspace_id, status='IN_TRANSIT').count()
        customs_holds = BusinessCrossBorderShipment.query.filter_by(workspace_id=workspace_id, status='CUSTOMS_HOLD').count()
        pending_customs = BusinessCrossBorderShipment.query.filter(
            BusinessCrossBorderShipment.workspace_id == workspace_id,
            BusinessCrossBorderShipment.customs_status.in_(['PENDING', 'SUBMITTED', 'INSPECTION'])
        ).count()
        delivered_month = BusinessCrossBorderShipment.query.filter(
            BusinessCrossBorderShipment.workspace_id == workspace_id,
            BusinessCrossBorderShipment.status == 'DELIVERED',
            BusinessCrossBorderShipment.actual_arrival_date >= today.replace(day=1)
        ).count()

        # Landed cost totals
        vouchers = BusinessLandedCostVoucher.query.filter(
            BusinessLandedCostVoucher.workspace_id == workspace_id,
            BusinessLandedCostVoucher.status.in_(['ALLOCATED', 'APPROVED'])
        ).all()
        total_landed_costs = sum((v.allocated_total_base_currency for v in vouchers), Decimal('0.00')).quantize(Decimal('0.01'))

        # Open cross-border POs
        open_pos = BusinessPurchaseOrder.query.filter(
            BusinessPurchaseOrder.workspace_id == workspace_id,
            BusinessPurchaseOrder.status.in_(['APPROVED', 'SENT_TO_SUPPLIER', 'PARTIALLY_RECEIVED'])
        ).all()

        total_open_po_base = sum((p.base_currency_total for p in open_pos), Decimal('0.00')).quantize(Decimal('0.01'))

        # Signals
        signals = []
        if customs_holds > 0:
            signals.append({
                'type': 'CUSTOMS_HOLD',
                'severity': 'HIGH',
                'message': f"{customs_holds} shipment(s) currently detained in customs inspection/hold.",
                'count': customs_holds
            })

        overdue_shipments = BusinessCrossBorderShipment.query.filter(
            BusinessCrossBorderShipment.workspace_id == workspace_id,
            BusinessCrossBorderShipment.status.in_(['BOOKED', 'IN_TRANSIT']),
            BusinessCrossBorderShipment.estimated_arrival_date < today
        ).count()
        if overdue_shipments > 0:
            signals.append({
                'type': 'SHIPMENT_DELAY',
                'severity': 'MEDIUM',
                'message': f"{overdue_shipments} shipment(s) have passed estimated arrival date.",
                'count': overdue_shipments
            })

        # Batches nearing expiry (< 30 days)
        expiring_batches = BusinessBatch.query.filter(
            BusinessBatch.workspace_id == workspace_id,
            BusinessBatch.status == 'ACTIVE',
            BusinessBatch.expiry_date != None,
            BusinessBatch.expiry_date <= today + timedelta(days=30)
        ).count()
        if expiring_batches > 0:
            signals.append({
                'type': 'BATCH_EXPIRY_RISK',
                'severity': 'MEDIUM',
                'message': f"{expiring_batches} active batch(es) expiring within 30 days.",
                'count': expiring_batches
            })

        return {
            'workspace_id': workspace_id,
            'shipments': {
                'in_transit': in_transit,
                'customs_holds': customs_holds,
                'pending_clearance': pending_customs,
                'delivered_this_month': delivered_month,
            },
            'procurement': {
                'open_pos_count': len(open_pos),
                'open_pos_total_base': str(total_open_po_base),
            },
            'landed_costs': {
                'vouchers_count': len(vouchers),
                'total_allocated_base': str(total_landed_costs),
            },
            'operational_signals': signals
        }

    @classmethod
    def get_operational_timeline(
        cls,
        workspace_id: str,
        shipment_id: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        goods_receipt_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Assembles a deterministic, chronological event timeline from authoritative records.
        Zero fabricated events; every event references its exact domain record and timestamp.
        """
        timeline = []

        # 1. Purchase Orders
        po_query = BusinessPurchaseOrder.query.filter_by(workspace_id=workspace_id)
        if purchase_order_id:
            po_query = po_query.filter_by(id=purchase_order_id)
        pos = po_query.all()
        for po in pos:
            timeline.append({
                'event_type': 'PURCHASE_ORDER_CREATED',
                'timestamp': po.created_at.isoformat() if po.created_at else None,
                'entity_type': 'business_purchase_order',
                'entity_id': po.id,
                'reference': po.po_number,
                'description': f"Purchase Order {po.po_number} created (Total: {po.currency} {po.total_amount})"
            })
            if po.approved_at:
                timeline.append({
                    'event_type': 'PURCHASE_ORDER_APPROVED',
                    'timestamp': po.approved_at.isoformat(),
                    'entity_type': 'business_purchase_order',
                    'entity_id': po.id,
                    'reference': po.po_number,
                    'description': f"Purchase Order {po.po_number} formally approved"
                })

        # 2. Shipments
        shp_query = BusinessCrossBorderShipment.query.filter_by(workspace_id=workspace_id)
        if shipment_id:
            shp_query = shp_query.filter_by(id=shipment_id)
        elif purchase_order_id:
            shp_query = shp_query.filter_by(purchase_order_id=purchase_order_id)
        shipments = shp_query.all()
        for s in shipments:
            timeline.append({
                'event_type': 'SHIPMENT_PLANNED',
                'timestamp': s.created_at.isoformat() if s.created_at else None,
                'entity_type': 'business_cross_border_shipment',
                'entity_id': s.id,
                'reference': s.shipment_number,
                'description': f"Consignment {s.shipment_number} planned from {s.origin_country} to {s.destination_country}"
            })
            if s.actual_departure_date:
                timeline.append({
                    'event_type': 'SHIPMENT_DEPARTED',
                    'timestamp': f"{s.actual_departure_date.isoformat()}T00:00:00Z",
                    'entity_type': 'business_cross_border_shipment',
                    'entity_id': s.id,
                    'reference': s.shipment_number,
                    'description': f"Consignment {s.shipment_number} departed origin port ({s.port_of_loading or s.origin_country})"
                })
            if s.customs_clearance_date:
                timeline.append({
                    'event_type': 'CUSTOMS_CLEARED',
                    'timestamp': f"{s.customs_clearance_date.isoformat()}T00:00:00Z",
                    'entity_type': 'business_cross_border_shipment',
                    'entity_id': s.id,
                    'reference': s.customs_reference or s.shipment_number,
                    'description': f"Customs cleared for consignment {s.shipment_number} at {s.port_of_entry or s.destination_country}"
                })
            if s.actual_arrival_date:
                timeline.append({
                    'event_type': 'SHIPMENT_DELIVERED',
                    'timestamp': f"{s.actual_arrival_date.isoformat()}T00:00:00Z",
                    'entity_type': 'business_cross_border_shipment',
                    'entity_id': s.id,
                    'reference': s.shipment_number,
                    'description': f"Consignment {s.shipment_number} delivered to destination warehouse"
                })

        # 3. Goods Receipts
        grn_query = BusinessGoodsReceipt.query.filter_by(workspace_id=workspace_id)
        if goods_receipt_id:
            grn_query = grn_query.filter_by(id=goods_receipt_id)
        elif purchase_order_id:
            grn_query = grn_query.filter_by(purchase_order_id=purchase_order_id)
        grns = grn_query.all()
        for g in grns:
            timeline.append({
                'event_type': 'GOODS_RECEIPT_COMPLETED',
                'timestamp': g.created_at.isoformat() if g.created_at else None,
                'entity_type': 'business_goods_receipt',
                'entity_id': g.id,
                'reference': g.grn_number,
                'description': f"Goods Receipt Note {g.grn_number} processed with accepted stock"
            })

        # 4. Landed Cost Vouchers
        lcv_query = BusinessLandedCostVoucher.query.filter_by(workspace_id=workspace_id)
        if goods_receipt_id:
            lcv_query = lcv_query.filter_by(goods_receipt_id=goods_receipt_id)
        elif purchase_order_id:
            lcv_query = lcv_query.filter_by(purchase_order_id=purchase_order_id)
        vouchers = lcv_query.all()
        for v in vouchers:
            if v.status in ('ALLOCATED', 'APPROVED'):
                timeline.append({
                    'event_type': 'LANDED_COST_ALLOCATED',
                    'timestamp': v.updated_at.isoformat() if v.updated_at else None,
                    'entity_type': 'business_landed_cost_voucher',
                    'entity_id': v.id,
                    'reference': v.voucher_number,
                    'description': f"Landed cost of {v.base_currency} {v.allocated_total_base_currency} allocated via {v.allocation_basis}"
                })
            if v.approved_at:
                timeline.append({
                    'event_type': 'LANDED_COST_APPROVED',
                    'timestamp': v.approved_at.isoformat(),
                    'entity_type': 'business_landed_cost_voucher',
                    'entity_id': v.id,
                    'reference': v.voucher_number,
                    'description': f"Landed cost voucher {v.voucher_number} locked and approved"
                })

        # Sort timeline chronologically
        timeline.sort(key=lambda x: x.get('timestamp') or '')
        return timeline
