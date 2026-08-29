# DEADLINEOS BUSINESS OS — MASTER PROGRAM TRACKER
**Document ID:** `B0-DOC-026`
**Status:** `B0 FROZEN / AUTHORITATIVE GOVERNANCE INDEX`
**Classification:** Technical Program Management & Architecture Index
**Author:** DeadlineOS Principal Architecture & Technical Program Management Group
**Timestamp:** 2026-08-26T09:34:00+05:30

---

## Program Identity

- **Program:** DeadlineOS Business OS
- **Personal OS Baseline Commit:** `32e177093c5e6859fcf3be9aa81f1d07a3fca901` (`32e1770`)
- **Personal OS Certified Tag:** `personal-os-v1.0-certified`
- **B0 Architecture Status:** **FROZEN + COMMITTED + TAGGED (`business-os-b0-frozen`)**
- **B1 Implementation Status:** **COMPLETED / IMPLEMENTATION VERIFIED (172/172 tests passing)**
- **B2 Implementation Status:** **COMPLETED / IMPLEMENTATION VERIFIED (181/181 tests passing)**
- **B3 Implementation Status:** **COMPLETED / IMPLEMENTATION VERIFIED (192/192 tests passing)**
- **B4 Implementation Status:** **COMPLETED / IMPLEMENTATION VERIFIED (198/198 tests passing)**
- **B5 Implementation Status:** **COMPLETED / IMPLEMENTATION VERIFIED (204/204 tests passing)**
- **B7 Implementation Status:** **COMPLETED / IMPLEMENTATION VERIFIED (216/216 tests passing)**
- **B8 Implementation Status:** **COMPLETED / IMPLEMENTATION VERIFIED (222/222 tests passing)**
- **Current Program Gate:** **ENTIRE BUSINESS OS PROGRAM FULLY CERTIFIED & RELEASED (v1.0.0-production)**
- **Implementation Status:** **BUSINESS OS ROADMAP (B0–B8) 100% COMPLETE & PRODUCTION READY**

---

## SECTION A — PERSONAL OS BASELINE

| Baseline Dimension | Value / Reference | Status | Verification Evidence |
|---|---|:---:|---|
| **Certified Commit** | `32e177093c5e6859fcf3be9aa81f1d07a3fca901` (`32e1770`) | **FROZEN** | `git rev-parse HEAD` == `32e1770` |
| **Certified Tag** | `personal-os-v1.0-certified` | **FROZEN** | Local & remote tag target `32e1770` |
| **Branch Alignment** | `main` == `origin/main` == `32e1770` | **VERIFIED** | Clean working tree (0 dirty files) |
| **Personal OS Models** | `backend/models/*.py` (16 models) | **FROZEN** | 0 files modified |
| **Personal OS Tests** | `backend/tests/*.py` (162 tests passing) | **FROZEN** | 0 files modified |
| **Production Service** | `https://deadline-os.onrender.com` | **LIVE / VERIFIED** | Render health probes passing |

> [!IMPORTANT]
> **PERMANENT INVARIANT:** Personal OS Phases 0–8 remain permanently frozen. No Business OS task is permitted to modify Personal OS schemas, routes, or tests.

---

## SECTION B — BUSINESS OS PROGRAM ROADMAP (B0–B8)

