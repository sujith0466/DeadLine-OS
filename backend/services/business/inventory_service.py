"""
DeadlineOS Business OS — Inventory & Stock Movement Service
============================================================
Authoritative operational inventory logic.
Derives stock truth exclusively from append-only movement ledger,
enforces negative stock prevention, and executes atomic inter-location transfers.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import func, case
from database.db import db
from models.business import (
    BusinessProduct,
    BusinessLocation,
    BusinessStockMovement,
    StagedExtraction
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class InventoryService:
    VALID_MOVEMENT_TYPES = {
        'INITIAL_STOCK': 'IN',
        'PURCHASE_RECEIVED': 'IN',
        'SALE': 'OUT',
        'TRANSFER_IN': 'IN',
        'TRANSFER_OUT': 'OUT',
        'DAMAGED': 'OUT',
        'RETURN': 'IN',
        'MANUAL_ADJUSTMENT': None  # Can be IN or OUT
    }

    @staticmethod
    def get_available_stock(workspace_id: str, product_id: str, location_id: str) -> Decimal:
        """
        Calculates authoritative available stock quantity for a product at a specific location
        by aggregating all immutable ledger movements.
        """
        result = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (BusinessStockMovement.direction == 'IN', BusinessStockMovement.quantity),
                        (BusinessStockMovement.direction == 'OUT', -BusinessStockMovement.quantity),
                        else_=0
                    )
                ),
                0
            )
        ).filter(
            BusinessStockMovement.workspace_id == workspace_id,
            BusinessStockMovement.product_id == product_id,
            BusinessStockMovement.location_id == location_id
        ).scalar()

        return Decimal(str(result or 0.00)).quantize(Decimal('0.01'))

    @staticmethod
    def get_total_product_stock(workspace_id: str, product_id: str) -> Decimal:
        """
        Calculates aggregate stock quantity across all locations for a product.
        """
        result = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (BusinessStockMovement.direction == 'IN', BusinessStockMovement.quantity),
                        (BusinessStockMovement.direction == 'OUT', -BusinessStockMovement.quantity),
                        else_=0
                    )
                ),
                0
            )
        ).filter(
            BusinessStockMovement.workspace_id == workspace_id,
            BusinessStockMovement.product_id == product_id
        ).scalar()

        return Decimal(str(result or 0.00)).quantize(Decimal('0.01'))

    @staticmethod
    def record_stock_movement(
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        staged_extraction_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessStockMovement:
        """
        Records an authoritative, append-only stock movement in the ledger.
        Pre-validates available stock for OUT movements to strictly prevent negative inventory.
        """
        product_id = data.get('product_id')
        if not product_id:
            raise APIError("Field 'product_id' is required.", "VALIDATION_ERROR", 400)

        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
        if not product:
            raise APIError("Product not found in this workspace.", "NOT_FOUND", 404)

        if product.status == 'ARCHIVED':
            raise APIError(f"Cannot record stock movement for archived product '{product.sku}'.", "PRODUCT_ARCHIVED", 400)

        location_id = data.get('location_id')
        if not location_id:
            raise APIError("Field 'location_id' is required.", "VALIDATION_ERROR", 400)

        location = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id).first()
        if not location:
            raise APIError("Location not found in this workspace.", "NOT_FOUND", 404)

        if location.status == 'INACTIVE':
            raise APIError(f"Cannot record stock movement for inactive location '{location.name}'.", "LOCATION_INACTIVE", 400)

        movement_type = (data.get('movement_type') or '').upper()
        if movement_type not in InventoryService.VALID_MOVEMENT_TYPES:
            raise APIError(f"Invalid movement_type '{movement_type}'. Allowed: {list(InventoryService.VALID_MOVEMENT_TYPES.keys())}", "VALIDATION_ERROR", 400)

        # Determine and validate direction
        expected_direction = InventoryService.VALID_MOVEMENT_TYPES[movement_type]
        if expected_direction is not None:
            direction = expected_direction
        else:
            direction = (data.get('direction') or 'IN').upper()
            if direction not in ('IN', 'OUT'):
                raise APIError("Direction must be 'IN' or 'OUT'.", "VALIDATION_ERROR", 400)

        try:
            quantity = Decimal(str(data.get('quantity', 0.00))).quantize(Decimal('0.01'))
        except Exception:
            raise APIError("Field 'quantity' must be a valid positive number.", "VALIDATION_ERROR", 400)

        if quantity <= Decimal('0.00'):
            raise APIError("Movement 'quantity' must be strictly greater than zero.", "VALIDATION_ERROR", 400)

        unit_cost = None
        if data.get('unit_cost') is not None:
            try:
                unit_cost = Decimal(str(data['unit_cost'])).quantize(Decimal('0.01'))
            except Exception:
                unit_cost = None

        # STRICT NEGATIVE STOCK ENFORCEMENT
        if direction == 'OUT':
            available = InventoryService.get_available_stock(workspace_id, product_id, location_id)
            if quantity > available:
                raise APIError(
                    f"Insufficient stock available for SKU '{product.sku}' at location '{location.name}'. "
                    f"Available: {available} {product.unit}, Requested: {quantity} {product.unit}.",
                    "INSUFFICIENT_STOCK",
                    400
                )

        if staged_extraction_id:
            staged = StagedExtraction.query.filter_by(id=staged_extraction_id, workspace_id=workspace_id).first()
            if not staged:
                staged_extraction_id = None

        movement = BusinessStockMovement(
            workspace_id=workspace_id,
            product_id=product_id,
            location_id=location_id,
            movement_type=movement_type,
            direction=direction,
            quantity=quantity,
            unit_cost=unit_cost,
            reference_type=data.get('reference_type'),
            reference_id=data.get('reference_id'),
            transfer_batch_id=data.get('transfer_batch_id'),
            staged_extraction_id=staged_extraction_id,
            actor_user_id=actor_user_id,
            reason=data.get('reason')
        )
        db.session.add(movement)
        db.session.flush()

        # C3.2: Batch attributions validation and ledger linking
        batch_attributions = data.get('batch_attributions') or data.get('batches')
        if batch_attributions:
            from services.business.batch_service import BatchService
            BatchService.validate_and_attribute_movement(
                workspace_id=workspace_id,
                movement=movement,
                attributions=batch_attributions,
                actor_user_id=actor_user_id,
                fefo_override_reason=data.get('fefo_override_reason')
            )

        # C3.3: Serial attributions validation and ledger linking
        serial_attributions = data.get('serial_attributions') or data.get('serials') or data.get('serial_numbers')
        if product.is_serialized or serial_attributions:
            from services.business.serial_service import SerialService
            SerialService.validate_and_attribute_movement(
                workspace_id=workspace_id,
                movement=movement,
                product=product,
                serials=serial_attributions,
                actor_user_id=actor_user_id,
                notes=data.get('serial_notes')
            )

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="STOCK_MOVEMENT_RECORDED",
            entity_type="business_stock_movement",
            entity_id=movement.id,
            after_state=movement.serialize(),
            reason=f"{movement_type} ({direction} {quantity} {product.unit}) for SKU {product.sku}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return movement

    @staticmethod
    def transfer_stock(
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        """
        Executes an atomic two-sided inter-location transfer.
        Commits TRANSFER_OUT at source and TRANSFER_IN at destination in a single transaction.
        """
        product_id = data.get('product_id')
        source_location_id = data.get('source_location_id')
        dest_location_id = data.get('destination_location_id')

        if not product_id or not source_location_id or not dest_location_id:
            raise APIError("Fields 'product_id', 'source_location_id', and 'destination_location_id' are required.", "VALIDATION_ERROR", 400)

        if source_location_id == dest_location_id:
            raise APIError("Source and destination locations must be different.", "VALIDATION_ERROR", 400)

        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
        if not product:
            raise APIError("Product not found in this workspace.", "NOT_FOUND", 404)

        if product.status == 'ARCHIVED':
            raise APIError("Cannot transfer archived product.", "PRODUCT_ARCHIVED", 400)

        source_loc = BusinessLocation.query.filter_by(id=source_location_id, workspace_id=workspace_id).first()
        dest_loc = BusinessLocation.query.filter_by(id=dest_location_id, workspace_id=workspace_id).first()

        if not source_loc:
            raise APIError("Source location not found in this workspace.", "NOT_FOUND", 404)
        if not dest_loc:
            raise APIError("Destination location not found in this workspace.", "NOT_FOUND", 404)

        if source_loc.status == 'INACTIVE' or dest_loc.status == 'INACTIVE':
            raise APIError("Both source and destination locations must be ACTIVE.", "LOCATION_INACTIVE", 400)

        try:
            quantity = Decimal(str(data.get('quantity', 0.00))).quantize(Decimal('0.01'))
        except Exception:
            raise APIError("Transfer 'quantity' must be a valid positive number.", "VALIDATION_ERROR", 400)

        if quantity <= Decimal('0.00'):
            raise APIError("Transfer 'quantity' must be strictly greater than zero.", "VALIDATION_ERROR", 400)

        # STRICT PRE-VALIDATION: Check available stock at source
        available_at_source = InventoryService.get_available_stock(workspace_id, product_id, source_location_id)
        if quantity > available_at_source:
            raise APIError(
                f"Insufficient stock for transfer at '{source_loc.name}'. "
                f"Available: {available_at_source} {product.unit}, Requested: {quantity} {product.unit}.",
                "INSUFFICIENT_STOCK",
                400
            )

        transfer_batch_id = str(uuid.uuid4())
        reason = data.get('reason') or f"Inter-location transfer from {source_loc.name} to {dest_loc.name}"

        # Atomic commit of both movements
        out_movement = BusinessStockMovement(
            workspace_id=workspace_id,
            product_id=product_id,
            location_id=source_location_id,
            movement_type='TRANSFER_OUT',
            direction='OUT',
            quantity=quantity,
            transfer_batch_id=transfer_batch_id,
            actor_user_id=actor_user_id,
            reason=reason
        )

        in_movement = BusinessStockMovement(
            workspace_id=workspace_id,
            product_id=product_id,
            location_id=dest_location_id,
            movement_type='TRANSFER_IN',
            direction='IN',
            quantity=quantity,
            transfer_batch_id=transfer_batch_id,
            actor_user_id=actor_user_id,
            reason=reason
        )

        db.session.add(out_movement)
        db.session.add(in_movement)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="STOCK_TRANSFER_EXECUTED",
            entity_type="business_stock_movement",
            entity_id=transfer_batch_id,
            after_state={
                'transfer_batch_id': transfer_batch_id,
                'product_id': product_id,
                'sku': product.sku,
                'quantity': str(quantity),
                'source_location_id': source_location_id,
                'source_location_name': source_loc.name,
                'destination_location_id': dest_location_id,
                'destination_location_name': dest_loc.name
            },
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            'transfer_batch_id': transfer_batch_id,
            'product_id': product_id,
            'product_name': product.name,
            'sku': product.sku,
            'quantity': str(quantity),
            'source_location': source_loc.serialize(),
            'destination_location': dest_loc.serialize(),
            'out_movement_id': out_movement.id,
            'in_movement_id': in_movement.id,
            'created_at': out_movement.created_at.isoformat()
        }

    @staticmethod
    def get_stock_levels(
        workspace_id: str,
        location_id: str = None,
        category: str = None,
        status_filter: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Retrieves live derived stock levels across products and locations.
        Calculates status: OUT_OF_STOCK, LOW, HEALTHY, and critical safety stock indicators.
        """
        # Base query for products in workspace
        prod_query = BusinessProduct.query.filter(
            BusinessProduct.workspace_id == workspace_id,
            BusinessProduct.status != 'ARCHIVED'
        )
        if category:
            prod_query = prod_query.filter_by(category=category)
        if search:
            prod_query = prod_query.filter(
                (BusinessProduct.name.ilike(f"%{search}%")) |
                (BusinessProduct.sku.ilike(f"%{search}%"))
            )

        products = prod_query.order_by(BusinessProduct.name.asc()).all()

        # Aggregate stock per product and location
        stock_agg_query = db.session.query(
            BusinessStockMovement.product_id,
            BusinessStockMovement.location_id,
            func.sum(
                case(
                    (BusinessStockMovement.direction == 'IN', BusinessStockMovement.quantity),
                    (BusinessStockMovement.direction == 'OUT', -BusinessStockMovement.quantity),
                    else_=0
                )
            ).label('current_quantity')
        ).filter(
            BusinessStockMovement.workspace_id == workspace_id
        )

        if location_id:
            stock_agg_query = stock_agg_query.filter(BusinessStockMovement.location_id == location_id)

        stock_aggregates = stock_agg_query.group_by(
            BusinessStockMovement.product_id,
            BusinessStockMovement.location_id
        ).all()

        # Build product-to-location stock map
        # map: { product_id: { location_id: Decimal } }
        stock_map = {}
        for p_id, l_id, qty in stock_aggregates:
            if p_id not in stock_map:
                stock_map[p_id] = {}
            stock_map[p_id][l_id] = Decimal(str(qty or 0.00)).quantize(Decimal('0.01'))

        # Fetch active locations for name resolution
        locations = BusinessLocation.query.filter_by(workspace_id=workspace_id, status='ACTIVE').all()
        location_dict = {loc.id: loc.name for loc in locations}

        stock_items = []
        total_skus = len(products)
        low_stock_count = 0
        out_of_stock_count = 0
        total_valuation = Decimal('0.00')

        for prod in products:
            prod_loc_stocks = stock_map.get(prod.id, {})

            if location_id:
                loc_qty = prod_loc_stocks.get(location_id, Decimal('0.00'))
                current_qty = loc_qty
                breakdown = [{
                    'location_id': location_id,
                    'location_name': location_dict.get(location_id, 'Selected Location'),
                    'quantity': str(loc_qty)
                }]
            else:
                current_qty = sum(prod_loc_stocks.values(), Decimal('0.00'))
                breakdown = [
                    {
                        'location_id': loc_id,
                        'location_name': location_dict.get(loc_id, 'Unknown Location'),
                        'quantity': str(q)
                    }
                    for loc_id, q in prod_loc_stocks.items()
                ]

            reorder_lvl = Decimal(str(prod.reorder_level))
            safety_lvl = Decimal(str(prod.safety_stock))
            cost_price = Decimal(str(prod.cost_price))
            selling_price = Decimal(str(prod.selling_price))

            # Stock health evaluation
            if current_qty <= Decimal('0.00'):
                health_status = 'OUT_OF_STOCK'
                out_of_stock_count += 1
            elif current_qty <= reorder_lvl:
                health_status = 'LOW'
                low_stock_count += 1
            else:
                health_status = 'HEALTHY'

            is_critical = current_qty <= safety_lvl and safety_lvl > Decimal('0.00')
            item_valuation = (current_qty * cost_price).quantize(Decimal('0.01'))
            if current_qty > Decimal('0.00'):
                total_valuation += item_valuation

            item_data = {
                'product_id': prod.id,
                'sku': prod.sku,
                'name': prod.name,
                'category': prod.category,
                'unit': prod.unit,
                'current_quantity': str(current_qty),
                'reorder_level': str(reorder_lvl),
                'safety_stock': str(safety_lvl),
                'cost_price': str(cost_price),
                'selling_price': str(selling_price),
                'stock_value': str(item_valuation),
                'currency': prod.currency,
                'status': health_status,
                'is_critical_safety': is_critical,
                'preferred_supplier_partner_id': prod.preferred_supplier_partner_id,
                'supplier_name': prod.supplier.name if prod.supplier else None,
                'location_breakdown': breakdown
            }

            if not status_filter or health_status == status_filter.upper():
                stock_items.append(item_data)

        # Pagination slice
        paginated_items = stock_items[offset:offset + limit]

        return {
            'total_skus': total_skus,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'total_stock_valuation': str(total_valuation),
            'currency': 'INR',
            'total_items': len(stock_items),
            'items': paginated_items
        }

    @staticmethod
    def get_movement_ledger(
        workspace_id: str,
        product_id: str = None,
        location_id: str = None,
        movement_type: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = BusinessStockMovement.query.filter_by(workspace_id=workspace_id)
        if product_id:
            query = query.filter_by(product_id=product_id)
        if location_id:
            query = query.filter_by(location_id=location_id)
        if movement_type:
            query = query.filter_by(movement_type=movement_type.upper())

        total = query.count()
        movements = query.order_by(BusinessStockMovement.created_at.desc()).offset(offset).limit(min(limit, 100)).all()
        return [m.serialize() for m in movements], total
