# DEADLINEOS BUSINESS OS — B7 MASTER IMPLEMENTATION PLAN
**Document ID:** `B7-DOC-002`
**Status:** `MASTER PLAN DRAFTED / NO IMPLEMENTATION`
**Classification:** Master Implementation Specification
**Author:** DeadlineOS Principal Architect & Multi-Entity Systems Lead
**Planning Date:** 2026-08-29T17:20:00+05:30

---

## 1. Overview & Scope

Phase B7 implements **Commercial Multi-Entity & Cross-Workspace Consolidation** for DeadlineOS Business OS:
1. **Business Entity Registry:** Allows businesses to register multiple legal entities, subsidiaries, or operating branches (`business_entities`) within a workspace.
2. **Entity-Scoped Financials:** Enables tagging invoices, transactions, and recurring obligations with specific legal entities.
3. **Cross-Workspace Consolidation Engine:** Deterministically aggregates financial metrics, cash reality, receivables, and payables across multiple workspaces/entities belonging to an authorized user.
4. **Inter-Entity Transfer Tracking:** Records cross-entity transfers with automated elimination of internal transactions from group financial summaries.

---

## 2. Milestone Execution Sequence (`B7.0` -> `B7.8`)

### Milestone B7.0: Readiness & Branch Setup
- Create and checkout working branch `feature/b7-multi-entity-consolidation`.
- Verify live baseline (210 backend tests green, clean Vite build).

### Milestone B7.1: Database Models & Forward Migration
- Implement `backend/models/business/entity.py` (`BusinessEntity` and `InterEntityTransfer` models).
- Add `entity_id` foreign key columns to `business_invoices`, `business_transactions`, and `business_recurring_obligations`.
- Export in `backend/models/business/__init__.py` and `backend/models/__init__.py`.
- Create forward migration `backend/migrations/versions/i6f7a8b9c0d1_business_os_multi_entity.py` (revising `h5e6f7a8b9c0`).

### Milestone B7.2: Entity Management Service
- Implement `backend/services/business/entity_service.py`.
- Features: Entity CRUD, default entity provisioning, tax identifier validation (GSTIN/PAN/EIN), active/inactive lifecycle.

### Milestone B7.3: Financial Consolidation Service
- Implement `backend/services/business/consolidation_service.py`.
- Features: Multi-workspace aggregation, currency normalization, inter-entity transfer elimination, consolidated cash reality and runway calculation.

### Milestone B7.4: API Routes & Blueprint Registration
- Implement:
  - `backend/api/business/entities.py`: CRUD for entities within a workspace.
  - `backend/api/business/consolidation.py`: Multi-workspace consolidated financial overview and group reports.
- Register blueprints in `backend/api/business/__init__.py`.

### Milestone B7.5: Frontend Client & Consolidation UI
- Update `frontend/src/api.ts` with B7 methods.
- Implement `frontend/src/components/Business/EntitySelector.tsx`.
- Implement `frontend/src/components/Business/ConsolidatedOverview.tsx`.
- Implement `frontend/src/components/Business/EntityManagementModal.tsx`.

### Milestone B7.6: Security, Multi-Entity & Isolation Test Suites
- Implement:
  - `backend/tests/test_entity_management.py`: Tests entity CRUD, validation, and defaults.
  - `backend/tests/test_consolidation_engine.py`: Tests mathematical multi-workspace aggregation and inter-entity elimination.
  - `backend/tests/test_inter_entity_transfers.py`: Tests transfer recording and lifecycle.
  - `backend/tests/test_multi_entity_tenant_isolation.py`: Tests cross-tenant security and RBAC.

### Milestone B7.7: Full Regression Gate & Production Build
- Run full backend regression suite (assert >= 216 tests passing, 0 regressions).
- Run frontend production build `tsc -b && vite build`.

### Milestone B7.8: Release Certification & Tagging
- Merge into `main`, tag `business-os-b7-certified`, and push.

---

## 3. Implementation Files Overview

| Component | Target File | Purpose |
|---|---|---|
| **Entity Models** | `backend/models/business/entity.py` | `BusinessEntity` & `InterEntityTransfer` |
| **Migration** | `backend/migrations/versions/i6f7a8b9c0d1_business_os_multi_entity.py` | Forward migration for B7 tables & entity_id FKs |
| **Entity Service** | `backend/services/business/entity_service.py` | Entity CRUD & tax ID validation |
| **Consolidation Service** | `backend/services/business/consolidation_service.py` | Cross-workspace aggregation & eliminations |
| **Entity API** | `backend/api/business/entities.py` | REST endpoints for entity management |
| **Consolidation API** | `backend/api/business/consolidation.py` | REST endpoints for consolidated reporting |
| **Frontend Client** | `frontend/src/api.ts` | B7 API client methods |
| **Frontend UI** | `frontend/src/components/Business/*.tsx` | Entity selector, consolidated dashboard, modals |
| **Test Suites** | `backend/tests/test_*.py` (4 suites) | Automated verification of B7 features |
