"""
DeadlineOS Business OS — Visual Restock Service (Phase C4.4)
============================================================
Evaluates visual shelf depletion against configured par levels and targets,
correlates open Purchase Orders and in-transit Cross-Border Freight Shipments,
synthesizes non-binding Draft Purchase Requests, and generates deduplicated
operational alerts while strictly preventing autonomous financial commitments.
"""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import func
from database.db import db
from models.business import (
    BusinessShelfZone,
    BusinessVisualObservation,
    BusinessProduct,
    BusinessLocation,
    BusinessPurchaseRequest,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessCrossBorderShipment,
    BusinessOperationalAlert,
    WorkspaceMember
)
from services.business.purchase_request_service import PurchaseRequestService
from services.business.audit_service import AuditService
from utils.errors import APIError


class VisualRestockService:
    @staticmethod
    def get_in_transit_freight_summary(
        workspace_id: str,
        product_id: str,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregates in-transit purchase order line quantities and active cross-border shipments
        for a given product in a workspace.
        """
        # 1. Query open PO lines for the product
        active_po_statuses = ('APPROVED', 'ISSUED', 'PARTIALLY_RECEIVED')
        po_query = (
            db.session.query(
                BusinessPurchaseOrderLine,
                BusinessPurchaseOrder
            )
            .join(BusinessPurchaseOrder, BusinessPurchaseOrderLine.purchase_order_id == BusinessPurchaseOrder.id)
            .filter(
                BusinessPurchaseOrder.workspace_id == workspace_id,
                BusinessPurchaseOrder.status.in_(active_po_statuses),
                BusinessPurchaseOrderLine.product_id == product_id
            )
        )

        if location_id:
            po_query = po_query.filter(BusinessPurchaseOrder.destination_location_id == location_id)

        po_results = po_query.all()

        total_in_transit_qty = Decimal('0.00')
        active_po_ids = set()

        for line, po in po_results:
            pending_qty = (line.ordered_quantity or Decimal('0.00')) - (line.received_quantity or Decimal('0.00'))
            if pending_qty > Decimal('0.00'):
                total_in_transit_qty += pending_qty
                active_po_ids.add(po.id)

        # 2. Query correlated cross-border shipments
        active_shipment_statuses = ('PLANNED', 'BOOKED', 'IN_TRANSIT', 'CUSTOMS_HOLD', 'CUSTOMS_CLEARED')
        shipments_query = BusinessCrossBorderShipment.query.filter(
            BusinessCrossBorderShipment.workspace_id == workspace_id,
            BusinessCrossBorderShipment.status.in_(active_shipment_statuses)
        )

        if active_po_ids:
            shipments_query = shipments_query.filter(
                BusinessCrossBorderShipment.purchase_order_id.in_(list(active_po_ids))
            )
        else:
            shipments_query = shipments_query.filter(BusinessCrossBorderShipment.id == None)  # empty

        shipments = shipments_query.order_by(BusinessCrossBorderShipment.estimated_arrival_date.asc().nulls_last()).all()

        shipment_list = []
        for s in shipments:
            shipment_list.append({
                'id': s.id,
                'shipment_number': s.shipment_number,
                'carrier_name': s.carrier_name,
                'transport_mode': s.transport_mode,
                'status': s.status,
                'customs_status': s.customs_status,
                'estimated_arrival_date': s.estimated_arrival_date.isoformat() if s.estimated_arrival_date else None,
                'port_of_entry': s.port_of_entry,
                'purchase_order_id': s.purchase_order_id
            })

        return {
            'product_id': product_id,
            'in_transit_quantity': total_in_transit_qty.quantize(Decimal('0.01')),
            'active_pos_count': len(active_po_ids),
            'active_shipments_count': len(shipment_list),
            'shipments': shipment_list
        }

    @staticmethod
    def evaluate_and_trigger_restock(
        workspace_id: str,
        observation_id: str,
        actor_user_id: str,
        override_quantity: Optional[Decimal] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates visual observation depletion against shelf par level and in-transit freight.
        If depleted, generates/updates an operational alert and a draft purchase request (if net shortfall > 0).
        Suppresses draft PR if incoming freight already covers the demand.
        """
        # RBAC Check
        member = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=actor_user_id,
            status='ACTIVE'
        ).first()
        if not member or member.role not in ('OWNER', 'ADMIN'):
            raise APIError("Only OWNER and ADMIN roles may trigger visual restock proposals.", "FORBIDDEN", 403)

        obs = BusinessVisualObservation.query.filter_by(
            id=observation_id,
            workspace_id=workspace_id
        ).first()

        if not obs:
            raise APIError("Visual observation not found in this workspace.", "OBSERVATION_NOT_FOUND", 404)

        # Resolve target product
        product_id = obs.matched_product_id
        if not product_id and obs.shelf_zone_id:
            zone = BusinessShelfZone.query.filter_by(id=obs.shelf_zone_id, workspace_id=workspace_id).first()
            if zone:
                product_id = zone.assigned_product_id

        if not product_id:
            raise APIError("Cannot evaluate restock without an identified product.", "PRODUCT_REQUIRED", 400)

        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
        if not product:
            raise APIError("Product not found in this workspace.", "PRODUCT_NOT_FOUND", 404)

        location = BusinessLocation.query.filter_by(id=obs.location_id, workspace_id=workspace_id).first()
        if not location:
            raise APIError("Location not found in this workspace.", "LOCATION_NOT_FOUND", 404)

        zone = obs.shelf_zone

        visual_count = Decimal(str(obs.visual_count or 0)).quantize(Decimal('0.01'))
        capacity = Decimal(str(zone.expected_capacity if zone and zone.expected_capacity else 0.00)).quantize(Decimal('0.01'))
        threshold = Decimal(str(zone.reorder_threshold if zone and zone.reorder_threshold else (product.reorder_level or 0.00))).quantize(Decimal('0.01'))

        # Check depletion condition
        is_depleted = (
            (visual_count <= threshold) or
            (obs.anomaly_type in ('EMPTY_SHELF', 'OUT_OF_STOCK', 'FACING_DEFICIT'))
        )

        freight_summary = VisualRestockService.get_in_transit_freight_summary(
            workspace_id=workspace_id,
            product_id=product.id,
            location_id=location.id
        )

        if not is_depleted and (override_quantity is None or override_quantity <= Decimal('0.00')):
            return {
                'is_depleted': False,
                'message': f"Shelf count ({visual_count} {product.unit}) is above reorder threshold ({threshold} {product.unit}). No restock needed.",
                'gross_demand': '0.00',
                'in_transit_quantity': str(freight_summary['in_transit_quantity']),
                'net_shortfall': '0.00',
                'purchase_request': None,
                'operational_alert': None,
                'in_transit_summary': freight_summary
            }

        # Calculate gross replenishment demand
        if override_quantity and override_quantity > Decimal('0.00'):
            gross_demand = Decimal(str(override_quantity)).quantize(Decimal('0.01'))
        else:
            if capacity > visual_count:
                gross_demand = (capacity - visual_count).quantize(Decimal('0.01'))
            else:
                gross_demand = max(threshold, Decimal('1.00')).quantize(Decimal('0.01'))

        in_transit_qty = freight_summary['in_transit_quantity']
        net_shortfall = max(Decimal('0.00'), gross_demand - in_transit_qty).quantize(Decimal('0.01'))

        is_empty = (visual_count == Decimal('0.00')) or (obs.anomaly_type in ('EMPTY_SHELF', 'OUT_OF_STOCK'))
        priority = 'URGENT' if is_empty else 'HIGH'

        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        zone_str = zone.id if zone else 'no_zone'
        fingerprint_raw = f"{workspace_id}:{location.id}:{product.id}:{zone_str}:{date_str}"
        fingerprint = hashlib.sha256(fingerprint_raw.encode('utf-8')).hexdigest()

        created_pr = None
        alert = None

        # Case 1: In-transit freight covers gross demand -> Suppress Draft PR
        if net_shortfall == Decimal('0.00'):
            alert = BusinessOperationalAlert.query.filter_by(
                workspace_id=workspace_id,
                dedup_fingerprint=fingerprint
            ).first()

            desc = (
                f"Shelf deficit detected on zone {zone.zone_code if zone else 'N/A'} "
                f"({gross_demand} {product.unit}), but {in_transit_qty} {product.unit} is currently "
                f"en route across {freight_summary['active_shipments_count']} active shipment(s). "
                f"Draft PR creation suppressed."
            )

            if alert:
                alert.alert_type = 'RESTOCK_EN_ROUTE'
                alert.severity = 'INFO'
                alert.title = f"Restock En Route: {product.name} ({product.sku})"
                alert.description = desc
                alert.recommended_action = 'EXPEDITE_PO'
            else:
                alert = BusinessOperationalAlert(
                    workspace_id=workspace_id,
                    alert_type='RESTOCK_EN_ROUTE',
                    severity='INFO',
                    status='ACTIVE',
                    title=f"Restock En Route: {product.name} ({product.sku})",
                    description=desc,
                    entity_type='PRODUCT',
                    entity_id=product.id,
                    dedup_fingerprint=fingerprint,
                    recommended_action='EXPEDITE_PO'
                )
                db.session.add(alert)
                db.session.flush()

            obs.operational_alert_id = alert.id
            db.session.commit()

            AuditService.log_event(
                workspace_id=workspace_id,
                actor_user_id=actor_user_id,
                action='RESTOCK_TRIGGERED',
                entity_type='business_visual_observation',
                entity_id=obs.id,
                after_state={'status': 'SUPPRESSED_EN_ROUTE', 'gross_demand': str(gross_demand), 'in_transit_qty': str(in_transit_qty)},
                reason=f"Restock evaluation suppressed: {in_transit_qty} units in transit",
                ip_address=ip_address,
                user_agent=user_agent
            )

            return {
                'is_depleted': True,
                'message': f"Restock demand of {gross_demand} {product.unit} is covered by {in_transit_qty} {product.unit} in-transit freight. Draft PR suppressed.",
                'gross_demand': str(gross_demand),
                'in_transit_quantity': str(in_transit_qty),
                'net_shortfall': '0.00',
                'purchase_request': None,
                'operational_alert': alert.to_dict() if alert else None,
                'in_transit_summary': freight_summary
            }

        # Case 2: Net Shortfall > 0 -> Create or Update Draft Purchase Request
        existing_pr = (
            BusinessPurchaseRequest.query
            .filter_by(workspace_id=workspace_id, product_id=product.id, location_id=location.id)
            .filter(BusinessPurchaseRequest.status.in_(['DRAFT', 'SUBMITTED']))
            .order_by(BusinessPurchaseRequest.created_at.desc())
            .first()
        )

        unit_price = product.cost_price or Decimal('0.00')
        reason_msg = (
            f"Visual restock trigger from observation {obs.id} on zone {zone.zone_code if zone else 'N/A'}: "
            f"Gross demand: {gross_demand} {product.unit}, In-transit: {in_transit_qty} {product.unit}, "
            f"Net shortfall: {net_shortfall} {product.unit}"
        )

        if existing_pr:
            existing_pr.requested_quantity = net_shortfall
            existing_pr.estimated_unit_price = unit_price
            existing_pr.estimated_total_price = (net_shortfall * unit_price).quantize(Decimal('0.01'))
            existing_pr.priority = priority
            existing_pr.reason = reason_msg
            created_pr = existing_pr
        else:
            req_num = PurchaseRequestService.generate_request_number(workspace_id)
            created_pr = BusinessPurchaseRequest(
                workspace_id=workspace_id,
                request_number=req_num,
                product_id=product.id,
                location_id=location.id,
                requested_quantity=net_shortfall,
                estimated_unit_price=unit_price,
                estimated_total_price=(net_shortfall * unit_price).quantize(Decimal('0.01')),
                priority=priority,
                status='DRAFT',
                reason=reason_msg,
                requested_by_user_id=actor_user_id
            )
            db.session.add(created_pr)
            db.session.flush()

        # Create or Update Operational Alert
        alert = BusinessOperationalAlert.query.filter_by(
            workspace_id=workspace_id,
            dedup_fingerprint=fingerprint
        ).first()

        alert_desc = (
            f"Shelf zone {zone.zone_code if zone else 'N/A'} is depleted "
            f"(Visual count: {visual_count}, Capacity: {capacity}). "
            f"Draft PR {created_pr.request_number} generated for {net_shortfall} {product.unit}."
        )

        if alert:
            alert.alert_type = 'VISUAL_RESTOCK_REQUIRED'
            alert.severity = 'CRITICAL' if priority == 'URGENT' else 'WARNING'
            alert.title = f"Visual Restock: {product.name} ({product.sku})"
            alert.description = alert_desc
            alert.recommended_action = 'CREATE_PURCHASE_REQUEST'
        else:
            alert = BusinessOperationalAlert(
                workspace_id=workspace_id,
                alert_type='VISUAL_RESTOCK_REQUIRED',
                severity='CRITICAL' if priority == 'URGENT' else 'WARNING',
                status='ACTIVE',
                title=f"Visual Restock: {product.name} ({product.sku})",
                description=alert_desc,
                entity_type='PRODUCT',
                entity_id=product.id,
                dedup_fingerprint=fingerprint,
                recommended_action='CREATE_PURCHASE_REQUEST'
            )
            db.session.add(alert)
            db.session.flush()

        obs.operational_alert_id = alert.id
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='RESTOCK_TRIGGERED',
            entity_type='business_purchase_request',
            entity_id=created_pr.id,
            after_state=created_pr.serialize(),
            reason=f"Restock PR {created_pr.request_number} generated for {net_shortfall} {product.unit}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            'is_depleted': True,
            'message': f"Visual restock triggered: Draft PR {created_pr.request_number} created for {net_shortfall} {product.unit}.",
            'gross_demand': str(gross_demand),
            'in_transit_quantity': str(in_transit_qty),
            'net_shortfall': str(net_shortfall),
            'purchase_request': created_pr.serialize(),
            'operational_alert': alert.to_dict() if alert else None,
            'in_transit_summary': freight_summary
        }

    @staticmethod
    def list_active_restock_triggers(
        workspace_id: str,
        location_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lists depleted shelf zones across locations with live shortfall metrics and in-transit correlation.
        """
        zones_query = BusinessShelfZone.query.filter_by(workspace_id=workspace_id, status='ACTIVE')
        if location_id:
            zones_query = zones_query.filter_by(location_id=location_id)

        zones = zones_query.all()
        results = []

        for z in zones:
            if not z.assigned_product_id:
                continue

            # Get latest observation for this zone
            latest_obs = (
                BusinessVisualObservation.query
                .filter_by(workspace_id=workspace_id, shelf_zone_id=z.id)
                .order_by(BusinessVisualObservation.capture_timestamp.desc())
                .first()
            )

            visual_count = latest_obs.visual_count if latest_obs else Decimal('0.00')
            capacity = z.expected_capacity or Decimal('0.00')
            threshold = z.reorder_threshold or Decimal('0.00')

            is_depleted = (visual_count <= threshold) or (latest_obs and latest_obs.anomaly_type in ('EMPTY_SHELF', 'OUT_OF_STOCK', 'FACING_DEFICIT'))

            if is_depleted:
                gross_demand = max(capacity - visual_count, threshold, Decimal('1.00')).quantize(Decimal('0.01'))
                freight = VisualRestockService.get_in_transit_freight_summary(workspace_id, z.assigned_product_id, z.location_id)
                in_transit = freight['in_transit_quantity']
                net_shortfall = max(Decimal('0.00'), gross_demand - in_transit).quantize(Decimal('0.01'))

                results.append({
                    'shelf_zone_id': z.id,
                    'zone_code': z.zone_code,
                    'zone_name': z.name,
                    'location_id': z.location_id,
                    'product_id': z.assigned_product_id,
                    'product_sku': z.assigned_product.sku if z.assigned_product else None,
                    'product_name': z.assigned_product.name if z.assigned_product else None,
                    'visual_count': str(visual_count),
                    'expected_capacity': str(capacity),
                    'reorder_threshold': str(threshold),
                    'gross_demand': str(gross_demand),
                    'in_transit_quantity': str(in_transit),
                    'net_shortfall': str(net_shortfall),
                    'latest_observation_id': latest_obs.id if latest_obs else None,
                    'latest_anomaly_type': latest_obs.anomaly_type if latest_obs else None,
                    'in_transit_summary': freight
                })

        total = len(results)
        paginated = results[offset:offset + limit]
        return paginated, total
