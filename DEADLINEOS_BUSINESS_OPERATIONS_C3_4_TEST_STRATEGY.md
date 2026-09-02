# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.4 TEST STRATEGY
**Milestone:** C3.4 — Landed Cost Allocation Engine
**Mode:** Quality Assurance & Verification Architecture
**Date:** 2026-09-02T14:59:30+05:30
**Baseline Commit:** `6f032e4`

---

## 1. Test Layer Architecture

| Test Layer | Framework / Harness | Purpose | Target Gate |
| :--- | :--- | :--- | :--- |
| **Migration Verification** | `pytest tests/test_migration_chain_verification.py` | Validates linear Alembic revision chain and table registration. | 100% PASS |
| **Dedicated Unit & Service Tests** | `pytest tests/test_business_landed_cost.py` | Unit test suite covering model constraints, allocation math, residual cents, FX conversion, state machine, and RBAC. | 100% PASS |
| **Live Neon PostgreSQL E2E** | `python scratch/e2e_c3_4_live.py` | Multi-scenario live production DB verification against Neon Serverless PostgreSQL. | 100% PASS (14/14) |
| **Full Backend Regression** | `pytest tests/ -k "not test_gemini" -q` | Full regression testing across B0–B8, C1, C2, C3.1, C3.2, C3.3, C3.4. | 100% PASS (370+ tests) |
| **Frontend TypeScript Build** | `npm --prefix frontend run build` | Full production build (`tsc -b && vite build`) for client API types. | 0 errors |
| **Protected Files Diff** | `git diff -- <7 protected files>` | Verifies 0-byte diff on Personal OS protected files. | 0 bytes diff |

---

## 2. Dedicated Unit & Service Test Scenarios (`test_business_landed_cost.py`)

1. `test_voucher_creation_and_defaults`: Creates draft voucher with reference numbers, verifies defaults.
2. `test_cost_item_creation_and_recalculation`: Adds itemized costs, verifies total calculation and positive constraint.
3. `test_proportional_value_allocation`: Verifies value-based allocation with multiple lines.
4. `test_proportional_quantity_allocation`: Verifies quantity-based allocation.
5. `test_deterministic_residual_cent_rule`: Verifies odd fractional cent allocation assigned to largest-weight line (and lowest index tiebreak).
6. `test_exact_total_reconciliation`: Verifies sum of allocations == voucher total down to the exact cent.
7. `test_foreign_currency_cost_conversion`: Verifies multi-currency item conversion via `ExchangeRateService`.
8. `test_missing_exchange_rate_rejection`: Verifies failure when foreign currency rate is absent.
9. `test_voucher_immutability_after_approval`: Verifies mutating an approved voucher raises `VOUCHER_IMMUTABLE`.
10. `test_reversal_lifecycle`: Verifies reversing an approved voucher marks status `REVERSED` and logs audit trail.
11. `test_tenant_isolation_landed_cost`: Cross-tenant lookup or mutation returns HTTP 404 / error.
12. `test_rbac_landed_cost_matrix`: Verifies 5-tier matrix (`landed_cost:read`, `write`, `allocate`, `approve`, `reverse`).

---

## 3. Live Neon PostgreSQL E2E Scenarios (`e2e_c3_4_live.py`)

- **E2E-1:** Create procurement fixture with multiple received lines (PO + GRN).
- **E2E-2:** Create landed cost voucher with valid freight/customs items.
- **E2E-3:** Allocate landed cost using Value basis; verify sum(allocations) == voucher total.
- **E2E-4:** Verify deterministic residual-cent behavior on an uneven 3-way split.
- **E2E-5:** Verify foreign-currency cost item conversion using historical FX rate.
- **E2E-6:** Verify missing FX rate fails safely (`EXCHANGE_RATE_NOT_FOUND`) and does not default to 1.0.
- **E2E-7:** Verify allocated cost is accurately mapped to GRN lines and product context.
- **E2E-8:** Verify approved voucher is strictly immutable.
- **E2E-9:** Verify authorized approval succeeds.
- **E2E-10:** Verify unauthorized approval fails (`ACCOUNTANT`, `MEMBER`, `VIEWER`).
- **E2E-11:** Verify cross-tenant voucher/PO/GRN access fails.
- **E2E-12:** Verify audit events for allocation, approval, and reversal.
- **E2E-13:** Verify double-allocation or race condition prevention.
- **E2E-14:** Verify C3.2 batch and C3.3 serial provenance remains intact.
