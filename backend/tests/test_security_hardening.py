"""
DeadlineOS — Authentication & Security Hardening Tests
========================================================
Verifies JWT authentication enforcement and unauthorized request rejection.
"""

def test_unauthenticated_request_rejected(client):
    """Verify that protected API endpoints return 401 when Authorization header is absent."""
    protected_endpoints = [
        ("GET", "/api/tasks"),
        ("GET", "/api/goals"),
        ("GET", "/api/habits"),
        ("GET", "/api/runtime/active"),
        ("POST", "/api/recovery/skip-today"),
        ("GET", "/api/analytics/overview"),
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            res = client.get(path)
        elif method == "POST":
            res = client.post(path, json={})
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"


def test_authenticated_request_allowed(client, mock_auth_headers):
    """Verify that protected endpoints succeed when valid Authorization token is provided."""
    res = client.get("/api/tasks", headers=mock_auth_headers)
    assert res.status_code == 200


def test_cors_preflight_unrestricted_for_options(client):
    """Verify that OPTIONS preflight requests do not require authentication."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization,Content-Type"
    }
    res = client.options("/api/tasks", headers=headers)
    assert res.status_code == 200
