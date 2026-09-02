# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.5 ARCHITECTURE REVIEW
**Milestone:** C3.5 — Cross-Border Supply Chain Operations Hub & Copilot Grounding
**Mode:** Architecture & Semantic Specification
**Date:** 2026-09-02T15:12:30+05:30
**Baseline Commit:** `d849c0d`

---

## 1. Cross-Border Operations Hub Architecture

The **Cross-Border Supply Chain Operations Hub** acts as an operational composition layer. It aggregates and cross-correlates disparate procurement, logistics, receiving, inventory, valuation, and provenance entities into a unified operational context:

```
Supplier (CommercialPartner)
       │
       ▼
Purchase Order (BusinessPurchaseOrder)
       │
       ├─────────────────────────────────────────────────┐
       ▼                                                 ▼
Shipment & Customs (BusinessCrossBorderShipment)   Goods Receipt (BusinessGoodsReceipt)
       │                                                 │
       ▼                                                 ▼
Port & Transit Status                             Stock Movements (Sole Qty Truth)
       │                                                 │
       ├─────────────────────────────────────────────────┼──────────────────┐
       ▼                                                 ▼                  ▼
Landed Cost Voucher & Allocation                  Batches (C3.2)     Serials (C3.3)
(business_landed_cost_allocations)               (business_batches) (business_serial_numbers)
```

### Shipment Lifecycle State Machine
States:
- `PLANNED`: Initial logistics planning, PO linked, carrier not booked.
- `BOOKED`: Carrier confirmed, Bill of Lading assigned, estimated dates set.
- `IN_TRANSIT`: Shipment departed origin port/country, en route.
- `CUSTOMS_HOLD`: Arrived at port of entry, subject to customs inspection or duty assessment.
- `CUSTOMS_CLEARED`: Formal customs clearance granted, duties paid/assessed.
- `DELIVERED`: Goods delivered to destination warehouse and GRN created.
- `CANCELLED`: Shipment aborted prior to delivery.

### Customs Clearance State Machine
States:
- `PENDING`: Customs paperwork not yet lodged.
- `SUBMITTED`: Import declaration filed with customs authority.
- `INSPECTION`: Physical examination, document audit, or tariff evaluation.
- `CLEARED`: Unconditional release granted.
- `REJECTED`: Import denied or detained.

---

## 2. Copilot Grounding & Semantic Contract Architecture

### The Four-Pillar Semantic Separation
To prevent LLM hallucination, confabulation, or misinterpretation of operational guidance, every Copilot response must cleanly categorize output into four explicit tiers:

1. **FACTS (`facts`)**:
   - Strictly grounded, immutable truths directly read from the database.
   - Examples: "Current on-hand inventory of SKU-101 is 45 units.", "Landed cost allocated to PO-901 is ₹12,500.00.", "1 USD was converted at 86.250000 INR on 2026-09-01."
2. **SIGNALS (`signals`)**:
   - Deterministic indicators computed by rules engines from authoritative data.
   - Examples: "Shipment SHP-2026-001 has been in CUSTOMS_HOLD for 4 days.", "Batch B-90 expires in 12 days.", "PO-104 is 3 days past its expected delivery date."
3. **FORECASTS (`forecasts`)**:
   - Statistical or model-driven projections of future state with explicit uncertainty.
   - Examples: "Projected stockout date for SKU-101 is 2026-09-18 based on 30-day velocity.", "Projected cash balance at month-end is ₹420,000.00."
4. **RECOMMENDATIONS (`recommendations`)**:
   - Proposed human operational actions requiring executive or managerial judgment.
   - Examples: "Follow up with customs broker regarding declaration DOC-881.", "Initiate reorder for 20 units of SKU-101."
5. **INSUFFICIENT_DATA (`insufficient_data`)**:
   - When required records (e.g. historical sales, exchange rates, shipping documents) do not exist, the Copilot **MUST NOT** estimate, guess, or synthesize. It must explicitly declare `INSUFFICIENT_DATA`.

---

## 3. Deterministic Query Dispatch

Where users ask precise factual questions, the Copilot engine intercepts the query and runs deterministic database queries rather than delegating arithmetic to LLM generation:
- Stock on hand $\rightarrow$ `InventoryService.get_stock_summary(workspace_id, product_id)`
- Landed cost $\rightarrow$ `LandedCostService.get_voucher(...)` / `BusinessLandedCostAllocation`
- Serial units $\rightarrow$ `SerialService.list_serials(...)`
- Batch expiry $\rightarrow$ `BatchService.list_batches(...)`
- In-transit shipments $\rightarrow$ `CrossBorderHubService.list_shipments(status='IN_TRANSIT')`

---

## 4. AI Action Safety & Human-in-the-Loop Staging

AI cannot perform direct database mutations. Any AI-suggested mutation follows the established governance pipeline:
```
Natural Language Prompt
       │
       ▼
AI Action Identification
       │
       ▼
Structured Proposal (with parameters)
       │
       ▼
Persistence to `business_staged_extractions` (Status: NEEDS_REVIEW)
       │
       ▼
Human User Review & Approval (UI / API)
       │
       ▼
Authorized Service Execution + Audit Trail
```
Zero direct mutation is permitted.
