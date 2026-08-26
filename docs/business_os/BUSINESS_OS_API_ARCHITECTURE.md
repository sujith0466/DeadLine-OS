# DEADLINEOS BUSINESS OS — API ARCHITECTURE & CONTRACT SPECIFICATION
**Document ID:** `B0-DOC-009`
**Status:** `B0 DESIGN DECISION`
**Classification:** Interface Architecture

---

## 1. API Conventions & Headers
- **Base Route Prefix:** `/api/business`
- **Authentication Header:** `Authorization: Bearer <Supabase_JWT>`
- **Tenancy Header (Required):** `X-Workspace-Id: <workspace_uuid>`
- **Idempotency Header (Required for mutations):** `Idempotency-Key: <uuid>`

---

## 2. API Endpoint Catalog

### 2.1 Workspace & Member Endpoints
- `POST /api/business/workspaces` — Create new workspace (`name`, `legal_name`, `base_currency`, `timezone`).
- `GET /api/business/workspaces` — List workspaces where current user is an active member.
- `GET /api/business/workspaces/current` — Get active workspace profile & metadata.
- `GET /api/business/members` — List members in current workspace.
- `POST /api/business/members/invite` — Invite new member by email with specified role.

### 2.2 Commercial Partner Registry Endpoints
- `GET /api/business/partners` — List partners (query params: `type=CUSTOMER|SUPPLIER`, `search=...`).
- `POST /api/business/partners` — Create partner (`name`, `tax_id`, `phone`, `credit_period_days`).
- `GET /api/business/partners/<id>` — Partner detail with active receivable/payable aging breakdown.

### 2.3 Invoices & Receivables/Payables Endpoints
- `GET /api/business/invoices` — List invoices (filter: `direction`, `status`, `due_before`).
- `POST /api/business/invoices` — Issue/Record invoice.
- `GET /api/business/invoices/<id>` — Invoice detail and settlement history.
- `POST /api/business/invoices/<id>/payments` — Record payment against invoice.

### 2.4 Financial Transactions & Cash Runway Endpoints
- `GET /api/business/transactions` — List transactions (filter: `start_date`, `end_date`, `type`).
- `POST /api/business/transactions` — Record manual transaction.
- `POST /api/business/transactions/<id>/reverse` — Reverse transaction (Admin/Owner only).
- `GET /api/business/financials/runway` — Get confirmed cash, committed in/out, and 30-day projection.

### 2.5 Ingestion & Staging Endpoints
- `POST /api/business/capture/upload` — Upload multipart file (PDF/Image/Audio).
- `GET /api/business/staging/pending` — List extractions awaiting human review.
- `POST /api/business/staging/<id>/confirm` — Confirm staged extraction into authoritative invoice/transaction.
- `POST /api/business/staging/<id>/reject` — Reject incorrect extraction.

### 2.6 Copilot & Intelligence Endpoints
- `POST /api/business/copilot/query` — Natural language operational/financial query.
- `GET /api/business/intelligence/risks` — Get active business risks (overdue receivables, cash bottlenecks).

---

## 3. Standard Response & Error Envelopes

### Success Envelope
```json
{
  "status": "success",
  "message": "Invoice recorded successfully",
  "data": {
    "id": "inv_8f9c11a0",
    "invoice_number": "INV-2026-004",
    "total_amount": "25000.00",
    "currency": "INR",
    "status": "ISSUED"
  },
  "request_id": "req_9921b7ce"
}
```

### Error Envelope
```json
{
  "status": "error",
  "error": {
    "code": "WORKSPACE_PERMISSION_DENIED",
    "message": "Your role (MEMBER) does not permit transaction reversals."
  },
  "request_id": "req_9921b7ce"
}
```
