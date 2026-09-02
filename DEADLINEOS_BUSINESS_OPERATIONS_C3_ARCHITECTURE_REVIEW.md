# DEADLINEOS BUSINESS OPERATIONS — PHASE C3 ARCHITECTURE REVIEW
# ADVANCED LOGISTICS & CROSS-BORDER SUPPLY CHAIN SPECIFICATION

**Document ID**: `C3-ARCH-001`
**Execution Timestamp**: 2026-09-02T14:12:00Z
**Authoritative Scope**: Phase C3 (Landed Cost, Batches/Serials/Expiry, Multi-Currency/FX)
**Governance Mode**: ARCHITECTURE & DESIGN ONLY (Implementation Strictly Forbidden)

---

## 1. Architectural Principles & Boundaries

The C3 architecture is governed by four immutable core principles:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     C3 ARCHITECTURAL INVARIANTS                         │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. INVENTORY QUANTITY LEDGER IS THE SOLE TRUTH:                         │
│    • Total available quantity is always SUM(IN) - SUM(OUT) from         │
│      business_stock_movements.                                          │
│    • Batches and serials attach as attribution records; they NEVER      │
│      maintain competing standalone balances.                            │
│ 2. COMMERCIAL FACTS VS FINANCIAL TRUTH:                                 │
│    • Foreign currency POs and Landed Cost Vouchers are commercial facts.│
│    • They NEVER directly write to business_transactions or invoices.   │
│    • Financial recognition flows through established AP staging gates.  │
│ 3. SOURCE FACT VS DERIVED FACT (MULTI-CURRENCY):                        │
│    • Source facts (e.g. $10,000 USD on PO) are permanently immutable.   │
│    • Base currency figures are derived using historical locked FX rates.│
│    • FX rates carry explicit provenance (source, effective date, actor).│
│ 4. DETERMINISTIC EXACT DECIMAL ARITHMETIC:                              │
│    • ZERO floating-point operations. Python Decimal & SQL NUMERIC only. │
│    • Allocation rounding residuals are deterministically assigned to    │
│      the largest component line to maintain exact penny equality.       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Landed Cost Allocation Architecture

### 2.1 Conceptual Model
Landed cost represents the total landed investment per unit of inventory:
$$\text{Landed Unit Cost} = \text{Base Purchase Cost per Unit} + \text{Allocated Landed Costs per Unit}$$

In cross-border logistics, landed costs originate from multiple external parties:
- **Ocean / Air / Road Freight**: Forwarder / Carrier.
- **Customs Import Duty & Clearance**: Customs Authority / Broker.
- **Marine / Transit Insurance**: Underwriter.
- **Port Handling & Demurrage**: Terminal Operator.

### 2.2 Landed Cost Voucher (`business_landed_cost_vouchers`)
Instead of embedding freight on the original PO, Landed Cost is captured via an independent commercial document: `BusinessLandedCostVoucher`.
- **Header**: `voucher_number`, `workspace_id`, `status` (`DRAFT`, `SUBMITTED`, `ALLOCATED`, `REVISED`), `effective_date`, `currency`, `exchange_rate`, `total_landed_cost`.
- **Reference Links**: Links to one or more `BusinessGoodsReceipt` (GRNs) being landed.
- **Cost Items (`business_landed_cost_items`)**:
  - `cost_category`: `FREIGHT`, `CUSTOMS_DUTY`, `INSURANCE`, `HANDLING`, `MISCELLANEOUS`.
  - `vendor_partner_id`: Counterparty issuing the charge.
  - `amount`: Nominal cost in invoice currency.
  - `currency`: Currency of charge.
  - `exchange_rate`: Rate to workspace base currency.
  - `base_amount`: Amount in workspace base currency (`amount * exchange_rate`).
  - `allocation_method`: Method for distributing this specific cost component.

### 2.3 Deterministic Allocation Algorithms
For a cost item with total base currency amount $C$, to be allocated across $N$ receiving lines ($i = 1 \dots N$):

#### A. Allocation By Item Value (Standard for Duties, Insurance, Taxes)
$$\text{Weight}_i = \frac{\text{Line Accepted Quantity}_i \times \text{Unit Purchase Price}_i}{\sum_{j=1}^N (\text{Line Accepted Quantity}_j \times \text{Unit Purchase Price}_j)}$$
$$\text{Raw Allocated Cost}_i = \text{round}(C \times \text{Weight}_i, 2)$$

#### B. Allocation By Quantity (Standard for Flat Handling)
$$\text{Weight}_i = \frac{\text{Line Accepted Quantity}_i}{\sum_{j=1}^N \text{Line Accepted Quantity}_j}$$
$$\text{Raw Allocated Cost}_i = \text{round}(C \times \text{Weight}_i, 2)$$

