# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.4 IMPLEMENTATION PLAN
**Milestone:** C3.4 — Landed Cost Allocation Engine
**Mode:** Step-by-Step Execution Plan
**Date:** 2026-09-02T14:58:50+05:30
**Baseline Commit:** `6f032e4`

---

## 1. Execution Sequence

```
1. Architecture & Discovery Audit [COMPLETED]
2. Architecture Review [COMPLETED]
3. Implementation Plan [CURRENT]
4. Financial & Security Red-Team Plan
5. Test Strategy
6. Database Migration (Revision `s6t7u8v9w0x1`)
7. ORM Models Definition (`backend/models/business/landed_cost.py`)
8. Domain Service (`backend/services/business/landed_cost_service.py`)
9. 5-Tier RBAC Integration (`backend/middleware/business_context.py`)
10. REST API Endpoints (`backend/api/business/landed_cost.py`)
11. Frontend API Client (`frontend/src/api.ts`)
12. Migration Chain Verification Test (`test_migration_chain_verification.py`)
13. Dedicated Unit & Integration Tests (`backend/tests/test_business_landed_cost.py`)
14. Live Neon PostgreSQL E2E Gate (`scratch/e2e_c3_4_live.py`)
15. Full Backend Regression (`pytest tests/ -k "not test_gemini" -q`)
16. Frontend Build Verification (`npm --prefix frontend run build`)
17. 7 Protected Personal OS Files 0-byte Diff Check
18. Final Implementation Audit Document
19. Git Commit, Tag/Release, and Push
20. HARD STOP
```

---

## 2. File Modification & Creation Inventory

| File Path | Action | Description |
| :--- | :--- | :--- |
| `backend/migrations/versions/s6t7u8v9w0x1_business_os_landed_cost_c3_4.py` | **NEW** | Alembic migration for 3 landed cost tables. |
| `backend/models/business/landed_cost.py` | **NEW** | Models `BusinessLandedCostVoucher`, `BusinessLandedCostVoucherItem`, `BusinessLandedCostAllocation`. |
| `backend/models/business/__init__.py` | **MODIFY** | Export landed cost models and register in `__all__`. |
| `backend/services/business/landed_cost_service.py` | **NEW** | Domain service for voucher lifecycle, currency conversion, proportional allocation, residual-cent rule, and reversal. |
| `backend/services/business/__init__.py` | **MODIFY** | Export `LandedCostService`. |
| `backend/middleware/business_context.py` | **MODIFY** | Add `landed_cost:*` permissions to 5-tier RBAC matrix. |
| `backend/api/business/landed_cost.py` | **NEW** | REST API endpoints for vouchers, cost items, preview, allocation, approval, reversal. |
| `backend/api/business/__init__.py` | **MODIFY** | Register `landed_cost_bp` mounted at `/landed-cost`. |
| `frontend/src/api.ts` | **MODIFY** | Add client methods for landed cost API. |
| `backend/tests/test_migration_chain_verification.py` | **MODIFY** | Add `s6t7u8v9w0x1` to expected chain and table list. |
| `backend/tests/test_business_landed_cost.py` | **NEW** | Comprehensive unit & integration test suite. |
| `scratch/e2e_c3_4_live.py` | **NEW** | Live Neon PostgreSQL E2E gate script. |
| `DEADLINEOS_BUSINESS_OPERATIONS_C3_4_IMPLEMENTATION_AUDIT.md` | **NEW** | Final release audit report. |

---

## 3. Decimal Precision & Rounding Standard

- Currency amounts: `Decimal('0.01')` using `ROUND_HALF_UP`.
- Exchange rates: `Decimal('0.000001')` (6 decimal places).
- Allocation weights: `Decimal('0.00000001')` (8 decimal places).
- Landed cost per unit: `Decimal('0.0001')` (4 decimal places).
- Floating-point types (`float`) are **strictly prohibited** in all financial and cost calculations.
