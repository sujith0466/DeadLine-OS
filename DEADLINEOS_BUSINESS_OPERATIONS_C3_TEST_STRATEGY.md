# DEADLINEOS BUSINESS OPERATIONS — PHASE C3 TEST STRATEGY
# COMPREHENSIVE VERIFICATION & E2E PROTOCOL

**Document ID**: `C3-TEST-001`
**Execution Timestamp**: 2026-09-02T14:18:00Z
**Governance Mode**: TEST STRATEGY SPECIFICATION ONLY

---

## 1. Test Architecture Overview

Every Phase C3 milestone must pass the complete 20-category verification matrix before freeze and release:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     C3 TEST HARNESS PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────┤
│ Tier 1: Domain & Unit Tests (Decimal math, penny rounding, state logic) │
│ Tier 2: Service & Invariant Tests (Ledger sync, batch/serial bounds)    │
│ Tier 3: REST API & Security Tests (RBAC 5-tier matrix, IDOR isolation)  │
│ Tier 4: Live PostgreSQL E2E Suites (Executed on live Neon DB)           │
│ Tier 5: Full Regression Suite (All 343 existing B0-B8 + C1 + C2 tests)  │
│ Tier 6: Frontend Production Build (`tsc -b && vite build` clean)        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Test Category Specifications (Categories A through T)

| ID | Category | Scope & Assertion Mandate |
| :--- | :--- | :--- |
| **A** | **Unit Tests** | Tests deterministic calculation functions, string normalizers, and enum validators in isolation. |
| **B** | **Service Tests** | Tests `ExchangeRateService`, `BatchService`, `SerialNumberService`, `LandedCostService`. |
| **C** | **API Integration Tests** | Tests HTTP request-response contracts, status codes (200, 201, 400, 403, 404, 409). |
| **D** | **RBAC Tests** | Verifies all 5 tiers: `OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER` (zero `MANAGER` role). |
| **E** | **Tenant Isolation Tests** | Asserts Workspace A queries cannot read or list Workspace B batches, serials, or vouchers. |
| **F** | **IDOR Tests** | Asserts direct UUID manipulation cross-workspace returns HTTP 404 or 403. |
| **G** | **Decimal Arithmetic Tests** | Asserts exact Decimal precision, no float contamination, exact 2-decimal rounding. |
| **H** | **Migration Integrity Tests** | Verifies Alembic head remains single-branch linear chain with clean upgrade & downgrade. |
| **I** | **Auditability Tests** | Asserts `AuditEvent` emitted for all batch state changes, serial moves, landed cost allocations, and FX overrides. |
| **J** | **Inventory Ledger Invariant** | Asserts `business_stock_movements` remains the sole quantity truth (`SUM(IN) - SUM(OUT)`). |
| **K** | **Batch Quantity Invariant** | Asserts `SUM(batch_movements) == movement_quantity` and `OUT <= available_batch_qty`. |
| **L** | **Serial Uniqueness Tests** | Asserts composite unique constraint on `(workspace_id, product_id, serial_number)` cannot be violated. |
| **M** | **Expiry Lifecycle Tests** | Asserts `current_date > expiry_date` transitions batch to `EXPIRED` and blocks normal dispatch. |
| **N** | **Landed Cost Allocation Tests**| Asserts sum of allocated lines equals voucher total down to the exact penny ($\Delta = 0.00$). |
| **O** | **FX Conversion Tests** | Asserts multi-currency conversion produces exact base currency equivalent using registered rate. |
| **P** | **Historical FX Reproducibility** | Asserts historical documents lock exchange rates and do not change when current rates are updated. |
| **Q** | **Cross-Border Procurement E2E** | Multi-stage lifecycle testing from PO creation to customs duty allocation and stock entry. |
| **R** | **PostgreSQL Live E2E** | Executed directly against Neon Serverless PostgreSQL with live network transactions. |
| **S** | **Frontend Production Build** | Compiles with `npm --prefix frontend run build` (`tsc -b && vite build`) with 0 errors. |
| **T** | **Full Regression Suite** | Runs all 343 existing backend tests to guarantee 100% backward compatibility. |

---

## 3. Authoritative C3 E2E Scenario Catalog

### E2E-1: International Supplier $\rightarrow$ PO $\rightarrow$ Foreign Currency $\rightarrow$ GRN
- **Workflow**:
  1. Commercial partner configured with default currency `'USD'`.
  2. PO created for 500 units at `$45.00 USD` (Total: `$22,500.00 USD`).
  3. System records exchange rate `1 USD = 84.500000 INR`. Derived base reporting amount = `₹1,901,250.00 INR`.
  4. PO approved and sent to supplier.
  5. GRN created upon physical arrival; 500 units accepted into `Central Warehouse`.
  6. `BusinessStockMovement` created with `quantity=500`, `movement_type='PURCHASE_RECEIVED'`.

