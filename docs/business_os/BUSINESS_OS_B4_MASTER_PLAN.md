# DEADLINEOS BUSINESS OS — B4 MASTER IMPLEMENTATION PLAN
**Document ID:** `B4-DOC-002`
**Status:** `MASTER PLAN DRAFTED / NO IMPLEMENTATION`
**Classification:** Master Implementation Specification
**Author:** DeadlineOS Principal Architect & AI Systems Lead
**Planning Date:** 2026-08-29T16:20:00+05:30

---

## 1. Overview & Objective

Phase B4 builds the **Intelligence, Zero-Bypass Copilot & Polymorphic Bridge** layer for DeadlineOS Business OS. It enables founders to interrogate their operational finances using natural language, receive deterministic cash risk alerts, and view business deadlines within their personal calendar, without compromising financial truth or Personal OS isolation.

---

## 2. Milestone Execution Sequence (`B4.0` $
ightarrow$ `B4.8`)

### Milestone B4.0: Readiness & Branch Setup
- Create and checkout working branch `feature/b4-intelligence-copilot`.
- Verify live baseline (192 backend tests green, clean Vite build).

### Milestone B4.1: Business Copilot Service & Context Assembler
- Implement `backend/services/business/copilot_service.py`.
- Features:
  - Context Assembler: Gathers verified cash position, runway days, top receivables, overdue aging, and upcoming payables.
  - Prompt Sanitization & Injection Defense: Strips systemic prompts, validates schema.
  - Advisory Inference: Queries hybrid AI provider with grounded financial context.
  - Action Proposal Generator: Emits structured action proposals (e.g. draft payment reminders, capture staging candidates).

### Milestone B4.2: Cash Risk & Financial Intelligence Engine
- Implement `backend/services/business/cash_risk_service.py`.
- Deterministic Risk Indicators:
  - `DEFICIT_WARNING`: Projected Position $< 0$ within 30 days.
  - `BURN_ACCELERATION`: Current 14-day burn rate $> 1.5 	imes$ 30-day average.
  - `RECEIVABLE_CONCENTRATION`: Single customer represents $> 40\%$ of total outstanding receivables.
  - `CRITICAL_RUNWAY`: Runway Days $< 30$ days.

### Milestone B4.3: Polymorphic Personal OS Bridge Adapter
- Implement `backend/services/business/bridge_service.py`.
- Features:
  - Cross-Domain Virtual Projection: Maps active receivables, payables, and critical cash milestones into virtual calendar/schedule feed items.
  - Read-Only Guarantee: Zero modification to Personal OS tables (`tasks`, `goals`, `schedule_slots`).
  - Unified User Feed: Combines personal schedule and business obligations for user workspaces.

### Milestone B4.4: Business Intelligence API Routes
- Implement:
  - `backend/api/business/copilot.py`: `POST /api/business/copilot/query`, `GET /api/business/copilot/suggestions`.
  - `backend/api/business/risk.py`: `GET /api/business/financial/risks`.
  - `backend/api/business/bridge.py`: `GET /api/business/bridge/feed`.
- Mount on `business_bp` in `backend/api/business/__init__.py`.

### Milestone B4.5: Frontend Copilot & Unified View Components
- Update `frontend/src/api.ts` with B4 methods (`askBusinessCopilot`, `getBusinessRisks`, `getBusinessBridgeFeed`).
- Create `frontend/src/components/Business/BusinessCopilotModal.tsx`.
- Create `frontend/src/components/Business/CashRiskBanner.tsx`.

### Milestone B4.6: Security & AI Boundary Automated Test Suites
- Create:
  - `backend/tests/test_business_copilot.py`: Tests zero-bypass context assembly, natural language advisory, and action generation.
  - `backend/tests/test_cash_risk_engine.py`: Tests deterministic risk triggers and threshold alerts.
  - `backend/tests/test_polymorphic_bridge.py`: Tests read-only virtual schedule projection and tenant isolation.
  - `backend/tests/test_copilot_tenant_isolation.py`: Tests cross-tenant prompt/data isolation and RBAC.

### Milestone B4.7: Regression Verification Gate
- Run full backend regression suite (assert $\ge 200$ tests passing, 0 regressions).
- Run frontend production build `tsc -b && vite build`.

### Milestone B4.8: Release Certification & Tagging
- Update Master Tracker.
- Merge into `main` and tag `business-os-b4-certified`.
- Push commits and tag to remote `origin`.

---

## 3. Implementation Files Overview

| Component | Target File | Purpose |
|---|---|---|
| **Copilot Service** | `backend/services/business/copilot_service.py` | Grounded financial question answering |
| **Risk Engine** | `backend/services/business/cash_risk_service.py` | Proactive cash deficit and concentration detection |
| **Bridge Service** | `backend/services/business/bridge_service.py` | Read-only polymorphic calendar projection |
| **Copilot API** | `backend/api/business/copilot.py` | REST endpoints for Copilot interaction |
| **Risk API** | `backend/api/business/risk.py` | REST endpoints for cash risk alerts |
| **Bridge API** | `backend/api/business/bridge.py` | REST endpoint for unified cross-domain feed |
| **Frontend Client** | `frontend/src/api.ts` | B4 API client methods |
| **Frontend UI** | `frontend/src/components/Business/BusinessCopilotModal.tsx` | Copilot modal interface |
| **Frontend Banner** | `frontend/src/components/Business/CashRiskBanner.tsx` | Interactive cash risk warning banner |
| **Test Suites** | `backend/tests/test_*.py` (4 suites) | Automated verification of B4 features |
