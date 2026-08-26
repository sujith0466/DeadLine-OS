# DEADLINEOS BUSINESS OS — RISK REGISTER & MITIGATION MATRIX
**Document ID:** `B0-DOC-015`
**Status:** `B0 DESIGN DECISION`
**Classification:** Risk Management & Architectural Controls

---

## 1. Architectural Risk Log

| Risk ID | Category | Severity | Description | Mitigation Strategy | Verification / Test |
|---|---|:---:|---|---|---|
| **`RSK-001`** | **Tenancy** | **CRITICAL** | Developer forgets `workspace_id` filter in a new query, leaking records across workspaces. | Implement a base repository pattern that enforces `workspace_id` in all constructor filters; write automated multi-tenant isolation unit tests. | `test_multi_tenant_isolation.py` |
| **`RSK-002`** | **Security** | **CRITICAL** | Copilot prompt leaks executive salaries or cash reserves to staff members with `MEMBER` role. | Copilot service queries data through an RBAC-aware repository that strips forbidden columns before building LLM context. | `test_copilot_rbac_isolation.py` |
| **`RSK-003`** | **Financial** | **HIGH** | Floating-point conversion in JavaScript or Python causes rounding loss (e.g. ₹0.01 discrepancy). | Store as `NUMERIC(15, 2)` in PostgreSQL; serialize as String in JSON API payloads; parse with Python `Decimal`. | `test_decimal_precision.py` |
| **`RSK-004`** | **Integrity**| **HIGH** | Ingestion pipeline auto-commits an inaccurate OCR amount directly to the financial ledger. | Implement mandatory Staging Queue (`StagedExtraction`). Only manual review confirmation can commit an invoice/transaction. | `test_staging_barrier.py` |
| **`RSK-005`** | **Storage**  | **HIGH** | Container restarts on Render destroy uploaded invoice PDFs stored on the ephemeral disk. | Implement `StorageService` cloud driver (Supabase Storage / S3) immediately in B1 foundation; prohibit local disk storage. | `test_storage_persistence.py` |
| **`RSK-006`** | **Integration**| **HIGH** | Business OS changes accidentally break certified Personal OS Phase 0–8 tests. | Forward-only Alembic migrations; completely isolated table prefixes (`business_`); continuous regression runs of all 162 Personal tests. | `pytest backend/tests/` (162 tests) |
| **`RSK-007`** | **Concurrency**| **MEDIUM**| Eventlet worker causes async socket issues on high-volume document streaming. | Isolate long-running document extractions into bounded thread pools; plan ASGI migration in Phase B8. | `test_concurrent_uploads.py` |