| Phase | Phase Name | Program Scope & Objectives | Implementation Status | Phase Gate Status |
|:---:|---|---|:---:|:---:|
| **B0** | **Architecture & Validation** | Product definition, multi-tenancy, RBAC, financial truth, decimal arithmetic, AI boundaries, requirements traceability, and red-team review. | **DESIGN ONLY (NO CODE)** | **FROZEN / PASSED** |
| **B1** | **Business Foundation** | Workspace provisioning, member management, 5-tier RBAC middleware, partner registry, base schema migrations. | **IMPLEMENTED (172 TESTS)** | **PASSED / CERTIFIED** |
| **B2** | **Capture & Staging** | Document/voice/text capture, Supabase Storage integration, AI extraction, staging review barrier, entity disambiguation. | **IMPLEMENTED (181 TESTS)** | **PASSED / CERTIFIED** |
| **B3** | **Execution & Ledger** | Invoices, payments, allocations, append-only adjustments, Cash Reality hierarchy, Runway Days math. | **IMPLEMENTED (192 TESTS)** | **PASSED / CERTIFIED** |
| **B4** | **Intelligence & Copilot** | Zero-bypass Business Copilot, cash risk engine, polymorphic Personal OS Today/Calendar bridge adapter. | **IMPLEMENTED (198 TESTS)** | **PASSED / CERTIFIED** |
| **B5** | **Rescue & Accountant Export** | Overdue receivable workflows, collection reminders, CSV/ZIP accountant audit export package. | **IMPLEMENTED (204 TESTS)** | **PASSED / CERTIFIED** |
| **B6** | **Advanced Automation** | Recurring obligation schedules, smart payment tracking, automated cash alert thresholds. | **IMPLEMENTED (210 TESTS)** | **PASSED / CERTIFIED** |
| **B7** | **Commercial Multi-Entity** | Multi-workspace management, client/vendor dual-entity accounting, advanced reporting. | **IMPLEMENTED (216 TESTS)** | **PASSED / CERTIFIED** |
| **B8** | **Production Excellence** | Health diagnostic probes, end-to-end security penetration testing, production hardening. | **IMPLEMENTED (222 TESTS)** | **PASSED / CERTIFIED** |

---

## SECTION C — B0 PASS HISTORY & EVOLUTION

| Pass | Purpose | Key Result & Output | Code Changes? |
|:---:|---|---|:---:|
| **Pass 1** | **Baseline Discovery** | Audited repository; discovered 7 reusable platform primitives and identified 5 critical architectural gaps (no tenancy, no RBAC, no decimal math, no staging barrier, mutable updates). Produced `B0_PASS1_BASELINE_DISCOVERY.md`. | **NO** |
| **Pass 2** | **Architecture Design** | Authored initial 18 architecture documents covering product definition, domain model, 5-tier RBAC, four-tier cash model, and 20 ADRs. Produced `B0_PASS2_ARCHITECTURE.md`. | **NO** |
| **Pass 3** | **Consistency Review** | Cross-examined documents; resolved 5 major semantic contradictions (Operational ledger vs ERP, audit cascade deletion, 5-tier MVP roles, cash semantics, honest red-team evidence). Produced `B0_PASS3_CONSISTENCY_REVIEW.md`. | **NO** |
| **Pass 3.1** | **Contract Reconciliation** | Reconciled 6 residual contract-level items (Transaction fact immutability vs lifecycle status, `discount_amount` column, $\text{ADBR}_{30}$ runway math, failover evidence, CI gate, RTM language). Produced `B0_PASS3_1_FINAL_RECONCILIATION.md`. | **NO** |
| **Pass 3.2** | **Freeze Integrity Gate** | Formally validated 5-tier Runway Precedence order, multi-layer invoice total enforcement, and verified zero open blockers. Produced `B0_PASS3_2_FREEZE_INTEGRITY.md` declaring **READY FOR FREEZE**. | **NO** |

---

## SECTION D — COMPLETE AUTHORITATIVE B0 ARTIFACT REGISTER

