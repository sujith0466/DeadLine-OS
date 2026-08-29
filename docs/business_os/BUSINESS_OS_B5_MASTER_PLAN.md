# DEADLINEOS BUSINESS OS — B5 MASTER IMPLEMENTATION PLAN
**Document ID:** `B5-DOC-002`
**Status:** `MASTER PLAN DRAFTED / NO IMPLEMENTATION`
**Classification:** Master Implementation Specification
**Author:** DeadlineOS Principal Architect & Financial Recovery Lead
**Planning Date:** 2026-08-29T16:30:00+05:30

---

## 1. Overview & Scope

Phase B5 implements **Rescue, Collection Reminders & Accountant Export** for DeadlineOS Business OS:
1. **Rescue Aging Engine:** Categorizes overdue receivables into aging buckets ($0-30$, $31-60$, $61-90$, $90+$ days) and ranks recovery priority by balance due and days past due.
2. **Collection Reminders:** Generates tone-aware payment reminders (`GENTLE`, `POLITE`, `URGENT`, `LEGAL`) grounded in verified invoice data, requiring human confirmation before dispatch.
3. **Accountant Export Package:** Generates deterministic CSV ledger exports and bundled ZIP archives containing invoices, transactions, payment allocations, and summary manifests with SHA-256 provenance.

---

## 2. Milestone Execution Sequence (`B5.0` $
ightarrow$ `B5.8`)

### Milestone B5.0: Readiness & Branch Setup
- Create and checkout working branch `feature/b5-rescue-export`.
- Verify live baseline (198 backend tests green, clean Vite build).

### Milestone B5.1: Database Models & Forward Migration
- Implement `backend/models/business/reminder.py` (`CollectionReminder` model).
- Export in `backend/models/business/__init__.py` and `backend/models/__init__.py`.
- Create forward migration `backend/migrations/versions/g4d5e6f7a8b9_business_os_rescue_export.py` (revising `f3c4d5e6f7a8`).

### Milestone B5.2: Rescue & Overdue Aging Engine
- Implement `backend/services/business/rescue_service.py`.
- Calculates overdue aging buckets, recovery priority score ($P = 	ext{balance\_due} 	imes (1 + rac{	ext{days\_overdue}}{30})$), and recovery action status.

### Milestone B5.3: Collection Reminder Service
- Implement `backend/services/business/reminder_service.py`.
- Supports tones (`GENTLE`, `POLITE`, `URGENT`, `LEGAL`), AI message synthesis, draft creation, dispatch recording, and state transitions.

### Milestone B5.4: Deterministic Accountant Export Engine
- Implement `backend/services/business/export_service.py`.
- Generates `invoices.csv`, `transactions.csv`, `allocations.csv`, `trial_balance.json`, and packages them into a cryptographically hashed ZIP archive.

### Milestone B5.5: API Routes & Blueprint Registration
- Implement:
  - `backend/api/business/rescue.py`: `GET /api/business/rescue/aging`, `GET /api/business/rescue/priorities`.
  - `backend/api/business/reminders.py`: `POST /api/business/reminders/draft`, `POST /api/business/reminders/:id/send`, `GET /api/business/reminders`.
  - `backend/api/business/exports.py`: `GET /api/business/exports/accountant-package`, `GET /api/business/exports/invoices.csv`, `GET /api/business/exports/transactions.csv`.
- Register blueprints in `backend/api/business/__init__.py`.

### Milestone B5.6: Frontend Client & Rescue UI Components
- Update `frontend/src/api.ts` with B5 methods.
- Implement `frontend/src/components/Business/RescueQueue.tsx`.
- Implement `frontend/src/components/Business/ReminderModal.tsx`.
- Implement `frontend/src/components/Business/AccountantExportModal.tsx`.

### Milestone B5.7: Security, Recovery & Export Test Suites
- Implement:
  - `backend/tests/test_rescue_workflows.py`: Tests aging bucket computation and recovery ranking.
  - `backend/tests/test_collection_reminders.py`: Tests tone-aware reminder synthesis, human confirmation barrier, and state transitions.
  - `backend/tests/test_accountant_export.py`: Tests deterministic CSV output, ZIP archive packaging, and SHA-256 provenance.
  - `backend/tests/test_rescue_tenant_isolation.py`: Tests cross-tenant isolation and 5-tier RBAC on exports and reminders.

### Milestone B5.8: Full Regression Gate & Release Certification
- Run full backend regression suite (assert $\ge 205$ tests passing, 0 regressions).
- Run frontend production build `tsc -b && vite build`.
- Merge into `main`, tag `business-os-b5-certified`, and push.

---

## 3. Implementation Files Overview

| Component | Target File | Purpose |
|---|---|---|
| **Reminder Model** | `backend/models/business/reminder.py` | Model for collection reminders |
| **Migration** | `backend/migrations/versions/g4d5e6f7a8b9_business_os_rescue_export.py` | Forward migration for reminders |
| **Rescue Service** | `backend/services/business/rescue_service.py` | Aging buckets & priority calculation |
| **Reminder Service** | `backend/services/business/reminder_service.py` | Tone-aware reminder synthesis & dispatch |
| **Export Service** | `backend/services/business/export_service.py` | Deterministic CSV & ZIP export engine |
| **Rescue API** | `backend/api/business/rescue.py` | Aging & recovery endpoints |
| **Reminders API** | `backend/api/business/reminders.py` | Reminder drafting & dispatch endpoints |
| **Exports API** | `backend/api/business/exports.py` | CSV & ZIP package download endpoints |
| **Frontend Client** | `frontend/src/api.ts` | B5 API client methods |
| **Frontend UI** | `frontend/src/components/Business/*.tsx` | RescueQueue, ReminderModal, AccountantExportModal |
| **Test Suites** | `backend/tests/test_*.py` (4 suites) | Automated verification of B5 features |
