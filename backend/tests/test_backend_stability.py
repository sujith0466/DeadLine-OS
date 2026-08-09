import uuid


def test_stability_endpoints(client):
    print("=== Phase 2: Backend Stability & Database Audit ===")

    # 1. Invalid payload format
    print("\n[1] Testing Invalid JSON format (Should not 500)")
    res = client.post(
        "/api/tasks", headers={"Content-Type": "application/json"}, data="{bad json"
    )
    print(f"Response: {res.status_code} (Expected 400/401/415)")
    assert res.status_code in [400, 401, 415]

    # 2. Invalid UUIDs for GET requests
    print("\n[2] Testing Bad UUID on GET /tasks/<id>")
    res = client.get("/api/tasks/not-a-uuid")
    print(f"Response: {res.status_code} (Expected 401/404)")
    assert res.status_code in [401, 404]

    # 3. Bad endpoints
    print("\n[3] Testing Non-existent Endpoint")
    res = client.get("/api/does-not-exist")
    print(f"Response: {res.status_code} (Expected 404)")
    assert res.status_code == 404

    print("\nBackend Stability Pass!")
