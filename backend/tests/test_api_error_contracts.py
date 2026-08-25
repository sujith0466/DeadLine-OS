"""
DeadlineOS — API Error Contracts & Request ID Observability Tests
==================================================================
Verifies standardized JSON error envelopes and request ID propagation.
"""

import uuid


def test_404_standard_error_envelope(client):
    """Verify that 404 error adheres to standard error envelope and includes request ID."""
    custom_id = str(uuid.uuid4())
    res = client.get("/api/non-existent-endpoint-test-404", headers={"X-Request-ID": custom_id})
    assert res.status_code == 404
    data = res.get_json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["request_id"] == custom_id
    assert res.headers.get("X-Request-ID") == custom_id
    assert res.headers.get("X-Correlation-ID") == custom_id


def test_request_id_auto_generation(client):
    """Verify that a request ID is automatically generated when not supplied."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert "X-Correlation-ID" in res.headers
    assert len(res.headers["X-Request-ID"]) > 10


def test_security_headers_present(client):
    """Verify that security headers are attached to all API responses."""
    res = client.get("/api/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
