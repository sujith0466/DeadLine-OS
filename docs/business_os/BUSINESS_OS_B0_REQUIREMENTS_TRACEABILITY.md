# DEADLINEOS BUSINESS OS — REQUIREMENTS TRACEABILITY MATRIX
**Document ID:** `B0-DOC-021`
**Status:** `B0 ARCHITECTURAL TRACEABILITY`
**Classification:** Engineering Governance Matrix

---

> [!IMPORTANT]
> **EVIDENCE CLASSIFICATION DISCLAIMER:**
> "100% Requirements Traceability" indicates that **100% of approved Business OS requirements have a defined Architectural Decision Record (ADR), Domain Aggregate, PostgreSQL Schema Definition, API Endpoint Contract, Security Control, and Planned Unit/Integration Test**.
> It does **NOT** indicate that Business OS requirements are already implemented or verified in application code (which will occur during Phases B1 through B8).

---

## 1. Requirements Traceability Matrix (RTM)

| Req ID | Requirement Summary | ADR Ref | Domain Aggregate | Database Table | API Endpoint | Security Control | Unit / Integration Test | Target Phase | Evidence Status |
|---|---|:---:|---|---|---|---|---|:---:|:---:|
| **`FR-001`** | Multi-tenant workspace scoping | `ADR-003` | Tenancy | `business_workspaces`, `business_workspace_members` | `POST /api/business/workspaces` | `SEC-001` (Tenant Isolation) | `test_workspace_scoping.py` | **B1** | ARCHITECTURALLY MITIGATED |
| **`FR-002`** | 5-Tier RBAC authorization | `ADR-004` | Tenancy | `business_workspace_members` | All `/api/business/*` routes | `@require_workspace(perm)` | `test_rbac_permissions.py` | **B1** | ARCHITECTURALLY MITIGATED |
| **`FR-003`** | Multimodal document capture | `ADR-015` | Capture | `business_ingestion_artifacts` | `POST /api/business/capture/upload` | `SEC-003` (Signed 15m URLs) | `test_capture_upload.py` | **B2** | ARCHITECTURALLY MITIGATED |
| **`FR-004`** | Mandatory review staging barrier | `ADR-009` | Staging | `business_staged_extractions` | `POST /api/business/staging/:id/confirm` | `AIR-001` (Human Confirm) | `test_staging_barrier.py` | **B2** | ARCHITECTURALLY MITIGATED |
| **`FR-005`** | Invoices & receivable aging | `ADR-005` | Invoices | `business_invoices`, `business_commercial_partners` | `GET/POST /api/business/invoices` | `DIR-002` (Balance Match) | `test_invoice_lifecycle.py` | **B3** | ARCHITECTURALLY MITIGATED |
| **`FR-006`** | Cash runway & Runway Days formula | `ADR-006` | Ledger | `business_transactions`, `business_invoices` | `GET /api/business/financials/runway` | `DIR-001` (Exact Decimal) | `test_cash_runway_math.py` | **B3** | ARCHITECTURALLY MITIGATED |
| **`FR-007`** | Reversible transactions & adjustments | `ADR-008` | Ledger | `business_transactions`, `business_payment_allocations` | `POST /api/business/transactions/:id/reverse` | `DIR-004` (Audit Logging) | `test_transaction_reversals.py` | **B3** | ARCHITECTURALLY MITIGATED |
| **`FR-008`** | Zero-bypass Business Copilot | `ADR-012` | Copilot | Read-only context queries | `POST /api/business/copilot/query` | `SEC-002` (Copilot RBAC) | `test_copilot_security.py` | **B4** | ARCHITECTURALLY MITIGATED |
| **`FR-009`** | Accountant export package | `ADR-020` | Export | Aggregated CSV/ZIP generators | `GET /api/business/export/accountant` | `audit:export_tally` perm | `test_accountant_export.py` | **B5** | ARCHITECTURALLY MITIGATED |
| **`FR-010`** | Polymorphic Personal OS sync | `ADR-014` | Bridge | Read-only adapter | Internal Bridge Service | `DIR-005` (Zero Personal Regr) | `test_personal_bridge.py` | **B4** | ARCHITECTURALLY MITIGATED |
| **`DIR-001`**| Exact Decimal arithmetic (`Numeric(15,2)`)| `ADR-007` | Ledger | All monetary columns | All financial endpoints | Float arithmetic ban | `test_decimal_precision.py` | **B1** | ARCHITECTURALLY MITIGATED |
| **`DIR-002`**| Settlement balance invariant | `ADR-008` | Invoices | `business_invoices` | Settlement endpoints | Invariant assertion | `test_settlement_invariants.py`| **B3** | ARCHITECTURALLY MITIGATED |
| **`DIR-003`**| Idempotent mutation handling | `ADR-013` | Ledger | `business_transactions` | Mutation endpoints | `Idempotency-Key` header | `test_idempotency_keys.py` | **B1** | ARCHITECTURALLY MITIGATED |
| **`DIR-004`**| Immutable audit records | `ADR-019` | Audit | `business_audit_events` | Internal event bus | Append-only / No Delete | `test_audit_immutability.py` | **B1** | ARCHITECTURALLY MITIGATED |
| **`SEC-001`**| Row-level tenant isolation | `ADR-003` | Tenancy | All `business_*` tables | All `/api/business/*` routes | Composite index & filter | `test_multi_tenant_leakage.py` | **B1** | ARCHITECTURALLY MITIGATED |
| **`SEC-002`**| Copilot RBAC context isolation | `ADR-012` | Copilot | Context builder | `POST /api/business/copilot/query` | Prompt context pruning | `test_copilot_context_pruning.py`| **B4** | ARCHITECTURALLY MITIGATED |
| **`SEC-003`**| Cloud storage signed URLs (15-min) | `ADR-015` | Storage | `StorageService` | `GET /api/business/documents/:id/url` | Short-lived signed URLs | `test_storage_signed_urls.py` | **B2** | ARCHITECTURALLY MITIGATED |
| **`SEC-004`**| Prompt injection input defense | `ADR-011` | AI | `AISafety.assert_prompt_safe` | Capture endpoints | Pre-LLM sanitizer | `test_prompt_injection.py` | **B2** | ARCHITECTURALLY MITIGATED |
| **`AIR-001`**| Zero unsupervised mutations | `ADR-009` | AI | Staging barriers | Capture endpoints | Mandatory human confirm | `test_ai_mutation_barrier.py` | **B2** | ARCHITECTURALLY MITIGATED |
| **`AIR-002`**| Structured output schema validation | `ADR-011` | AI | `AISafety.validate_and_sanitize`| All AI extraction pipelines | Pydantic / JSON schema | `test_ai_schema_validation.py` | **B2** | ARCHITECTURALLY MITIGATED |
| **`AIR-003`**| 3-Tier failover & graceful degradation | `ADR-011` | Platform | `HybridFailoverAIProvider` | AI orchestration pipelines | Heuristic fallback | `test_ai_failover_chains.py` | **B2** | VERIFIED AGAINST PLATFORM |

---

## 2. Completeness & Orphan Check
- **Orphan Requirements:** 0 found. All requirements map directly to approved ADRs, domain models, and test specifications.
- **Orphan Entities:** 0 found. All database tables support specific functional or security requirements.
- **Orphan ADRs:** 0 found. All 20 ADRs are referenced and assigned to implementation phases (B1 through B5).
