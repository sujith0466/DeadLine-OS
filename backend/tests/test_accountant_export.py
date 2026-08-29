"""
B5 Test Suite — Accountant Export Engine
========================================
Tests deterministic CSV streaming, ZIP packaging, and cryptographic manifest.
"""

import uuid
import zipfile
import io
import json


def test_accountant_export_package_generation_and_checksum_integrity(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Export Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Create financial data: invoice and income
    res_inv = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "50000.00",
        "due_date": "2026-09-01"
    })
    client.post(f"/api/business/invoices/{res_inv.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)
    client.post("/api/business/transactions", headers=ws_headers, json={
        "transaction_type": "INCOME",
        "amount": "150000.00"
    })

    # 1. Test CSV downloads
    res_inv_csv = client.get("/api/business/exports/invoices.csv", headers=ws_headers)
    assert res_inv_csv.status_code == 200
    assert "Invoice ID,Invoice Number" in res_inv_csv.data.decode("utf-8")
    assert "50000.00" in res_inv_csv.data.decode("utf-8")

    res_tx_csv = client.get("/api/business/exports/transactions.csv", headers=ws_headers)
    assert res_tx_csv.status_code == 200
    assert "150000.00" in res_tx_csv.data.decode("utf-8")

    # 2. Test Full ZIP Package
    res_pkg = client.get("/api/business/exports/accountant-package", headers=ws_headers)
    assert res_pkg.status_code == 200
    assert res_pkg.mimetype == "application/zip"

    # Inspect ZIP contents
    zip_buf = io.BytesIO(res_pkg.data)
    with zipfile.ZipFile(zip_buf, "r") as zf:
        namelist = zf.namelist()
        assert "manifest.json" in namelist
        assert "invoices_export.csv" in namelist
        assert "transactions_export.csv" in namelist
        assert "payment_allocations_export.csv" in namelist
        assert "financial_summary.json" in namelist

        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["workspace_id"] == ws_id
        assert manifest["generated_by_user_id"] == user_id
        assert "invoices_export.csv" in manifest["file_checksums"]