| Doc ID | Artifact Filename | Relative Brain/Docs Path | Classification Category | Pass / Evolution | Normative? | Frozen? |
|---|---|---|---|---|:---:|:---:|
| `B0-DOC-001` | `BUSINESS_OS_PRODUCT_DEFINITION.md` | `BUSINESS_OS_PRODUCT_DEFINITION.md` | Product / UX / Journey | Pass 2 / Updated Pass 3 | **YES** | **FROZEN** |
| `B0-DOC-002` | `BUSINESS_OS_DOMAIN_ARCHITECTURE.md` | `BUSINESS_OS_DOMAIN_ARCHITECTURE.md` | Normative Architecture Contract | Pass 2 / Updated Pass 3.1 | **YES** | **FROZEN** |
| `B0-DOC-003` | `BUSINESS_OS_MULTI_TENANCY_RBAC.md` | `BUSINESS_OS_MULTI_TENANCY_RBAC.md` | Normative Architecture Contract | Pass 2 / Updated Pass 3 | **YES** | **FROZEN** |
| `B0-DOC-004` | `BUSINESS_OS_FINANCIAL_ARCHITECTURE.md` | `BUSINESS_OS_FINANCIAL_ARCHITECTURE.md` | Financial / Math Contract | Pass 2 / Updated Pass 3.2 | **YES** | **FROZEN** |
| `B0-DOC-005` | `BUSINESS_OS_AI_ARCHITECTURE.md` | `BUSINESS_OS_AI_ARCHITECTURE.md` | Normative Architecture Contract | Pass 2 | **YES** | **FROZEN** |
| `B0-DOC-006` | `BUSINESS_OS_EVENT_ARCHITECTURE.md` | `BUSINESS_OS_EVENT_ARCHITECTURE.md` | Normative Architecture Contract | Pass 2 | **YES** | **FROZEN** |
| `B0-DOC-007` | `BUSINESS_OS_SECURITY_ARCHITECTURE.md` | `BUSINESS_OS_SECURITY_ARCHITECTURE.md` | Security / Red-Team | Pass 2 / Updated Pass 3 | **YES** | **FROZEN** |
| `B0-DOC-008` | `BUSINESS_OS_DATA_ARCHITECTURE.md` | `BUSINESS_OS_DATA_ARCHITECTURE.md` | Normative Architecture Contract | Pass 2 / Updated Pass 3.1 | **YES** | **FROZEN** |
| `B0-DOC-009` | `BUSINESS_OS_API_ARCHITECTURE.md` | `BUSINESS_OS_API_ARCHITECTURE.md` | Normative Architecture Contract | Pass 2 | **YES** | **FROZEN** |
| `B0-DOC-010` | `BUSINESS_OS_INTEGRATION_ARCHITECTURE.md`| `BUSINESS_OS_INTEGRATION_ARCHITECTURE.md`| Deployment / Integration | Pass 2 | **YES** | **FROZEN** |
| `B0-DOC-011` | `BUSINESS_OS_STORAGE_DEPLOYMENT_ARCHITECTURE.md`| `BUSINESS_OS_STORAGE_DEPLOYMENT_ARCHITECTURE.md`| Deployment / Storage | Pass 2 | **YES** | **FROZEN** |
| `B0-DOC-012` | `BUSINESS_OS_UX_ARCHITECTURE.md` | `BUSINESS_OS_UX_ARCHITECTURE.md` | Product / UX / Journey | Pass 2 | Supporting | **FROZEN** |
| `B0-DOC-013` | `BUSINESS_OS_USER_JOURNEYS.md` | `BUSINESS_OS_USER_JOURNEYS.md` | Product / UX / Journey | Pass 2 | Supporting | **FROZEN** |
| `B0-DOC-014` | `BUSINESS_OS_REQUIREMENTS.md` | `BUSINESS_OS_REQUIREMENTS.md` | Requirements / Traceability | Pass 2 / Updated Pass 3.1 | **YES** | **FROZEN** |
| `B0-DOC-015` | `BUSINESS_OS_RISK_REGISTER.md` | `BUSINESS_OS_RISK_REGISTER.md` | Security / Red-Team | Pass 2 / Updated Pass 3 | **YES** | **FROZEN** |
| `B0-DOC-016` | `BUSINESS_OS_OPEN_QUESTIONS.md` | `BUSINESS_OS_OPEN_QUESTIONS.md` | Governance / Decision Record | Pass 2 / Updated Pass 3 | Supporting | **FROZEN** |
| `B0-DOC-017` | `BUSINESS_OS_ADR_INDEX.md` | `BUSINESS_OS_ADR_INDEX.md` | Architectural Decision Record | Pass 2 / Updated Pass 3.1 | **YES** | **FROZEN** |
| `B0-DOC-018` | `BUSINESS_OS_B0_PASS2_ARCHITECTURE.md` | `BUSINESS_OS_B0_PASS2_ARCHITECTURE.md` | Master Review / Blueprint | Pass 2 | Supporting | **FROZEN** |
| `B0-DOC-019` | `DEADLINEOS_BUSINESS_OS_B0_PASS2_ARCHITECTURE_REVIEW.md`| `DEADLINEOS_BUSINESS_OS_B0_PASS2_ARCHITECTURE_REVIEW.md`| Pass Review / Governance | Pass 2 | Supporting | **FROZEN** |
| `B0-DOC-020` | `BUSINESS_OS_FINANCIAL_TRUTH_CONTRACT.md`| `BUSINESS_OS_FINANCIAL_TRUTH_CONTRACT.md`| Financial / Math Contract | Pass 3 / Updated Pass 3.2 | **YES** | **FROZEN** |
| `B0-DOC-021` | `BUSINESS_OS_B0_REQUIREMENTS_TRACEABILITY.md`| `BUSINESS_OS_B0_REQUIREMENTS_TRACEABILITY.md`| Requirements / Traceability | Pass 3 / Updated Pass 3.1 | **YES** | **FROZEN** |
| `B0-DOC-022` | `BUSINESS_OS_B0_PASS3_RED_TEAM.md` | `BUSINESS_OS_B0_PASS3_RED_TEAM.md` | Security / Red-Team | Pass 3 / Updated Pass 3.1 | **YES** | **FROZEN** |
| `B0-DOC-023` | `BUSINESS_OS_B0_PASS3_CONSISTENCY_REVIEW.md`| `BUSINESS_OS_B0_PASS3_CONSISTENCY_REVIEW.md`| Pass Review / Governance | Pass 3 | Supporting | **FROZEN** |
| `B0-DOC-024` | `DEADLINEOS_BUSINESS_OS_B0_PASS3_1_FINAL_RECONCILIATION.md`| `DEADLINEOS_BUSINESS_OS_B0_PASS3_1_FINAL_RECONCILIATION.md`| Pass Review / Governance | Pass 3.1 | Supporting | **FROZEN** |
| `B0-DOC-025` | `DEADLINEOS_BUSINESS_OS_B0_PASS3_2_FREEZE_INTEGRITY.md`| `DEADLINEOS_BUSINESS_OS_B0_PASS3_2_FREEZE_INTEGRITY.md`| Freeze Gate Certification | Pass 3.2 | **YES** | **FROZEN** |
| `B0-DOC-026` | `BUSINESS_OS_B0_MASTER_TRACKER.md` | `BUSINESS_OS_B0_MASTER_TRACKER.md` | Master Program Tracker | Pass 3.2 Final | **YES** | **FROZEN** |
| `B0-DOC-027` | `DEADLINEOS_BUSINESS_OS_B0_FREEZE_CERTIFICATE.md`| `DEADLINEOS_BUSINESS_OS_B0_FREEZE_CERTIFICATE.md`| Master Freeze Certificate | Pass 3.2 Final | **YES** | **FROZEN** |
| `B0-DOC-028` | `DEADLINEOS_BUSINESS_OS_B0_TO_B1_HANDOFF.md`| `DEADLINEOS_BUSINESS_OS_B0_TO_B1_HANDOFF.md`| Handoff Specification | Pass 3.2 Final | **YES** | **FROZEN** |

