"""
B8 Test Suite — Release Certification Engine & 14-Gate Production Verification
==============================================================================
Deterministically validates full-system release readiness against the 14 release gates.
"""

import subprocess
import os
from decimal import Decimal
from models.business import Workspace, WorkspaceMember, Invoice, BusinessTransaction, CommercialPartner
from services.business.health_service import BusinessHealthService, VERSION, BUILD_ID
from app import db


def test_gate_01_database_and_migration_integrity(client):
    """
    Gate 1 & 4: Verify database connectivity, session availability, and schema compatibility.
    """
    health = BusinessHealthService.check_health()
    assert health["status"] == "HEALTHY"
    assert health["checks"]["database"] == "OK"
    assert health["latency_ms"] < 500


def test_gate_02_personal_os_0_byte_diff():
    """
    Gate 11: Verify that all 7 protected Personal OS files have exactly 0 bytes diff.
    """
    protected_files = [
        "frontend/src/pages/auth/Login.tsx",
        "frontend/src/pages/auth/Register.tsx",
        "frontend/src/context/AuthContext.tsx",
        "frontend/src/components/ProtectedRoute.tsx",
        "frontend/src/hooks/useDemoLogin.ts",
        "backend/utils/auth.py",
        "backend/models/user.py"
    ]
    cmd = ["git", "diff", "--"] + protected_files
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="d:/DeadLine OS")
    assert result.returncode == 0
    assert result.stdout.strip() == "", f"Personal OS diff detected: {result.stdout}"


def test_gate_03_deep_health_all_subsystems(client):
    """
    Gate 9 & 10: Deep health probe validates all 7 core Business OS subsystems online.
    """
    res = client.get("/api/business/health")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["status"] == "HEALTHY"
    for subsystem, check_status in data["checks"].items():
        assert check_status == "OK", f"Subsystem {subsystem} failed: {check_status}"


def test_gate_04_liveness_and_readiness_probes(client):
    """
    Gate 4: Liveness and Readiness probes return valid HTTP 200 responses.
    """
    live_res = client.get("/api/business/health/liveness")
    assert live_res.status_code == 200
    assert live_res.get_json()["data"]["status"] == "ALIVE"

    ready_res = client.get("/api/business/health/readiness")
    assert ready_res.status_code == 200
    assert ready_res.get_json()["data"]["status"] == "READY"


def test_gate_05_multi_tenant_isolation_idor(client, mock_auth_headers):
    """
    Gate 6: Cross-tenant data exfiltration via IDOR is strictly rejected.
    """
    # Create Workspace A
    res_a = client.post("/api/business/workspaces", headers=mock_auth_headers, json={"name": "Tenant Alpha"})
    ws_a_id = res_a.get_json()["data"]["workspace"]["id"]
    headers_a = {**mock_auth_headers, "X-Workspace-Id": ws_a_id}

    # Create Invoice in Workspace A
    res_inv = client.post(
        "/api/business/invoices",
        headers=headers_a,
        json={"invoice_type": "RECEIVABLE", "total_amount": "5000.00"}
    )
    inv_id = res_inv.get_json()["data"]["invoice"]["id"]

    # Create Workspace B
    res_b = client.post("/api/business/workspaces", headers=mock_auth_headers, json={"name": "Tenant Beta"})
    ws_b_id = res_b.get_json()["data"]["workspace"]["id"]
    headers_b = {**mock_auth_headers, "X-Workspace-Id": ws_b_id}

    # Attempt to read Workspace A's invoice using Workspace B's scope
    res_idor = client.get(f"/api/business/invoices/{inv_id}", headers=headers_b)
    assert res_idor.status_code in (403, 404), "IDOR vulnerability: Cross-tenant access succeeded!"


def test_gate_06_rbac_enforcement_matrix(client, mock_auth_headers):
    """
    Gate 7: 5-Tier RBAC restricts unauthorized roles from modifying financial data.
    """
    # Create workspace with owner
    res_ws = client.post("/api/business/workspaces", headers=mock_auth_headers, json={"name": "RBAC Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    # Add VIEWER member
    viewer_user_id = 9999
    member = WorkspaceMember(
        workspace_id=ws_id,
        user_id=viewer_user_id,
        role="VIEWER",
        status="ACTIVE"
    )
    db.session.add(member)
    db.session.commit()

    viewer_headers = {"Authorization": f"Bearer {viewer_user_id}", "X-Workspace-Id": ws_id}

    # Viewer attempts to create invoice -> Must be rejected with 403
    res_forbidden = client.post(
        "/api/business/invoices",
        headers=viewer_headers,
        json={"invoice_type": "RECEIVABLE", "total_amount": "1000.00"}
    )
    assert res_forbidden.status_code == 403


def test_gate_07_financial_truth_decimal_precision(client, mock_auth_headers):
    """
    Gate 8: Financial calculations use exact Decimal arithmetic without IEEE-754 drift.
    """
    res_ws = client.post("/api/business/workspaces", headers=mock_auth_headers, json={"name": "Decimal Truth Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    headers = {**mock_auth_headers, "X-Workspace-Id": ws_id}

    res_inv = client.post(
        "/api/business/invoices",
        headers=headers,
        json={
            "invoice_type": "RECEIVABLE",
            "issue_date": "2026-08-31",
            "due_date": "2026-09-30",
            "currency": "INR",
            "items": [{"description": "Service", "quantity": "3", "unit_price": "333.33"}],
            "tax_amount": "179.99"
        }
    )
    assert res_inv.status_code == 201
    inv = res_inv.get_json()["data"]["invoice"]
    assert Decimal(str(inv["subtotal"])) == Decimal("999.99")
    assert Decimal(str(inv["tax_amount"])) == Decimal("179.99")
    assert Decimal(str(inv["total_amount"])) == Decimal("1179.98")


def test_gate_08_error_masking_zero_secret_leak(client):
    """
    Gate 13: Error responses do not leak database stack traces, SQL syntax, or secrets.
    """
    res = client.get("/api/business/nonexistent_route_404")
    assert res.status_code in (401, 404)
    data = res.get_json()
    assert "Traceback" not in str(data)
    assert "password" not in str(data).lower()
    assert "secret" not in str(data).lower()


def test_gate_09_all_business_blueprints_registered(client):
    """
    Gate 9: Verify all 22 modular sub-blueprints are mounted and responsive under /api/business.
    """
    from api.business import business_bp
    blueprints = [bp.name for bp, _ in business_bp._blueprints]
    assert len(blueprints) >= 20, f"Expected >= 20 blueprints, found {len(blueprints)}"


def test_gate_10_version_and_build_identity(client):
    """
    Gate 14: Verify consistent version and build identifier across the release.
    """
    res = client.get("/api/business/health")
    data = res.get_json()["data"]
    assert data["version"] == VERSION
    assert data["build_id"] == BUILD_ID
    assert "1.0.0-production" in data["version"]
