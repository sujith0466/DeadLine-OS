"""
DeadlineOS Business OS — Product & SKU Service
===============================================
Business logic for catalog SKU definition, pricing metadata,
and product lifecycle management.
"""

from database.db import db
from datetime import datetime, timezone
from decimal import Decimal
from models.business import BusinessProduct, CommercialPartner, BusinessStockMovement
from services.business.audit_service import AuditService
from utils.errors import APIError


class ProductService:
    VALID_UNITS = {'UNIT', 'PCS', 'KG', 'GRAM', 'LITER', 'ML', 'BOX', 'PACK', 'METER'}
    VALID_STATUSES = {'ACTIVE', 'DISCONTINUED', 'ARCHIVED'}

    @staticmethod
    def create_product(
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessProduct:
        sku = (data.get('sku') or '').strip().upper()
        if not sku:
            raise APIError("Product 'sku' is required.", "VALIDATION_ERROR", 400)

        name = (data.get('name') or '').strip()
        if not name:
            raise APIError("Product 'name' is required.", "VALIDATION_ERROR", 400)

        existing = BusinessProduct.query.filter_by(workspace_id=workspace_id, sku=sku).first()
        if existing:
            raise APIError(f"Product with SKU '{sku}' already exists in this workspace.", "DUPLICATE_SKU", 400)

        unit = (data.get('unit') or 'UNIT').upper()
        if unit not in ProductService.VALID_UNITS:
            raise APIError(f"Invalid unit '{unit}'. Allowed: {ProductService.VALID_UNITS}", "VALIDATION_ERROR", 400)

        try:
            reorder_level = Decimal(str(data.get('reorder_level', 0.00)))
            safety_stock = Decimal(str(data.get('safety_stock', 0.00)))
            cost_price = Decimal(str(data.get('cost_price', 0.00)))
            selling_price = Decimal(str(data.get('selling_price', 0.00)))
        except Exception:
            raise APIError("Numerical fields (reorder_level, safety_stock, cost_price, selling_price) must be valid decimals.", "VALIDATION_ERROR", 400)

        if reorder_level < 0 or safety_stock < 0 or cost_price < 0 or selling_price < 0:
            raise APIError("Pricing and threshold values must be non-negative.", "VALIDATION_ERROR", 400)

        supplier_id = data.get('preferred_supplier_partner_id')
        if supplier_id:
            supplier = CommercialPartner.query.filter_by(id=supplier_id, workspace_id=workspace_id).first()
            if not supplier:
                raise APIError("Referenced supplier not found in this workspace.", "VALIDATION_ERROR", 400)

        product = BusinessProduct(
            workspace_id=workspace_id,
            sku=sku,
            name=name,
            category=data.get('category'),
            unit=unit,
            reorder_level=reorder_level,
            safety_stock=safety_stock,
            cost_price=cost_price,
            selling_price=selling_price,
            currency=data.get('currency', 'INR'),
            preferred_supplier_partner_id=supplier_id,
            status='ACTIVE',
            created_by_user_id=actor_user_id
        )
        db.session.add(product)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PRODUCT_CREATED",
            entity_type="business_product",
            entity_id=product.id,
            after_state=product.serialize(),
            reason="Catalog product created",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return product

    @staticmethod
    def get_products(
        workspace_id: str,
        category: str = None,
        status: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = BusinessProduct.query.filter_by(workspace_id=workspace_id)
        if category:
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status.upper())
        if search:
            query = query.filter(
                (BusinessProduct.name.ilike(f"%{search}%")) |
                (BusinessProduct.sku.ilike(f"%{search}%"))
            )

        total = query.count()
        products = query.order_by(BusinessProduct.name.asc()).offset(offset).limit(min(limit, 100)).all()
        return [p.serialize() for p in products], total

    @staticmethod
    def get_product_by_id(workspace_id: str, product_id: str) -> BusinessProduct:
        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
        if not product:
            raise APIError("Product not found in this workspace.", "NOT_FOUND", 404)
        return product

    @staticmethod
    def update_product(
        workspace_id: str,
        actor_user_id: str,
        product_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessProduct:
        product = ProductService.get_product_by_id(workspace_id, product_id)
        before_state = product.serialize()

        if 'name' in data:
            name = (data['name'] or '').strip()
            if not name:
                raise APIError("Product 'name' cannot be empty.", "VALIDATION_ERROR", 400)
            product.name = name

        if 'category' in data:
            product.category = data['category']

        if 'unit' in data:
            unit = (data['unit'] or '').upper()
            if unit in ProductService.VALID_UNITS:
                product.unit = unit

        if 'reorder_level' in data:
            product.reorder_level = Decimal(str(data['reorder_level']))
        if 'safety_stock' in data:
            product.safety_stock = Decimal(str(data['safety_stock']))
        if 'cost_price' in data:
            product.cost_price = Decimal(str(data['cost_price']))
        if 'selling_price' in data:
            product.selling_price = Decimal(str(data['selling_price']))

        if product.reorder_level < 0 or product.safety_stock < 0 or product.cost_price < 0 or product.selling_price < 0:
            raise APIError("Pricing and threshold values must be non-negative.", "VALIDATION_ERROR", 400)

        if 'preferred_supplier_partner_id' in data:
            sup_id = data['preferred_supplier_partner_id']
            if sup_id:
                sup = CommercialPartner.query.filter_by(id=sup_id, workspace_id=workspace_id).first()
                if not sup:
                    raise APIError("Supplier not found in this workspace.", "VALIDATION_ERROR", 400)
            product.preferred_supplier_partner_id = sup_id

        if 'status' in data:
            status = (data['status'] or '').upper()
            if status in ProductService.VALID_STATUSES:
                product.status = status

        product.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PRODUCT_UPDATED",
            entity_type="business_product",
            entity_id=product.id,
            before_state=before_state,
            after_state=product.serialize(),
            reason="Product catalog updated",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return product

    @staticmethod
    def archive_product(
        workspace_id: str,
        actor_user_id: str,
        product_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessProduct:
        product = ProductService.get_product_by_id(workspace_id, product_id)
        before_state = product.serialize()
        product.status = 'ARCHIVED'
        product.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PRODUCT_ARCHIVED",
            entity_type="business_product",
            entity_id=product.id,
            before_state=before_state,
            after_state=product.serialize(),
            reason="Product archived",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return product

    @staticmethod
    def delete_product(
        workspace_id: str,
        actor_user_id: str,
        product_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        product = ProductService.get_product_by_id(workspace_id, product_id)

        # Check if historical stock movements exist
        has_movements = BusinessStockMovement.query.filter_by(product_id=product_id).first() is not None
        if has_movements:
            raise APIError("Cannot delete product with historical stock movements. Archive the product instead.", "INTEGRITY_ERROR", 400)

        before_state = product.serialize()
        db.session.delete(product)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PRODUCT_DELETED",
            entity_type="business_product",
            entity_id=product_id,
            before_state=before_state,
            after_state=None,
            reason="Product deleted (zero historical movements)",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return True
