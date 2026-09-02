# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.5 DISCOVERY AUDIT
**Milestone:** C3.5 — Cross-Border Supply Chain Operations Hub & Copilot Grounding
**Mode:** Architecture Discovery & Current-State Audit
**Date:** 2026-09-02T15:12:00+05:30
**Baseline Commit:** `d849c0d` (C3.4 freeze)
**Current Alembic Head:** `s6t7u8v9w0x1`
**Database Engine:** Neon Serverless PostgreSQL

---

## 1. Executive Summary

Milestone C3.5 establishes the unified **Cross-Border Supply Chain Operations Hub** and the **Grounded Business Copilot**. 
Its dual objective is to:
1. Provide single-pane-of-glass operational visibility and deterministic correlation across suppliers, Purchase Orders (PO), multi-currency exchange rates, cross-border shipments, customs clearance, Goods Receipt Notes (GRN), inventory stock movements, batch/expiry provenance, serialized unit tracking, and landed-cost allocations.
2. Ground the conversational Business Copilot in verified, authoritative domain facts, enforcing a strict semantic contract that cleanly separates **FACTS**, **SIGNALS**, **FORECASTS**, and **RECOMMENDATIONS**, while eliminating hallucinations through deterministic query routing and safety-gated human-review staging for mutation proposals.

---

## 2. Existing vs. New vs. Deferred Capability Audit

| Domain | Existing Capability (Frozen B0–C3.4) | New C3.5 Capability | Deferred (C4/C5/Future) |
| :--- | :--- | :--- | :--- |
| **Procurement** | `BusinessPurchaseOrder`, PO lines, supplier partner linkage, approval workflow | Correlated cross-border procurement view in Operations Hub | Autonomous supplier purchase order creation |
| **Receiving** | `BusinessGoodsReceipt`, GRN lines, quality inspection, accepted/rejected quantities | Linkage to shipment carrier, customs release, and operational timeline | Automated dock sensor intake |
| **Inventory Quantity** | `business_stock_movements` (sole authoritative ledger) | Read-model aggregation of on-hand inventory across transit & warehouses | Computer-vision shelf stock counting (C4) |
| **Batch Provenance** | `business_batches`, FEFO suggestions, quarantine lifecycle (C3.2) | Shipment-to-batch traceability, shelf-life risk signals | IoT temperature sensor monitoring (C5) |
| **Serial Provenance** | `business_serial_numbers`, unit lifecycle, quarantine (C3.3) | Shipment-to-serial traceability, warranty & delivery timeline correlation | RFID gate antenna telemetry (C5) |
| **Landed Cost** | `business_landed_cost_vouchers`, itemized costs, line allocations (C3.4) | Landed cost visibility per shipment and per received PO line | Automated accounting ledger posting |
| **Currency & FX** | `business_exchange_rates`, 7-day lookback, Decimal conversion (C3.1) | Cross-border declared customs currency vs base currency reconciliation | Automated FX hedging / forward contracts |
| **Shipment Tracking** | Carrier name/tracking on GRN (rudimentary text) | `business_cross_border_shipments`: structured shipment lifecycle, origin/dest countries, bills of lading, ports | Full Transportation Management System (TMS), carrier EDI integration |
| **Customs / Import** | None | Operational customs reference, duty amounts, clearance status, customs hold | Automated customs declaration filing |
| **Business Copilot** | Financial cash position, basic receivables/payables, simple PO count (C2.6) | Fully grounded copilot across all C3 domains, semantic separation (FACT/SIGNAL/FORECAST/REC), deterministic query dispatch | Unsupervised autonomous agent mutations |
| **Action Safety** | `StagedExtraction` with manual confirmation (B7) | AI-generated operational proposals staged as `StagedExtraction` for human review | Direct voice or prompt-triggered database writes |

---

## 3. Strict Source-of-Truth Mapping

Every metric and field displayed in the Cross-Border Operations Hub and reported by the Grounded Copilot must originate from an authoritative source. Zero duplicate competing ledgers are permitted:

```
[Operational Metric]                  [Sole Authoritative Source]
Physical Stock On-Hand              → business_stock_movements (SUM(IN) - SUM(OUT))
Batch Expiry & Availability         → business_batches + stock movement attribution
Serial Status & Location            → business_serial_numbers
Purchase Order Value & Status       → business_purchase_orders (subtotal_amount, status)
Exchange Rate & FX Provenance       → business_exchange_rates (rate, rate_source, effective_date)
Landed Cost Apportionment           → business_landed_cost_allocations (allocated_cost_base_currency)
Goods Receipt Physical Delivery     → business_goods_receipt_lines (accepted_quantity)
Commercial Partner / Supplier       → business_commercial_partners
Shipment & Customs Context          → business_cross_border_shipments (new C3.5 table)
Operational Event Timestamps        → Authoritative entity created_at / approved_at timestamps
```

---

## 4. Alembic Linear Revision Chain Verification
- Frozen Head: `s6t7u8v9w0x1` (C3.4 Landed Cost Engine)
- Target Revision for C3.5: `t7u8v9w0x1y2`
- Parent Revision: `s6t7u8v9w0x1`
- Linear, non-branching chain maintained.
