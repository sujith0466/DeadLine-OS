# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.4 ARCHITECTURE REVIEW
**Milestone:** C3.4 — Landed Cost Allocation Engine
**Mode:** Architecture & Mathematical Specification
**Date:** 2026-09-02T14:58:30+05:30
**Baseline Commit:** `6f032e4`

---

## 1. Architectural Principles & Invariants

1. **Authoritative Quantity Ledger Invariant**:
   `business_stock_movements` remains the sole physical quantity ledger. Landed cost allocates monetary acquisition overhead to received inventory units without modifying physical quantities or stock balances.

2. **Exact Decimal Reconciliation Invariant**:
   For any approved or allocated voucher:
   $$\sum_{i=1}^{N} \text{AllocatedCost}_i == \text{TotalAllocatableBaseCost}$$
   Exact Decimal equality is guaranteed. Zero penny creation, zero penny loss.

3. **Deterministic Residual Cent Assignment Rule**:
   When fractional cents emerge from proportional distribution:
   - Calculate line share: $\text{RawShare}_i = \text{TotalAllocatableBaseCost} \times \text{Weight}_i$
   - Quantize to 2 decimal places using `ROUND_HALF_UP`: $\text{Allocated}_i = \text{quantize}(\text{RawShare}_i, \text{Decimal}('0.01'))$
   - Compute residual: $\Delta = \text{TotalAllocatableBaseCost} - \sum_{i=1}^{N} \text{Allocated}_i$
   - If $\Delta \ne 0$:
     - Assign $\Delta$ (positive or negative) to the line with the **strictly largest allocation weight** ($\max(\text{Weight}_i)$).
     - If two or more lines tie for largest weight: Assign $\Delta$ to the line with the **lowest line index** ($\min(\text{Index}_i)$).

4. **Multi-Currency & FX Provenance**:
   - Each cost item records its source currency, source amount, effective exchange rate, and base currency amount.
   - Exchange rate is resolved via C3.1 `ExchangeRateService.get_exchange_rate()` based on effective date.
   - If source currency equals workspace base currency, exchange rate is exactly `1.000000`.
   - Missing foreign exchange rates fail safely (`EXCHANGE_RATE_NOT_FOUND`) and are never defaulted to `1.0`.

5. **Voucher Immutability & State Machine**:
   - States: `DRAFT` $\rightarrow$ `ALLOCATED` $\rightarrow$ `APPROVED`
   - Terminal state: `REVERSED` (triggered via governed reversal)
   - In `APPROVED` state:
     - No items can be added, updated, or deleted.
     - No allocations can be re-run or mutated.
     - The voucher and its allocations become strictly read-only.
   - Reversal creates an auditable record, setting status to `REVERSED` and referencing the reversing action.

---

## 2. Allocation Bases

The engine supports two procurement-authoritative allocation bases:

### Basis A: Proportional by Value (`allocation_basis = 'VALUE'`)
Authoritative when freight and duties correspond to invoice line value (e.g., ad valorem customs tariffs, insurance):
$$\text{LineBaseValue}_i = \text{AcceptedQuantity}_i \times \text{UnitCost}_i$$
$$\text{TotalBasisValue} = \sum_{i=1}^{N} \text{LineBaseValue}_i$$
$$\text{Weight}_i = \frac{\text{LineBaseValue}_i}{\text{TotalBasisValue}}$$

### Basis B: Proportional by Quantity (`allocation_basis = 'QUANTITY'`)
Authoritative when logistics and handling costs scale per piece/container (e.g., flat handling, per-unit inspection, container offloading):
$$\text{TotalBasisQuantity} = \sum_{i=1}^{N} \text{AcceptedQuantity}_i$$
$$\text{Weight}_i = \frac{\text{AcceptedQuantity}_i}{\text{TotalBasisQuantity}}$$

---

## 3. Provenance & Downstream Traceability

Landed cost preserves full end-to-end provenance:
```
Commercial Partner (Supplier / Carrier / Customs Broker)
       │
       ▼
Purchase Order (business_purchase_orders)
       │
       ▼
Goods Receipt Note (business_goods_receipts)
       │
       ▼
Goods Receipt Line (business_goods_receipt_lines)
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
Physical Stock Movement                  Landed Cost Voucher
(business_stock_movements)               (business_landed_cost_vouchers)
       │                                         │
       ▼                                         ▼
Batches & Serials                        Voucher Items & Allocation
(C3.2 / C3.3)                            (business_landed_cost_allocations)
```

---

## 4. 5-Tier RBAC Permission Matrix

| Role | `landed_cost:read` | `landed_cost:write` | `landed_cost:allocate` | `landed_cost:approve` | `landed_cost:reverse` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **OWNER** | Allowed | Allowed | Allowed | Allowed | Allowed |
| **ADMIN** | Allowed | Allowed | Allowed | Allowed | Allowed |
| **ACCOUNTANT** | Allowed | Allowed | Allowed | Denied | Denied |
| **MEMBER** | Allowed | Denied | Denied | Denied | Denied |
| **VIEWER** | Allowed | Denied | Denied | Denied | Denied |
