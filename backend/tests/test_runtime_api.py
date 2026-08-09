import pytest
from app import create_app
from database.db import db
from models.user import User
import uuid

def test_runtime_api_flow(client, mock_auth_headers):
    # 1. Check active (should be None)
    res = client.get('/api/runtime/active', headers=mock_auth_headers)
    assert res.status_code == 200
    assert res.json['active'] is False
    
    # 2. Start
    res = client.post('/api/runtime/start', json={
        "entity_id": "task-123",
        "entity_type": "TASK"
    }, headers=mock_auth_headers)
    assert res.status_code == 200
    assert "runtime_id" in res.json
    
    # 3. Check active
    res = client.get('/api/runtime/active', headers=mock_auth_headers)
    assert res.status_code == 200
    assert res.json['active'] is True
    assert res.json['status'] == 'RUNNING'
    
    # 4. Pause
    res = client.post('/api/runtime/pause', json={
        "entity_id": "task-123"
    }, headers=mock_auth_headers)
    assert res.status_code == 200
    
    # 5. Resume
    res = client.post('/api/runtime/resume', json={
        "entity_id": "task-123"
    }, headers=mock_auth_headers)
    assert res.status_code == 200
    
    # 6. Complete
    res = client.post('/api/runtime/complete', json={
        "entity_id": "task-123"
    }, headers=mock_auth_headers)
    assert res.status_code == 200
    
    # 7. Check active (should be None again)
    res = client.get('/api/runtime/active', headers=mock_auth_headers)
    assert res.status_code == 200
    assert res.json['active'] is False