---

## SECTION E — NORMATIVE B0 CONTRACTS

| Contract Area | Source Document | Core Invariant Rule | B1 Verification Gate |
|---|---|---|---|
| **Product Scope** | `B0-DOC-001` | Operational clarity engine for MSMEs; explicit non-goals (Not ERP, not GST filer, not payroll). | Product boundary review |
| **Tenancy Isolation** | `B0-DOC-003` | All queries enforce `WHERE workspace_id = :ws_id`; composite primary keys. | `test_multi_tenant_leakage.py` |
| **5-Tier RBAC** | `B0-DOC-003` | Two-stage middleware (`@require_auth` + `@require_workspace(perm)`); roles: `OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`. | `test_rbac_permissions.py` |
| **Exact Decimal Math** | `B0-DOC-004` | All monetary values use `NUMERIC(15, 2)` and Python `Decimal`. Floating-point arithmetic is strictly banned. | `test_decimal_precision.py` |
| **Invoice Total Math** | `B0-DOC-004` | $\text{total\_amount} = \text{subtotal} + \text{tax\_amount} - \text{discount\_amount}$, enforced via schema check constraint and frozen upon `ISSUED`. | `test_invoice_math_invariants.py` |
| **Transaction Immutability**| `B0-DOC-020` | Facts (`amount`, `currency`, `date`, `partner_id`) are immutable. Reversals create counter-adjustments; original row status becomes `REVERSED`. | `test_transaction_immutability.py` |
| **Runway Math & Precedence**| `B0-DOC-004` | $\text{Runway} = \lfloor\text{Confirmed Cash} / \text{ADBR}_{30}\rfloor$. Strict precedence: `NEGATIVE` $\rightarrow$ `STALE` $\rightarrow$ `INSUFFICIENT_HISTORY` $\rightarrow$ `ZERO_BURN` $\rightarrow$ `CALCULATED`. | `test_cash_runway_math.py` |
| **AI Authority Boundary** | `B0-DOC-005` | AI is strictly advisory/interpretive; zero direct writes; mandatory human confirmation barrier (`StagedExtraction`). | `test_ai_mutation_barrier.py` |
| **Copilot Security** | `B0-DOC-005` | Zero prompt escalation; prompt context is built strictly from role-filtered database query results bound to `g.workspace_id`. | `test_copilot_rbac_isolation.py` |
| **Permanent Audit Trail** | `B0-DOC-008` | Append-only `business_audit_events`; non-cascading foreign key; soft-deletion for workspaces. | `test_audit_immutability.py` |
| **Idempotency** | `B0-DOC-009` | Mandatory `Idempotency-Key` header on all mutation endpoints with 24-hour cache. | `test_idempotency_keys.py` |
| **Cloud Object Storage** | `B0-DOC-011` | Supabase Storage with 15-minute presigned access URLs; zero persistent storage on ephemeral Render disk. | `test_storage_signed_urls.py` |
| **Personal OS Isolation** | `B0-DOC-010` | 0 personal models modified; polymorphic read-only adapter; 162 Personal OS tests run in CI gate. | Continuous Personal OS CI Gate |

