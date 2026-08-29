# DEADLINEOS BUSINESS OS — B6 MASTER IMPLEMENTATION PLAN
**Document ID:** `B6-DOC-002`
**Status:** `MASTER PLAN DRAFTED / NO IMPLEMENTATION`
**Classification:** Master Implementation Specification
**Author:** DeadlineOS Principal Architect & Automation Systems Lead
**Planning Date:** 2026-08-29T16:50:00+05:30

---

## 1. Overview & Scope

Phase B6 implements **Advanced Automation & Recurring Obligations** for DeadlineOS Business OS:
1. **Recurring Obligations Engine:** Allows business owners to schedule recurring customer retainers, supplier payables, rent, payroll, and tax deadlines (`WEEKLY`, `BIWEEKLY`, `MONTHLY`, `QUARTERLY`, `ANNUALLY`).
2. **Idempotent Automation Runner:** Deterministically executes scheduled obligations, generates draft/issued invoices via B3 services, and tracks execution history in `business_automation_execution_logs`.
3. **Tax & Compliance Schedule Templates:** Pre-configured recurring schedules for Indian GST filing, TDS remittance, and advance tax payments.

---

## 2. Milestone Execution Sequence (`B6.0` -> `B6.8`)

### Milestone B6.0: Readiness & Branch Setup
- Create and checkout working branch `feature/b6-automation-recurring`.
- Verify live baseline (204 backend tests green, clean Vite build).

### Milestone B6.1: Database Models & Forward Migration
- Implement `backend/models/business/recurring.py` (`RecurringObligation` and `AutomationExecutionLog` models).
- Export in `backend/models/business/__init__.py` and `backend/models/__init__.py`.
- Create forward migration `backend/migrations/versions/h5e6f7a8b9c0_business_os_recurring_automation.py` (revising `g4d5e6f7a8b9`).

### Milestone B6.2: Recurrence Calculation Engine
- Implement `backend/services/business/recurring_obligation_service.py`.
- Features: Recurrence stepping, month-end clamping (28/29/30/31 days), pause/resume state machine, next due date calculation.

### Milestone B6.3: Automation Runner Service
- Implement `backend/services/business/automation_runner_service.py`.
- Features: Batch runner, cycle idempotency checking, draft/issued invoice creation via B3 `InvoiceService`, execution logging, error isolation.

### Milestone B6.4: API Routes & Blueprint Registration
- Implement:
  - `backend/api/business/recurring.py`: CRUD for recurring obligations, pause/resume/trigger endpoints.
  - `backend/api/business/automation.py`: Manual batch run trigger and execution log queries.
- Register blueprints in `backend/api/business/__init__.py`.

### Milestone B6.5: Frontend Client & Automation UI
- Update `frontend/src/api.ts` with B6 methods.
- Implement `frontend/src/components/Business/RecurringObligationsList.tsx`.
- Implement `frontend/src/components/Business/RecurringObligationModal.tsx`.
- Implement `frontend/src/components/Business/AutomationLogsDrawer.tsx`.

### Milestone B6.6: Security, Recurrence & Isolation Test Suites
- Implement:
  - `backend/tests/test_recurring_obligations.py`: Tests CRUD, recurrence math, pause/resume lifecycle.
  - `backend/tests/test_automation_runner.py`: Tests idempotent batch execution and invoice generation.
  - `backend/tests/test_tax_compliance_schedules.py`: Tests tax schedule recurrence and due dates.
  - `backend/tests/test_automation_tenant_isolation.py`: Tests multi-tenant isolation and 5-tier RBAC.

### Milestone B6.7: Full Regression Gate & Production Build
- Run full backend regression suite (assert >= 210 tests passing, 0 regressions).
- Run frontend production build `tsc -b && vite build`.

### Milestone B6.8: Release Certification & Tagging
- Merge into `main`, tag `business-os-b6-certified`, and push.

---

## 3. Implementation Files Overview

| Component | Target File | Purpose |
|---|---|---|
| **Recurring Models** | `backend/models/business/recurring.py` | `RecurringObligation` & `AutomationExecutionLog` |
| **Migration** | `backend/migrations/versions/h5e6f7a8b9c0_business_os_recurring_automation.py` | Forward migration for B6 tables |
| **Recurrence Service** | `backend/services/business/recurring_obligation_service.py` | Recurrence calculation & lifecycle |
| **Runner Service** | `backend/services/business/automation_runner_service.py` | Batch execution & idempotency |
| **Recurring API** | `backend/api/business/recurring.py` | REST endpoints for recurring obligations |
| **Automation API** | `backend/api/business/automation.py` | REST endpoints for runner & audit logs |
| **Frontend Client** | `frontend/src/api.ts` | B6 API client methods |
| **Frontend UI** | `frontend/src/components/Business/*.tsx` | Recurring list, modal, and logs drawer |
| **Test Suites** | `backend/tests/test_*.py` (4 suites) | Automated verification of B6 features |
