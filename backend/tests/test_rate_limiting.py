"""
DeadlineOS — Rate Limiting & Abuse Protection Tests
=====================================================
Verifies endpoint rate limiting and OPTIONS preflight exemption.
"""

def test_options_preflight_exempt_from_rate_limits(client):
    """Verify that OPTIONS requests are exempt from rate limiting."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization"
    }
    for _ in range(10):
        res = client.options("/api/health", headers=headers)
        assert res.status_code == 200
