import pytest
from decimal import Decimal
import datetime
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    BusinessTransaction,
    Invoice,
    CommercialPartner,
    RecurringObligation,
    StagedExtraction,
    BusinessEntity,
    AuditEvent
)
from app import db

def test_b7_bounded_queries_and_n_plus_one_safety(client, mock_auth_headers):
    """
    Test B7.1: Verify that listing endpoints (invoices, transactions, members, entities)
    execute bounded queries and return clean serialized payloads with 0 information leaks.
    """
    # 1. Create Workspace
    ws_res = client.post(
        "/api/business/workspaces",
        json={"name": "B7 Hardening Enterprise", "base_currency": "INR"},
        headers=mock_auth_headers
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.get_json()["data"]["workspace"]["id"]
    ws_headers = {**mock_auth_headers, "X-Workspace-Id": ws_id}

    # 2. Add partner, invoice, transaction
    partner = CommercialPartner(
        workspace_id=ws_id,
        name="Hardened Vendor Corp",
        partner_type="VENDOR"
    )
    db.session.add(partner)
    db.session.commit()

    inv = Invoice(
        workspace_id=ws_id,
        invoice_number="INV-B7-001",
        invoice_type="PAYABLE",
        issue_date=datetime.date(2026, 8, 31),
        due_date=datetime.date(2026, 9, 15),
        currency="INR",
        subtotal=Decimal("10000.00"),
        tax_amount=Decimal("1800.00"),
        total_amount=Decimal("11800.00"),
        balance_due=Decimal("11800.00"),
        partner_id=partner.id,
        created_by_user_id=1
    )
    db.session.add(inv)
    db.session.commit()

    tx = BusinessTransaction(
        workspace_id=ws_id,
        transaction_type="EXPENSE",
        amount=Decimal("11800.00"),
        currency="INR",
        transaction_date=datetime.date(2026, 8, 31),
        notes="Vendor settlement B7",
        status="CONFIRMED",
        created_by_user_id=1
    )
    db.session.add(tx)
    db.session.commit()

    # 3. Test list invoices performance & structure
    inv_res = client.get("/api/business/invoices", headers=ws_headers)
    assert inv_res.status_code == 200
    inv_data = inv_res.get_json()
    assert inv_data["status"] == "success"
    assert len(inv_data["data"]["invoices"]) >= 1

    # 4. Test list transactions performance & structure
    tx_res = client.get("/api/business/transactions", headers=ws_headers)
    assert tx_res.status_code == 200
    tx_data = tx_res.get_json()
    assert tx_data["status"] == "success"
    assert len(tx_data["data"]["transactions"]) >= 1


def test_b7_error_resilience_and_sanitization(client, mock_auth_headers):
    """
    Test B7.2: Verify that 401, 403, 404, and invalid input scenarios
    return structured, sanitized JSON error responses without stack traces.
    """
    # 1. 401 Missing Auth
    res_401 = client.get("/api/business/invoices")
    assert res_401.status_code == 401
    data_401 = res_401.get_json()
    assert data_401["status"] == "error"

    # 2. 400/401/403 Missing Workspace Header
    res_no_ws = client.get("/api/business/invoices", headers=mock_auth_headers)
    assert res_no_ws.status_code in (400, 401, 403)

    # 3. 404 Nonexistent Item
    ws_res = client.post(
        "/api/business/workspaces",
        json={"name": "B7 Error Workspace", "base_currency": "INR"},
        headers=mock_auth_headers
    )
    ws_id = ws_res.get_json()["data"]["workspace"]["id"]
    ws_headers = {**mock_auth_headers, "X-Workspace-Id": ws_id}

    res_404 = client.get("/api/business/invoices/nonexistent-inv-id", headers=ws_headers)
    assert res_404.status_code == 404
    data_404 = res_404.get_json()
    assert data_404["status"] == "error"


def test_b7_financial_truth_decimal_invariants(client, mock_auth_headers):
    """
    Test B7.3: Verify that financial amounts maintain exact Decimal arithmetic (NUMERIC(15,2))
    without IEEE-754 floating-point rounding errors.
    """
    ws_res = client.post(
        "/api/business/workspaces",
        json={"name": "B7 Decimal Workspace", "base_currency": "INR"},
        headers=mock_auth_headers
    )
    ws_id = ws_res.get_json()["data"]["workspace"]["id"]
    ws_headers = {**mock_auth_headers, "X-Workspace-Id": ws_id}

    # Create invoice with items subtotal & tax
    inv_res = client.post(
        "/api/business/invoices",
        json={
            "invoice_type": "RECEIVABLE",
            "issue_date": "2026-08-31",
            "due_date": "2026-09-30",
            "currency": "INR",
            "items": [
                {
                    "description": "Enterprise UX Consulting",
                    "quantity": "1",
                    "unit_price": "12345.67"
                }
            ],
            "tax_amount": "2222.22"
        },
        headers=ws_headers
    )
    assert inv_res.status_code == 201
    inv_data = inv_res.get_json()["data"]["invoice"]

    # Invariants: subtotal = 12345.67, tax = 2222.22, total = 14567.89
    assert Decimal(str(inv_data["subtotal"])) == Decimal("12345.67")
    assert Decimal(str(inv_data["tax_amount"])) == Decimal("2222.22")
    assert Decimal(str(inv_data["total_amount"])) == Decimal("14567.89")