---

## SECTION F — KEY BUSINESS OS ARCHITECTURAL DECISIONS

1. **`ADR-001` (Product Scope):** Operational Co-Pilot and Financial Clarity Engine for MSMEs (Not an ERP).
2. **`ADR-002` (Target ICP):** Owner-operated service & trade micro-enterprises (5–15 employees).
3. **`ADR-003` (Multi-Tenancy):** Row-Level Tenancy with explicit `workspace_id` foreign keys and composite indexes.
4. **`ADR-004` (5-Tier RBAC):** `OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER` enforced at API middleware.
5. **`ADR-005` (Domain Boundary):** All Business OS entities live in isolated `business_*` tables.
6. **`ADR-006` (Cash Reality):** Four-tier cash model (Confirmed Cash + Committed Inflows - Committed Outflows = Projected Position).
7. **`ADR-007` (Monetary Data Types):** `NUMERIC(15, 2)` in PostgreSQL, Python `Decimal`, string JSON serialization.
8. **`ADR-008` (Append-Only Ledger):** Reversible adjustments; original transaction rows are preserved as `REVERSED`.
9. **`ADR-009` (Human-in-the-Loop Barrier):** AI extractions stage in `StagedExtraction` requiring human review before commit.
10. **`ADR-010` (Entity Disambiguation):** Deterministic prompting when partner names match $\ge 2$ entities (No guessing).
11. **`ADR-011` (Strict AI Boundary):** Arithmetic and permissions are 100% deterministic code; AI is restricted to advisory NLU/OCR.
12. **`ADR-012` (Zero-Bypass Copilot):** Prompts receive only pre-filtered database records permitted by caller's RBAC role.
13. **`ADR-013` (Transactional Outbox):** Outbox events committed in same DB transaction; dispatched safely via Blinker.
14. **`ADR-014` (Polymorphic Bridge):** Business deadlines project into personal Today/Calendar views without schema mutations.
15. **`ADR-015` (Cloud Object Storage):** Documents stored in Supabase Storage with 15-minute presigned URLs.
16. **`ADR-016` (Cloud-First Sync):** Cloud-first responsive web architecture in MVP; local offline syncing deferred.
17. **`ADR-017` (Render Deployment):** Business OS mounted under `/api/business` blueprint within existing Render web service.
18. **`ADR-018` (Async I/O Evolution):** Eventlet retained for B1 MVP; ASGI (Uvicorn) migration scheduled for Phase B8.
19. **`ADR-019` (Immutable Audit Trail):** Every mutation records actor ID, IP, diffs, reason, and timestamp.
20. **`ADR-020` (Accountant Export):** One-click CSV ledger, receivable aging sheet, and ZIP package of original invoice PDFs.

