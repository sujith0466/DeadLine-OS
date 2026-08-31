"""
B8 Test Suite — Business Health Diagnostic Probe
=================================================
Tests GET /api/business/health, /liveness, /readiness, latency, and read-only non-mutating behavior.
"""

from models.business import Workspace, Invoice, BusinessTransaction


def test_business_health_probe_healthy(client):
    """
    Test B8.1: Verify deep health probe checks all 7 subsystems and returns 200 with structured telemetry.
    """
    res = client.get("/api/business/health")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["status"] == "HEALTHY"
    assert data["subsystem"] == "Business OS"
    assert data["version"] == "1.0.0-production"
    assert "build_id" in data
    assert "latency_ms" in data
    assert "timestamp" in data

    # All 7 subsystem checks
    checks = data["checks"]
    assert checks["database"] == "OK"
    assert checks["storage"] == "OK"
    assert checks["ledger"] == "OK"
    assert checks["intelligence"] == "OK"
    assert checks["consolidation"] == "OK"
    assert checks["automation"] == "OK"
    assert checks["auth_rbac"] == "OK"

    # Subsystem latencies present
    assert "database" in data["subsystem_latencies"]
    assert "ledger" in data["subsystem_latencies"]


def test_business_liveness_probe(client):
    """
    Test B8.2: Verify lightweight liveness endpoint returns ALIVE status with zero DB dependencies.
    """
    res = client.get("/api/business/health/liveness")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["status"] == "ALIVE"
    assert data["subsystem"] == "Business OS"
    assert data["version"] == "1.0.0-production"
    assert "timestamp" in data


def test_business_readiness_probe(client):
    """
    Test B8.3: Verify readiness endpoint evaluates traffic readiness and returns READY status.
    """
    res = client.get("/api/business/health/readiness")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["status"] == "READY"
    assert data["subsystem"] == "Business OS"
    assert data["database"] == "OK"
    assert "latency_ms" in data
    assert "timestamp" in data


def test_health_probe_is_strictly_non_mutating(client):
    """
    Test B8.4: Verify that running health checks 10 times in sequence causes zero state mutation or record creation.
    """
    ws_count_before = Workspace.query.count()
    inv_count_before = Invoice.query.count()
    tx_count_before = BusinessTransaction.query.count()

    for _ in range(10):
        res = client.get("/api/business/health")
        assert res.status_code == 200

    ws_count_after = Workspace.query.count()
    inv_count_after = Invoice.query.count()
    tx_count_after = BusinessTransaction.query.count()

    assert ws_count_before == ws_count_after
    assert inv_count_before == inv_count_after
    assert tx_count_before == tx_count_after