#### C. Allocation By Weight / Volume (Standard for Air/Ocean Freight)
$$\text{Weight}_i = \frac{\text{Line Total Weight}_i}{\sum_{j=1}^N \text{Line Total Weight}_j}$$
$$\text{Raw Allocated Cost}_i = \text{round}(C \times \text{Weight}_i, 2)$$

### 2.4 Exact Penny-Residual Reconciliation Algorithm
Because rounding to 2 decimal places can cause $\sum_{i=1}^N \text{Raw Allocated Cost}_i \ne C$:
$$\Delta = C - \sum_{i=1}^N \text{Raw Allocated Cost}_i$$
**Deterministic Residual Assignment**:
- If $\Delta \ne 0.00$, identify the line item $k$ with the maximum $\text{Weight}_k$.
- If there is a tie, select the line with the lowest line index $k$.
- Set $\text{Allocated Cost}_k = \text{Raw Allocated Cost}_k + \Delta$.
- **Assertion**: $\sum_{i=1}^N \text{Allocated Cost}_i \equiv C$ (exact to 0.00000000).

### 2.5 Immutability & Revision Strategy
- Once a Landed Cost Voucher is marked `ALLOCATED`, its records are **read-only and immutable**.
- If customs duty is subsequently reassessed or freight demurrage is added:
  - An append-only **Correction Voucher** (`voucher_type='SUPPLEMENTARY'` or `'REVERSAL'`) is created.
  - It references `original_voucher_id`, computes the incremental variance, and records adjustment lines.
  - Historical audit trails are never destructively overwritten.

---

## 3. Batch, Lot & Expiry Management Architecture