### E2E-2: GRN $\rightarrow$ Batch Creation $\rightarrow$ Quantity Validation
- **Workflow**:
  1. GRN receiving line specifies batch `LOT-2026-AUG-99`, manufacture date `2026-08-01`, expiry date `2027-08-01`.
  2. System records `BusinessBatch` linked to GRN.
  3. Physical stock movement attributes 500 units to `LOT-2026-AUG-99`.
  4. Querying batch available stock yields exactly `500.00`.
  5. Attempting to issue 550 units from this batch is rejected with HTTP 400 `INSUFFICIENT_BATCH_STOCK`.
  6. Issuing 100 units leaves exactly `400.00` available batch stock.

### E2E-3: GRN $\rightarrow$ Serial Creation $\rightarrow$ Uniqueness Validation
- **Workflow**:
  1. Serialized product received on GRN with 5 units and serials: `[SN-001, SN-002, SN-003, SN-004, SN-005]`.
  2. All 5 serials registered in `IN_STOCK` state at `Depot 1`.
  3. Attempting to receive `SN-003` a second time in any location is rejected with HTTP 409 `SERIAL_ALREADY_EXISTS`.
  4. Attempting to transfer `SN-002` from `Depot 2` (where it does not exist) is rejected with HTTP 400 `SERIAL_NOT_AT_LOCATION`.

### E2E-4: Expiry Warning / Expired Inventory Behavior
- **Workflow**:
  1. Batch `LOT-EXP-01` created with expiry date set to yesterday (`current_date - 1 day`).
  2. Batch status evaluated as `EXPIRED`.
  3. Attempting to create a `SALE` stock movement using `LOT-EXP-01` is strictly rejected with HTTP 400 `BATCH_EXPIRED`.
  4. Quarantining or writing off as `DAMAGED` is allowed, removing it from active stock.

### E2E-5: Freight + Customs + Insurance $\rightarrow$ Deterministic Landed Cost
- **Workflow**:
  1. GRN with 2 product lines: Line 1 (100 units at ₹100.00, value ₹10,000) and Line 2 (50 units at ₹400.00, value ₹20,000). Total value = ₹30,000.
  2. Landed Cost Voucher created with:
     - Freight: ₹3,000 (Allocated by Value: 1/3 to Line 1 = ₹1,000, 2/3 to Line 2 = ₹2,000).
     - Customs Duty: ₹1,500 (Allocated by Value: ₹500 to Line 1, ₹1,000 to Line 2).
     - Insurance: ₹100 (Allocated by Value: ₹33.33 to Line 1, ₹66.67 to Line 2).
  3. Verify penny residual is deterministically resolved: total allocated across all lines exactly equals ₹4,600.00.
  4. True Landed Unit Cost:
     - Line 1: Purchase ₹100.00 + Allocated ₹15.33 = ₹115.33 per unit.
     - Line 2: Purchase ₹400.00 + Allocated ₹61.34 = ₹461.34 per unit.

### E2E-6: Foreign Currency PO $\rightarrow$ Historical FX Conversion
- **Workflow**:
  1. PO-101 created on 2026-08-01 for `$5,000 USD` at rate `83.50 INR/USD` (Valuation: ₹417,500).
  2. On 2026-08-20, current exchange rate is updated to `85.00 INR/USD`.
  3. Querying PO-101 reports original locked rate `83.50` and reporting valuation ₹417,500.
  4. Historical financial fact is preserved without retroactive distortion.

### E2E-7: Cross-Tenant Access Attempt $\rightarrow$ Rejection
- **Workflow**:
  1. Tenant A creates Batch `BATCH-SECRET-A`.
  2. Tenant B issues API request `GET /api/business/inventory/batches/<batch_a_id>`.
  3. Server rejects with HTTP 404 `NOT_FOUND` (no information leakage).
  4. Tenant B attempts to allocate Tenant A's batch in a stock movement $\rightarrow$ rejected with HTTP 404.

### E2E-8: RBAC Unauthorized Mutation $\rightarrow$ Rejection
- **Workflow**:
  1. User with `VIEWER` role attempts to record batch receiving $\rightarrow$ HTTP 403 Forbidden.
  2. User with `MEMBER` role attempts to approve Landed Cost Voucher $\rightarrow$ HTTP 403 Forbidden.
  3. User with `ACCOUNTANT` role attempts to quarantine physical batch $\rightarrow$ HTTP 403 Forbidden.
  4. User with `ADMIN` role performs the operations $\rightarrow$ HTTP 200/201 Success.

### E2E-9: Correction/Reversal of Landed Cost Data
- **Workflow**:
  1. Landed Cost Voucher `LCV-001` allocated and frozen.
  2. Customs department issues revised assessment reducing duty by ₹500.
  3. `LandedCostService.create_reversal_voucher` creates `LCV-001-REV` with negative adjustment lines.
  4. Historical `LCV-001` remains intact in audit history.

### E2E-10: Full International Procurement $\rightarrow$ Receiving $\rightarrow$ Traceability $\rightarrow$ Landed Cost $\rightarrow$ Reporting
- **Workflow**:
  1. International PO in EUR $\rightarrow$ Goods arrival at port $\rightarrow$ GRN with batch and serial registration.
  2. Carrier freight in USD + Customs duty in INR logged on Landed Cost Voucher.
  3. Deterministic allocation to product lines and batches.
  4. Product catalog updated with derived landed valuation.
  5. Copilot queried for true gross margin on batch $\rightarrow$ cites exact landed cost fact.
