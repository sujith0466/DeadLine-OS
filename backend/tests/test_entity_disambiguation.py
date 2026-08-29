"""
B2 Test Suite — Entity Resolution & Disambiguation
===================================================
Tests partner matching against CommercialPartner registry.
"""

import uuid
from models.business import CommercialPartner
from services.business.entity_resolution_service import EntityResolutionService
from database.db import db


def test_partner_resolution_exact_and_ambiguous(app):
    with app.app_context():
        ws_id = str(uuid.uuid4())

        # Add partners
        p1 = CommercialPartner(workspace_id=ws_id, partner_type="CUSTOMER", name="Ravi Kumar", status="ACTIVE")
        p2 = CommercialPartner(workspace_id=ws_id, partner_type="SUPPLIER", name="Ravi Stores", status="ACTIVE")
        p3 = CommercialPartner(workspace_id=ws_id, partner_type="BOTH", name="Tata Consultancy Services", status="ACTIVE")
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        # 1. Exact match
        res_exact = EntityResolutionService.resolve_partner(ws_id, "Tata Consultancy Services")
        assert res_exact["status"] == "EXACT_MATCH"
        assert res_exact["partner_id"] == p3.id

        # 2. Ambiguous match (Multiple "Ravi" counterparties)
        res_ambig = EntityResolutionService.resolve_partner(ws_id, "Ravi")
        assert res_ambig["status"] == "AMBIGUOUS_MATCH"
        assert res_ambig["partner_id"] is None
        assert len(res_ambig["candidates"]) == 2

        # 3. No match
        res_none = EntityResolutionService.resolve_partner(ws_id, "Unknown Counterparty Pvt Ltd")
        assert res_none["status"] == "NO_MATCH"
        assert res_none["partner_id"] is None
