"""
DeadlineOS — Health, Readiness & Liveness Probe Tests
======================================================
Verifies that all monitoring and operational endpoints meet production specifications.
"""

def test_root_and_api_liveness_probes(client):
    """Verify liveness probe returns HTTP 200 without DB/network dependencies."""
    res_api = client.get("/api/live")
    assert res_api.status_code == 200
    data_api = res_api.get_json()
    assert data_api["status"] == "alive"
    assert data_api["service"] == "DeadlineOS"

    res_root = client.get("/live")
    assert res_root.status_code == 200
    data_root = res_root.get_json()
    assert data_root["status"] == "alive"


def test_root_and_api_health_probes(client):
    """Verify general health probe returns HTTP 200 and component statuses."""
    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    data = res_api.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "DeadlineOS"
    assert data["database"] == "connected"

    res_root = client.get("/health")
    assert res_root.status_code == 200
    data_root = res_root.get_json()
    assert data_root["status"] == "healthy"


def test_root_and_api_readiness_probes(client):
    """Verify readiness probe confirms database connectivity."""
    res_api = client.get("/api/ready")
    assert res_api.status_code == 200
    data = res_api.get_json()
    assert data["status"] == "ready"
    assert data["dependencies"]["database"] == "ok"

    res_root = client.get("/ready")
    assert res_root.status_code == 200
    data_root = res_root.get_json()
    assert data_root["status"] == "ready"


def test_health_ai_hierarchy_probe(client):
    """Verify lightweight AI provider status probe."""
    res = client.get("/api/health/ai")
    assert res.status_code == 200
    data = res.get_json()
    assert data["primary"] == "OpenRouter"
    assert data["fallback"] == "Gemini"
    assert data["deterministic"] == "Active"


def test_health_db_endpoint(client):
    """Verify database connectivity endpoint."""
    res = client.get("/api/health/db")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["message"] == "Database reachable"