### 3.1 Model Structure (`business_batches`)
A batch represents a distinct production run or supplier delivery lot:
- `id`: UUID (Primary Key).
- `workspace_id`: Foreign Key (`business_workspaces.id`).
- `batch_number`: Human-readable identifier (e.g., `LOT-2026-08-A4`).
- `product_id`: Foreign Key (`business_products.id`).
- `supplier_partner_id`: Foreign Key (`business_commercial_partners.id`).
- `goods_receipt_id`: Foreign Key (`business_goods_receipts.id`).
- `manufacture_date`: Optional Date.
- `expiry_date`: Optional Date.
- `status`: `ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, `QUARANTINED`, `EXHAUSTED`.
- `quarantine_reason`: Text description if quarantined.
- `initial_quantity`: Original quantity received into this batch.

### 3.2 Attribution Invariant: Movement-Batch Linkage
To ensure that batch balances **never diverge** from the physical inventory truth:
- A new link table: `business_stock_movement_batches`.
  - `stock_movement_id`: Foreign Key (`business_stock_movements.id`).
  - `batch_id`: Foreign Key (`business_batches.id`).
  - `quantity`: Exact Decimal quantity attributed to this batch for this movement.
- **Mathematical Invariant**:
  $$\text{Available Stock for Batch } B = \sum_{\text{IN movements of } B} \text{quantity} - \sum_{\text{OUT movements of } B} \text{quantity}$$
  $$\sum_{B \in \text{Batches of Product } P} \text{Batch Available Stock}_B \equiv \text{Total Available Product Stock}_P$$
- When recording an `OUT` movement (SALE, TRANSFER_OUT, DAMAGED):
  - The sum of batch allocation quantities MUST equal the stock movement quantity.
  - If $\text{Requested Batch Quantity} > \text{Available Stock for Batch } B$, the transaction is **aborted with HTTP 400 `INSUFFICIENT_BATCH_STOCK`**.

### 3.3 Expiry Lifecycle & FEFO Policy
- **Expiry Status Evaluation**:
  - `EXPIRED`: `current_date > expiry_date`.
  - `EXPIRING_SOON`: `current_date + warning_horizon_days >= expiry_date`.
- **Policy Rule**:
  - `EXPIRED` batches are strictly blocked from normal `SALE` or `TRANSFER_IN` movements.
  - They can only be transferred to a `QUARANTINE` location or recorded as a `DAMAGED` write-off.
- **FEFO Advisory Engine**:
  - When fulfilling sales or transfers, the system deterministically sorts available batches by `expiry_date ASC, created_at ASC`.
  - The API returns suggested allocations matching FEFO order.
  - Warehouse operators can select alternative non-expired batches, provided they log an audit reason.

---

## 4. Serial Number Tracking Architecture

### 4.1 Model Structure (`business_serial_numbers`)
A serial number represents an individual discrete asset or SKU unit:
- `id`: UUID (Primary Key).
- `workspace_id`: Foreign Key (`business_workspaces.id`).
- `product_id`: Foreign Key (`business_products.id`).
- `serial_number`: Unique alphanumeric string.
- `current_location_id`: Foreign Key (`business_locations.id`).
- `status`: `IN_STOCK`, `ALLOCATED`, `SHIPPED`, `CONSUMED`, `DEFECTIVE`, `DISPOSED`.
- `batch_id`: Optional Foreign Key (`business_batches.id`).
- `originating_grn_id`: Foreign Key (`business_goods_receipts.id`).
- `last_movement_id`: Foreign Key (`business_stock_movements.id`).

### 4.2 Invariants & Constraints
1. **Workspace & Product Uniqueness**:
   - `UniqueConstraint('workspace_id', 'product_id', 'serial_number')`.
   - A serial number cannot be registered twice for the same product in a workspace.
2. **Single-Location Rule**:
   - A serial-numbered item in state `IN_STOCK` can exist in **exactly one location** at any instant in time.
3. **Movement Synchronization**:
   - For serialized products, every `BusinessStockMovement` must have an exact 1:1 set of entries in `business_stock_movement_serials`.
   - $\text{Count of Serials} \equiv \text{Movement Quantity}$.
   - For an `OUT` movement from Location $L$, each specified serial MUST currently be `status='IN_STOCK'` and `current_location_id == L`.

---

## 5. Multi-Currency & Exchange Rate Provenance Architecture

### 5.1 Source Fact vs Derived Fact Principle
```
┌─────────────────────────────────────────┐      ┌─────────────────────────────────────────┐
│           SOURCE FACT (IMMUTABLE)       │      │        DERIVED FACT (HISTORICAL)        │
├─────────────────────────────────────────┤      ├─────────────────────────────────────────┤
│ • PO-2026-089 issued in USD             │      │ • Exchange Rate applied: 84.500000      │
│ • Total Amount: $10,000.00 USD          │ ───► │ • Rate Provenance: RBI_CUSTOMS_DAILY    │
│ • Commercial Partner: Shenzhen Micro    │      │ • Effective Date: 2026-08-15            │
│ • Payment Terms: NET_60 USD             │      │ • Derived Base Valuation: ₹845,000.00   │
└─────────────────────────────────────────┘      └─────────────────────────────────────────┘
```
- The foreign currency values are the immutable contractual facts.
- The base currency value is derived at point of commitment and locked with the document.
- Subsequent changes in today's FX rate never alter the historical reporting value.

### 5.2 Exchange Rate Registry (`business_exchange_rates`)
- `id`: UUID.
- `workspace_id`: Foreign Key.
- `from_currency`: ISO-4217 code (e.g., `USD`, `EUR`, `GBP`, `CNY`).
- `to_currency`: Workspace base currency (e.g., `INR`).
- `rate`: `Numeric(18, 6)`. Amount of base currency per 1 unit of foreign currency.
- `effective_date`: Date.
- `rate_source`: `SYSTEM_DEFAULT`, `CENTRAL_BANK`, `CUSTOMS_RATE`, `MANUAL_OVERRIDE`.
- `created_by_user_id`: Foreign Key (`users.id`).
- **Constraint**: `UniqueConstraint('workspace_id', 'from_currency', 'to_currency', 'effective_date')`.

### 5.3 Missing Rate & Rounding Policy
- If no rate exists for `effective_date`, the system looks up the most recent available rate within a 7-day lookback window.
- If no rate exists, the transaction **cannot be committed** without explicit user entry of a rate (`MANUAL_OVERRIDE`).
- Silent fallback to `1.0` is strictly forbidden.

---

## 6. Security, RBAC & Multi-Tenant Boundaries

### 6.1 Strict 5-Tier RBAC Authorization Matrix
| Capability | OWNER | ADMIN | MEMBER | ACCOUNTANT | VIEWER |
| :--- | :---: | :---: | :---: | :---: | :---: |
| View Logistics, Batches & Landed Costs | Allowed | Allowed | Allowed | Allowed | Allowed |
| Receive Goods with Batches & Serials | Allowed | Allowed | Allowed | Denied (403) | Denied (403) |
| Create Landed Cost Voucher | Allowed | Allowed | Denied (403) | Allowed | Denied (403) |
| Approve & Allocate Landed Cost | Allowed | Allowed | Denied (403) | Denied (403) | Denied (403) |
| Manage Exchange Rates & Overrides | Allowed | Allowed | Denied (403) | Allowed | Denied (403) |
| Quarantine / Release Expired Stock | Allowed | Allowed | Denied (403) | Denied (403) | Denied (403) |

*Rule Check: The role `MANAGER` is never introduced. All checks are server-side.*

### 6.2 Multi-Tenant Isolation
- All tables contain `workspace_id` indexed and validated on every query.
- IDOR attacks attempting to link a Batch from Workspace A to a PO in Workspace B are rejected with HTTP 404/403.
