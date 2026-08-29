"""
B2 Test Suite — Capture Ingestion
=================================
Tests text prompt capture, multipart file upload, SHA-256 fingerprinting,
and duplicate artifact detection.
"""

import io
import uuid


def test_text_capture_creates_staged_item(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    # Create workspace
    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Text Capture Co"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Ingest text prompt
    res_cap = client.post(
        "/api/business/capture/text",
        headers=ws_headers,
        json={"text": "Bought server hardware from Dell India for 1.5 lakh on 2026-08-29"}
    )
    assert res_cap.status_code == 201
    data = res_cap.get_json()["data"]["staged_extraction"]
    assert data["status"] == "NEEDS_REVIEW"
    assert data["source_channel"] == "TEXT_PROMPT"
    assert data["normalized_data"]["amount"] == "150000.00"
    assert data["normalized_data"]["currency"] == "INR"
    assert data["normalized_data"]["date"] == "2026-08-29"


def test_file_upload_ingestion_and_duplicate_flag(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}"}

    res_ws = client.post("/api/business/workspaces", headers={**headers, "Content-Type": "application/json"}, json={"name": "File Capture Co"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Upload valid PDF invoice
    pdf_content = b"%PDF-1.4 Mock Invoice Content for Reliance Retail 5000"
    data = {
        'file': (io.BytesIO(pdf_content), 'invoice_aug29.pdf', 'application/pdf'),
        'artifact_type': 'DOCUMENT'
    }

    res_upload = client.post(
        "/api/business/capture/upload",
        headers=ws_headers,
        data=data,
        content_type='multipart/form-data'
    )
    assert res_upload.status_code == 201
    upload_data = res_upload.get_json()["data"]
    assert upload_data["is_duplicate"] is False
    assert upload_data["artifact"]["file_name"] == "invoice_aug29.pdf"
    assert upload_data["staged_extraction"]["status"] == "NEEDS_REVIEW"

    # 2. Re-upload identical file (duplicate fingerprinting check)
    res_dupe = client.post(
        "/api/business/capture/upload",
        headers=ws_headers,
        data={'file': (io.BytesIO(pdf_content), 'invoice_aug29_copy.pdf', 'application/pdf')},
        content_type='multipart/form-data'
    )
    assert res_dupe.status_code == 201
    assert res_dupe.get_json()["data"]["is_duplicate"] is True
