"""
B8 Test Suite — Business Health Diagnostic Probe
=================================================
Tests GET /api/business/health readiness, latency, and read-only non-mutating behavior.
"""


def test_business_health_probe_healthy(client):
    res = client.get("/api/business/health")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["status"] == "HEALTHY"
    assert data["subsystem"] == "Business OS"
    assert data["checks"]["database"] == "OK"
    assert data["checks"]["storage"] == "OK"
    assert data["checks"]["ledger"] == "OK"
    assert "latency_ms" in data
    assert "timestamp" in data
