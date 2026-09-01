"""
DeadlineOS Business OS — Product Catalog Endpoints
===================================================
Handles product creation, catalog browsing, metadata updates, and archival.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.product_service import ProductService

products_bp = Blueprint('biz_products', __name__)


@products_bp.route('/products', methods=['GET'])
@require_workspace('inventory:read')
def list_products():
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('search')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        products, total = ProductService.get_products(
            workspace_id=g.workspace_id,
            category=category,
            status=status,
            search=search,
            limit=limit,
            offset=offset
        )
        return success_response(data={"products": products, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@products_bp.route('/products', methods=['POST'])
@require_workspace('inventory:create')
def create_product():
    data = request.get_json(silent=True) or {}
    try:
        product = ProductService.create_product(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"product": product.serialize()},
            message="Product created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@products_bp.route('/products/<product_id>', methods=['GET'])
@require_workspace('inventory:read')
def get_product(product_id):
    try:
        product = ProductService.get_product_by_id(g.workspace_id, product_id)
        return success_response(data={"product": product.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@products_bp.route('/products/<product_id>', methods=['PUT'])
@require_workspace('inventory:update')
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    try:
        product = ProductService.update_product(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            product_id=product_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"product": product.serialize()},
            message="Product updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@products_bp.route('/products/<product_id>/archive', methods=['POST'])
@require_workspace('inventory:update')
def archive_product(product_id):
    try:
        product = ProductService.archive_product(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            product_id=product_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"product": product.serialize()},
            message="Product archived successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@products_bp.route('/products/<product_id>', methods=['DELETE'])
@require_workspace('inventory:delete')
def delete_product(product_id):
    try:
        ProductService.delete_product(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            product_id=product_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(message="Product deleted successfully.")
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