---

## SECTION G — FINANCIAL TRUTH CONTRACT INDEX

- **Authoritative Facts:** `business_transactions` (inbound/outbound money movements), `business_payment_allocations` (transaction-to-invoice settlement links), and `business_audit_events`.
- **Derived Settlement State:** `invoice.paid_amount` ($\sum \text{Allocations}$), `invoice.balance_due` ($\text{total\_amount} - \text{paid\_amount}$), `invoice.status`.
- **Invoice Math Formula:** $\text{total\_amount} = \text{subtotal} + \text{tax\_amount} - \text{discount\_amount}$.
- **Settlement Invariant:** $i.\text{paid\_amount} + i.\text{balance\_due} \equiv i.\text{total\_amount}$ at all times.
- **Runway Days Formula:** $\lfloor\text{Confirmed Cash} / \text{ADBR}_{30}\rfloor$, where $\text{ADBR}_{30} = \frac{\sum \text{Expenses}_{[-30,0]} + \sum \text{Payables}_{[0,+30]}}{60}$.
- **Precedence Order:** `RUNWAY_NEGATIVE` (P1) $\rightarrow$ `RUNWAY_STALE` (P2) $\rightarrow$ `RUNWAY_INSUFFICIENT_HISTORY` (P3) $\rightarrow$ `RUNWAY_ZERO_BURN` (P4) $\rightarrow$ `CALCULATED` (P5).

---

## SECTION H — SECURITY & RED TEAM REGISTER

- **Attack Scenarios Evaluated:** 20 comprehensive threat vectors (Cross-tenant access, manipulated workspace IDs, Copilot RBAC bypass, prompt injection, duplicate payment retries, unauthorized reversals, audit destruction, ephemeral disk loss, AI outages).
- **Classification Status:**
  - 16 Scenarios: `ARCHITECTURALLY MITIGATED — IMPLEMENTATION UNVERIFIED (B1–B5 Gated)`.
  - 3 Scenarios: `VERIFIED AGAINST EXISTING PERSONAL OS INFRASTRUCTURE` (AI provider failover, Blinker event bus, outbox crash resilience).
  - 1 Scenario: `ARCHITECTURALLY REQUIRED — IMPLEMENTATION UNVERIFIED (B1 GATED)` (Continuous 162-test Personal OS regression gate).
