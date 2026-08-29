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

__all__ = ['business_bp']
