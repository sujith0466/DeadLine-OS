"""
DeadlineOS Business OS — Blueprint Registration
===============================================
Mounts all Business OS sub-blueprints under unified /api/business.
"""

from flask import Blueprint
from .workspaces import workspaces_bp
from .members import members_bp
from .partners import partners_bp
from .audit import audit_bp
from .capture import capture_bp
from .staging import staging_bp
from .invoices import invoices_bp
from .transactions import transactions_bp
from .allocations import allocations_bp
from .financial import financial_bp
from .copilot import copilot_bp
from .risk import risk_bp
from .bridge import bridge_bp
from .rescue import rescue_bp
from .reminders import reminders_bp
from .exports import exports_bp
from .recurring import recurring_bp
from .automation import automation_bp
from .entities import entities_bp
from .consolidation import consolidation_bp
from .intelligence import intelligence_bp
from .health import health_bp
from .tasks import tasks_bp
from .products import products_bp
from .locations import locations_bp
from .inventory import inventory_bp
from .procurement import procurement_bp
from .purchase_orders import purchase_orders_bp
from .goods_receipts import goods_receipts_bp
from .operational_intelligence import operational_intelligence_bp
from .alerts import alerts_bp
from .voice_operations import voice_ops_bp
from .exchange_rates import exchange_rates_bp
from .batches import batches_bp
from .serials import serials_bp
from .landed_cost import landed_cost_bp

business_bp = Blueprint('business', __name__, url_prefix='/api/business')

# Register modular sub-blueprints
business_bp.register_blueprint(workspaces_bp)
business_bp.register_blueprint(members_bp)
business_bp.register_blueprint(partners_bp)
business_bp.register_blueprint(audit_bp)
business_bp.register_blueprint(capture_bp)
business_bp.register_blueprint(staging_bp)
business_bp.register_blueprint(invoices_bp)
business_bp.register_blueprint(transactions_bp)
business_bp.register_blueprint(allocations_bp)
business_bp.register_blueprint(financial_bp)
business_bp.register_blueprint(copilot_bp)
business_bp.register_blueprint(risk_bp)
business_bp.register_blueprint(bridge_bp)
business_bp.register_blueprint(rescue_bp)
business_bp.register_blueprint(reminders_bp)
business_bp.register_blueprint(exports_bp)
business_bp.register_blueprint(recurring_bp)
business_bp.register_blueprint(automation_bp)
business_bp.register_blueprint(entities_bp)
business_bp.register_blueprint(consolidation_bp)
business_bp.register_blueprint(intelligence_bp)
business_bp.register_blueprint(health_bp)
business_bp.register_blueprint(tasks_bp)
business_bp.register_blueprint(products_bp)
business_bp.register_blueprint(locations_bp)
business_bp.register_blueprint(inventory_bp)
business_bp.register_blueprint(procurement_bp)
business_bp.register_blueprint(purchase_orders_bp)
business_bp.register_blueprint(goods_receipts_bp, url_prefix='/procurement/goods-receipts')
business_bp.register_blueprint(operational_intelligence_bp, url_prefix='/intelligence/operations')
business_bp.register_blueprint(alerts_bp, url_prefix='/operations/alerts')
business_bp.register_blueprint(voice_ops_bp, url_prefix='/operations/voice')
business_bp.register_blueprint(exchange_rates_bp, url_prefix='/exchange-rates')
business_bp.register_blueprint(batches_bp, url_prefix='/batches')
business_bp.register_blueprint(serials_bp, url_prefix='/serials')
business_bp.register_blueprint(landed_cost_bp, url_prefix='/landed-cost')

__all__ = ['business_bp']
