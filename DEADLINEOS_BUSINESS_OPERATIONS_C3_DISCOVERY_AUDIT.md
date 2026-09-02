# DEADLINEOS BUSINESS OPERATIONS — PHASE C3 DISCOVERY AUDIT
# ADVANCED LOGISTICS & CROSS-BORDER SUPPLY CHAIN DISCOVERY

**Document ID**: `C3-DISCOVERY-001`
**Execution Timestamp**: 2026-09-02T14:10:00Z
**Baseline Git Commit**: `8c95698` (Phase C2 Master Certification Synchronization)
**Governance Mode**: DISCOVERY & AUDIT ONLY (Implementation Strictly Forbidden)

---

## 1. Executive Summary

This discovery audit investigates the current state of DeadlineOS Business Operations (B0–B8, C1, and C2.1–C2.6), evaluates the existing data models, database migration history, service abstractions, API endpoints, and user interface workflows, and identifies architectural capabilities, reusable foundations, domain gaps, and frozen invariants relevant to **Phase C3: Advanced Logistics & Cross-Border Supply Chain**.

### Key Findings
1. **Authoritative Quantity Foundation is Intact**:
   - The authoritative operational inventory quantity is derived solely from the append-only ledger `business_stock_movements` (`SUM(IN) - SUM(OUT)`).
   - This invariant has been preserved through C1, C2.1, and C2.2.
   - Any C3 batch, expiry, or serial tracking capability **must strictly be modeled as an attribution extension of `business_stock_movements`**, never as a competing mutable quantity column (such as `current_quantity` or `available_balance` on product or location tables).
2. **Current Currency Model is Nominally Single-Currency with Fragmented Fields**:
   - `Workspace.base_currency` defaults to `'INR'`.
   - `Invoice`, `BusinessTransaction`, `BusinessPurchaseOrder`, and `BusinessProduct` each store an isolated `currency = db.Column(db.String(3), default='INR')` string.
   - However, **no exchange rate table, historical FX rate provenance, or deterministic multi-currency conversion service exists**.
   - If an invoice or PO is recorded in `'USD'`, the system currently performs calculations nominally without currency normalization.
   - **Critical Architectural Dependency**: Multi-currency and FX provenance is a mandatory prerequisite for cross-border landed cost allocation.
3. **Goods Receiving (GRN) Captures Physical Arrival, but Lacks Batch/Serial & Commercial Landed Cost**:
   - C2.2 established `BusinessGoodsReceipt` and `BusinessGoodsReceiptLine`.
   - Each accepted line item immediately posts a `BusinessStockMovement(movement_type='PURCHASE_RECEIVED', direction='IN', quantity=accepted_qty, unit_cost=po_line.unit_price)`.
   - Currently, `unit_cost` is locked to the FOB purchase price. There is no mechanism to allocate international ocean/air freight, import customs duty, marine insurance, or port handling fees across SKU lines.
   - There are no columns or foreign keys on GRN lines or stock movements for batch/lot numbers, manufacturing dates, expiration dates, or individual unit serial numbers.
4. **Frozen Boundaries are Completely Respected**:
   - All 7 Personal OS files maintain a verified 0-byte diff.
   - Business OS B0–B8 financial truth (`business_transactions`, `business_invoices`, payment allocations, cash positions) remains untainted.
   - Alembic migration head is confirmed at `o2l3m4n5o6p7` with a single linear revision chain.

---

## 2. Inventory of Existing Reusable Infrastructure

| Subsystem | Existing Component | Reusability in Phase C3 | Architectural Boundary & Constraints |
| :--- | :--- | :--- | :--- |
| **Inventory Ledger** | `BusinessStockMovement` & `InventoryService` | **Authoritative Quantity Engine** | `SUM(IN) - SUM(OUT)` is immutable. Batches & Serials attach via attribution; ledger never replaced. |
| **Procurement** | `BusinessPurchaseOrder` & `PurchaseOrderService` | **Commercial Contract Inception** | Extensible with `currency`, `exchange_rate`, `base_currency_total`, and incoterms. |
| **Goods Receiving** | `BusinessGoodsReceipt` & `GoodsReceiptService` | **Physical Intake Gateway** | GRN lines serve as the physical entry point for batch/lot creation and serial registration. |
| **Commercial Partners** | `CommercialPartner` & `PartnerService` | **Counterparty Master** | Extensible with `default_currency`, `country_code`, `incoterms`, and customs identifiers. |
| **Staging Gateway** | `StagedExtraction` & `StagingService` | **Zero-Bypass Input Boundary** | External bills of entry, carrier AWB/BOL, and customs documents route via `NEEDS_REVIEW`. |
| **Audit & Forensic Trail** | `AuditEvent` & `AuditService` | **Regulatory Compliance Logging** | Every batch split, serial state transition, landed cost calculation, and FX override is logged. |
| **Operational Alerts** | `BusinessOperationalAlert` & `OperationalAlertService` | **Early Warning Telemetry** | Directly extensible with `BATCH_EXPIRING_SOON`, `BATCH_EXPIRED`, and `FX_VOLATILITY_WARNING`. |
| **Business Copilot** | `CopilotService` | **Conversational Grounding** | Grounded in live batch expiry dates, serial provenance, and landed margins without hallucination. |

