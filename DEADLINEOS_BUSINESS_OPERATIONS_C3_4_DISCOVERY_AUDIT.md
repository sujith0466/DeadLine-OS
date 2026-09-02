# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.4 DISCOVERY AUDIT
**Milestone:** C3.4 — Landed Cost Allocation Engine
**Mode:** Architecture Discovery & Current-State Audit
**Date:** 2026-09-02T14:58:00+05:30
**Baseline Commit:** `6f032e4` (C3.3 freeze)
**Current Alembic Head:** `r5s6t7u8v9w0`
**Database Engine:** Neon Serverless PostgreSQL

---

## 1. Executive Summary

Milestone C3.4 introduces the **Landed Cost Allocation Engine** to DeadlineOS Business Operations. The primary goal is to accurately apportion additional acquisition, logistics, and import expenditures (e.g., international freight, customs clearance, import tariffs/duties, transit insurance, port handling, and customs brokerage) to physically received inventory items (Goods Receipt Notes / GRN lines).

This audit establishes:
1. The **exact financial boundaries** separating operational landed cost from the frozen B0–B8 general ledger and commercial invoices.
2. The **exact data model** for landed cost vouchers, cost items, and line-level allocations.
3. The **currency and exchange rate integration** leveraging C3.1 `ExchangeRateService`.
4. The **deterministic residual-cent allocation algorithm** preventing penny leakage or creation.
5. The **5-tier RBAC matrix** enforcing strict separation of preparation (`ACCOUNTANT`, `MEMBER`, `ADMIN`, `OWNER`) from formal approval (`ADMIN`, `OWNER`).

---

## 2. Current State Inspection & Existing Model Assets

### A. Procurement & Receiving Models (`backend/models/business/`)
- `BusinessPurchaseOrder` (`business_purchase_orders`):
  - Tracks supplier contracts, currency, exchange rate, payment terms, and status.
  - Linked to `BusinessCommercialPartner` (`supplier_partner_id`) and `BusinessLocation` (`destination_location_id`).
- `BusinessPurchaseOrderLine` (`business_purchase_order_lines`):
  - Line items with `ordered_quantity`, `received_quantity`, `unit_price`, and `total_price`.
- `BusinessGoodsReceipt` (`business_goods_receipts`):
  - Physical delivery event (GRN). Linked to `purchase_order_id`, `supplier_partner_id`, and `destination_location_id`.
- `BusinessGoodsReceiptLine` (`business_goods_receipt_lines`):
  - Individual physical delivery line. Contains `purchase_order_line_id`, `product_id`, `received_quantity`, `accepted_quantity`, `rejected_quantity`, `unit_cost`, and `stock_movement_id`.
  - Invariant: `accepted_quantity + rejected_quantity = received_quantity`.

### B. Multi-Currency Engine (`ExchangeRateService` - C3.1)
- `business_exchange_rates`:
  - Stores `workspace_id`, `from_currency`, `to_currency`, `rate` (NUMERIC(18, 6)), `effective_date`, `rate_source`.
  - Supports 1:1 identity, direct lookup, 7-day historical lookback, and inverse pair calculation.
  - `convert_currency(workspace_id, amount, from_currency, to_currency, effective_date)` deterministically returns Decimal converted value.
  - Absence of exchange rate fails safely (`EXCHANGE_RATE_NOT_FOUND`) and never defaults silently to 1.0.

### C. Inventory Ledger & Provenance (`BusinessStockMovement` - C1, C3.2, C3.3)
- `business_stock_movements`:
  - SOLE authoritative inventory quantity truth (`SUM(IN) - SUM(OUT)`).
  - Contains immutable physical stock transactions.
  - Never modified or rewritten by landed cost allocation. Landed cost is operational valuation metadata, not physical quantity.

---

## 3. Financial & Operational Boundary Definition

1. **Non-Negotiable Boundary:**
   - Frozen accounting ledgers (`business_transactions`, `business_invoices`, `payment_allocations`) are **NOT** mutated.
   - Landed cost allocation does **NOT** silently generate double-entry bookkeeping journal entries in C3.4.
   - Landed cost is strictly an **operational cost allocation engine** allowing enterprise inventory to record unit-level true acquisition cost alongside frozen contractual PO purchase prices.
2. **Source Facts vs. Derived Facts:**
   - **Source Facts:** Individual freight invoice, customs duty bill, carrier bill, source currency, date, exchange rate applied.
   - **Derived Facts:** Allocation weight, apportioned landed cost per line, resultant landed cost per unit, cumulative unit cost.
   - Server-side authoritative recalculation: Client-supplied allocations or rounding amounts are never trusted.

---

## 4. Gap Analysis & Scope for C3.4

To support production-grade landed cost allocation:
1. **New Table: `business_landed_cost_vouchers`**:
   - Master voucher tracking reference number, associated PO / GRN, source currency, base currency, allocation basis (`VALUE` or `QUANTITY`), lifecycle status (`DRAFT`, `ALLOCATED`, `APPROVED`, `REVERSED`), total cost, and audit fields.
2. **New Table: `business_landed_cost_voucher_items`**:
   - Itemized expense lines: category (`FREIGHT`, `CUSTOMS`, `DUTIES`, `INSURANCE`, `HANDLING`, `BROKERAGE`, `PORT_CHARGES`, `STORAGE`, `OTHER`), source amount, currency, exchange rate, and converted base amount.
3. **New Table: `business_landed_cost_allocations`**:
   - Persisted derived facts linking voucher to specific `business_goods_receipt_lines`. Stores line base value, allocation weight, allocated base cost, and landed cost per unit.
4. **Deterministic Allocation Engine**:
   - Implements Proportional Value and Proportional Quantity allocation bases.
   - Residual cent rule: Allocates rounding remainder to largest-weight line (with ties resolved to lowest line index).
5. **Immutability & Reversal**:
   - Once approved, vouchers are immutable. Reversals require an auditable reversal action producing a linked compensating state.
6. **RBAC & Tenant Isolation**:
   - 5-tier matrix enforced server-side. Workspace scoping on all queries and mutations.

---

## 5. Alembic Linear Chain Verification
- Current Head: `r5s6t7u8v9w0`
- Target Revision: `s6t7u8v9w0x1`
- Parent Revision: `r5s6t7u8v9w0`
- Linear, non-branching chain maintained.
