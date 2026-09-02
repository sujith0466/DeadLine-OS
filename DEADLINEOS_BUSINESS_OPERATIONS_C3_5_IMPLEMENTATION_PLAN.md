# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.5 IMPLEMENTATION PLAN
**Milestone:** C3.5 — Cross-Border Supply Chain Operations Hub & Copilot Grounding
**Mode:** Step-by-Step Execution Plan
**Date:** 2026-09-02T15:13:00+05:30
**Baseline Commit:** `d849c0d`

---

## 1. Execution Sequence

```
1. Architecture & Discovery Audit [COMPLETED]
2. Architecture Review [COMPLETED]
3. Implementation Plan [CURRENT]
4. Security & AI Red-Team Plan
5. Test Strategy
6. Linear Alembic Migration `t7u8v9w0x1y2_business_os_cross_border_c3_5.py`
7. ORM Model: `BusinessCrossBorderShipment` (`backend/models/business/cross_border.py`)
8. Domain Service: `CrossBorderHubService` (`backend/services/business/cross_border_hub_service.py`)
9. Grounded Copilot Enhancement: `CopilotService` (`backend/services/business/copilot_service.py`)
10. RBAC Matrix Verification & Registration (`backend/middleware/business_context.py`)
11. REST API Blueprint: `backend/api/business/cross_border.py`
12. Frontend API Client Methods (`frontend/src/api.ts`)
13. Migration Verification Test Update (`backend/tests/test_migration_chain_verification.py`)
14. Dedicated Unit & Service Tests (`backend/tests/test_business_cross_border.py`)
15. Live Neon PostgreSQL E2E Gate (`scratch/e2e_c3_5_live.py`)
16. Full Backend Regression (`pytest tests/ -k "not test_gemini" -q`)
17. Frontend Build Verification (`npm --prefix frontend run build`)
18. 7 Protected Personal OS Files 0-byte Diff Verification
19. Final Implementation Audit Document
20. Git Commit, Tag/Release, and Push
21. HARD STOP
```

---

## 2. File Modification & Creation Inventory

| File Path | Action | Description |
| :--- | :--- | :--- |
| `backend/migrations/versions/t7u8v9w0x1y2_business_os_cross_border_c3_5.py` | **NEW** | Alembic migration creating `business_cross_border_shipments`. |
| `backend/models/business/cross_border.py` | **NEW** | ORM model `BusinessCrossBorderShipment`. |
| `backend/models/business/__init__.py` | **MODIFY** | Export `BusinessCrossBorderShipment`. |
| `backend/services/business/cross_border_hub_service.py` | **NEW** | Operational hub service: aggregation, timeline, customs, correlation. |
| `backend/services/business/copilot_service.py` | **MODIFY** | Fully grounded copilot with FACT/SIGNAL/FORECAST/REC separation, deterministic routing, injection guardrails. |
| `backend/services/business/__init__.py` | **MODIFY** | Export `CrossBorderHubService`. |
| `backend/middleware/business_context.py` | **MODIFY** | Register `cross_border:*` permissions across the 5 RBAC tiers. |
| `backend/api/business/cross_border.py` | **NEW** | REST API endpoints for hub, shipments, timeline, copilot grounded query. |
| `backend/api/business/__init__.py` | **MODIFY** | Mount `cross_border_bp` at `/cross-border`. |
| `frontend/src/api.ts` | **MODIFY** | Add client methods for cross-border hub and grounded copilot. |
| `backend/tests/test_migration_chain_verification.py` | **MODIFY** | Register revision `t7u8v9w0x1y2` and new table. |
| `backend/tests/test_business_cross_border.py` | **NEW** | Unit & service test suite covering all C3.5 capabilities. |
| `scratch/e2e_c3_5_live.py` | **NEW** | 19 live Neon Serverless PostgreSQL E2E scenarios. |
| `DEADLINEOS_BUSINESS_OPERATIONS_C3_5_IMPLEMENTATION_AUDIT.md` | **NEW** | Final implementation audit report. |