---

## 3. Architectural Gap Analysis

### Gap 1: Landed Cost Allocation Framework (Missing)
- **Current State**: Products are valued exclusively at their raw PO line unit price (`unit_price`).
- **Real-World Reality**: In cross-border logistics, freight, customs duties, insurance, and handling typically represent 15% to 45% of total product cost. Valuing inventory at FOB price severely distorts gross margin, inventory valuation, and pricing decisions.
- **Missing Architecture**:
  1. Landed cost document model (`BusinessLandedCostVoucher`).
  2. Cost component itemization (Freight, Customs Duty, Insurance, Handling, Surcharge).
  3. Deterministic allocation algorithms (By Line Value, By Quantity, By Weight, By Volume).
  4. Exact decimal penny-residual reconciliation.
  5. Immutable allocation records preventing silent historical tampering.

### Gap 2: Batch, Lot & Expiry Date Management (Missing)
- **Current State**: Inventory is fungible per product per location. Products with different production dates, batches, or expiration dates are commingled.
- **Real-World Reality**: Regulated goods (chemicals, pharmaceuticals, food, electronics, high-reliability fasteners) require strict batch traceability and First-Expired, First-Out (FEFO) controls.
- **Missing Architecture**:
  1. `BusinessBatch` master entity (`batch_number`, `product_id`, `mfg_date`, `expiry_date`, `supplier_id`).
  2. Linking batch attribution to `BusinessStockMovement` so batch stock equals movement sum.
  3. Quarantine and expiry state machine (`FRESH` $\rightarrow$ `EXPIRING_SOON` $\rightarrow$ `EXPIRED` $\rightarrow$ `QUARANTINED`).
  4. FEFO advisory dispatch engine for sales orders, transfers, and consumption.

### Gap 3: Serial Number Tracking (Missing)
- **Current State**: High-value serialized assets and equipment cannot be tracked by unique serial identifier.
- **Missing Architecture**:
  1. `BusinessSerialNumber` entity (`serial_number`, `product_id`, `current_location_id`, `status`).
  2. Lifecycle states (`IN_STOCK`, `ALLOCATED`, `SHIPPED`, `DEFECTIVE`, `CONSUMED`).
  3. Strict single-location invariant (a serial cannot exist in multiple locations).
  4. Receiving validation (a serial cannot be received twice).

### Gap 4: Multi-Currency & Exchange Rate Provenance (Missing)
- **Current State**: Currency codes are stored as plain strings without exchange rate linkage or historical conversion tracking.
- **Missing Architecture**:
  1. `BusinessExchangeRate` registry (`from_currency`, `to_currency`, `rate`, `effective_date`, `provenance`).
  2. Deterministic conversion utility maintaining exact Decimal precision.
  3. Distinction between Source Fact (`10,000 USD`) and Derived Reporting Fact (`845,000 INR`).
  4. Strict locking of historical FX rates at document confirmation time.

---

## 4. Architectural Conflicts & Risk Identification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      POTENTIAL CONFLICT MATRIX                          │
├─────────────────────────────────────────────────────────────────────────┤
│ Conflict 1: Dual Quantity Truth Risk                                    │
│ Risk: Adding a `remaining_quantity` column on `BusinessBatch` that is   │
│ updated directly, bypassing `BusinessStockMovement`.                    │
│ Resolution: Enforce that all batch changes require an underlying        │
│ `BusinessStockMovement` record with batch attribution.                  │
│                                                                         │
│ Conflict 2: Financial Ledger Contamination                              │
│ Risk: Landed cost calculations directly altering frozen                 │
│ `business_transactions` or `business_invoices`.                         │
│ Resolution: Landed cost vouchers remain commercial operational entities.│
│ Financial reconciliation occurs via existing accounts payable staging.  │
│                                                                         │
│ Conflict 3: Retroactive Historical Landed Cost Modification             │
│ Risk: Modifying historical landed cost allocations after stock has      │
│ already been sold or moved.                                             │
│ Resolution: Landed cost allocations are immutable. Revisions require a  │
│ new revision voucher with reversal lines and audit trail.               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Audit Conclusion & Gate Recommendation

The DeadlineOS repository baseline is clean, stable, and ready for C3 architecture specification. No breaking changes or regressions to B0–B8, C1, or C2 exist. Proceeding to detailed architecture design.