- **Open Security Vulnerabilities:** **0**

---

## SECTION I — REQUIREMENTS TRACEABILITY

- **Total Requirements:** 25 (10 Functional, 4 Non-Functional, 4 Security, 4 Data Integrity, 3 AI Safety).
- **Architectural Traceability:** **100% (25/25 mapped in `B0-DOC-021`)**.
- **Orphan Requirements / Entities / ADRs:** **0**
- **Evidence Disclaimer:** "Architectural Traceability $\ne$ Implementation Verification." (All 25 requirements are mapped to planned B1–B5 verification tests).

---

## SECTION J — B1 IMPLEMENTATION GATE

To begin Phase B1 implementation, all 13 prerequisites must be satisfied:
1. B0 architecture formally certified and frozen. (**SATISFIED**)
2. Master tracker created and committed. (**SATISFIED**)
3. Personal OS tag `personal-os-v1.0-certified` verified at `32e1770`. (**SATISFIED**)
4. Working tree completely clean. (**SATISFIED**)
5. HEAD verified against certified baseline. (**SATISFIED**)
6. Complete B0 artifact inventory verified (28 documents). (**SATISFIED**)
7. Zero unresolved B0 blockers. (**SATISFIED**)
8. B1 scope explicitly defined (`workspaces`, `members`, RBAC, `partners`). (**SATISFIED**)
9. B1 branch boundary defined (`feature/b1-foundation`). (**SATISFIED**)
10. Personal OS regression gate defined (162 tests). (**SATISFIED**)
11. Forward-only migration strategy defined (`business_*` tables). (**SATISFIED**)
12. B1 unit/integration test plan defined. (**SATISFIED**)
13. **User explicitly authorizes B1 implementation.** (**PENDING USER DIRECTIVE**)

---

## SECTION K — B1 VERIFICATION REQUIREMENTS (PLANNED TEST SUITES)

1. `test_workspace_scoping.py` — Tenant creation, listing, switching, and status validation. (PLANNED)
2. `test_multi_tenant_leakage.py` — Verifies cross-tenant data access rejection. (PLANNED)
3. `test_rbac_permissions.py` — 5-tier role enforcement across all endpoints. (PLANNED)
4. `test_partner_registry.py` — Customer/Supplier CRUD, tax ID validation, and credit periods. (PLANNED)
5. `test_decimal_precision.py` — Precision assertions on `NUMERIC(15, 2)` monetary columns. (PLANNED)
6. `test_idempotency_keys.py` — Deduplication on mutation endpoints. (PLANNED)
7. `test_audit_immutability.py` — Permanent non-cascading audit logging. (PLANNED)
8. `test_personal_os_regression.py` — Full execution of the 162 Personal OS tests. (PLANNED)

---

## SECTION L — DEFERRED ROADMAP DECISIONS

1. **High-Throughput ASGI / Uvicorn Migration:** Explicitly deferred to Phase B8 (Production Excellence).
2. **Multi-Currency Cross-Border FX Hedging:** Explicitly deferred to Phase B2+.

---

## SECTION M — PERMANENT GOVERNANCE RULES

1. **Personal OS is frozen.** (No personal schema or code modifications).
2. **Business OS is a separate program.** (Isolated `business_*` tables and `/api/business/*` routes).
3. **B0 architecture is frozen.** (No silent contract modifications in B1+).
4. **AI is advisory; deterministic code is authoritative.** (Zero unsupervised ledger writes).
5. **Historical financial facts are strictly immutable.** (Reversals create counter-adjustments).
6. **Tenancy is enforced server-side.** (All queries filter by `workspace_id`).
7. **Copilot cannot bypass RBAC.** (Prompts receive role-scoped data only).
8. **Consequential mutations require human confirmation.** (`StagedExtraction` barrier).
9. **Every Business OS phase requires its own release gate.**
