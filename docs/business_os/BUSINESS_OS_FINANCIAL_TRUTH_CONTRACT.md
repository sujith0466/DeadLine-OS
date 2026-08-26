# DEADLINEOS BUSINESS OS — FINANCIAL TRUTH CONTRACT
**Document ID:** `B0-DOC-020`
**Status:** `B0 ARCHITECTURAL CONTRACT`
**Classification:** Core Financial Integrity Specification
**Author:** DeadlineOS Architecture Group

---

## 1. Scope & Nature of the Financial System
1. **Operational Financial Event Ledger (Not an ERP / General Ledger):**
   - Business OS does **NOT** maintain a double-entry chart of accounts (no journal debits/credits or statutory balance sheets).
   - Business OS implements an **Append-Only Operational Event Ledger** centered around commercial commitments (`Invoice`), settled movements of money (`BusinessTransaction`), and contractual settlement links (`PaymentAllocation`).
2. **Authoritative Financial Hierarchy:**

$$\text{Authoritative Facts} \longrightarrow \text{Settlement Allocations} \longrightarrow \text{Derived Balances} \longrightarrow \text{Cash Runway Projections}$$

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. AUTHORITATIVE FACTS (Immutable Historical Facts)                         │
│    - `business_transactions`: Inbound/outbound money movements              │
│    - `business_payment_allocations`: Settlement links (Tx $\rightarrow$ Inv)│
│    - `business_audit_events`: Permanent forensic event records              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. COMMERCIAL COMMITMENTS (Contractual State)                               │
│    - `business_invoices`: Issued receivable or payable contracts            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. DERIVED SETTLEMENT STATE (Deterministic Cached Views)                    │
│    - `invoice.paid_amount` = $\sum \text{Allocations}$                      │
│    - `invoice.balance_due` = $\text{total\_amount} - \text{paid\_amount}$   │
│    - `invoice.status` = Derived from balance and due date                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. CASH PROJECTION STATE (Forward-Looking Intelligence)                     │
│    - `Confirmed Cash` = $\sum \text{Settled Non-Reversed Transactions}$     │
│    - `Committed Inflows` = $\sum \text{Unsettled Inbound Invoices in Window}$│
│    - `Committed Outflows` = $\sum \text{Unsettled Outbound Invoices in Window}$│
│    - `Projected Position` = $\text{Confirmed} + \text{Inflows} - \text{Outflows}$│
│    - `Runway Days` = Deterministic formula ($\lfloor\text{Confirmed Cash} / \text{ADBR}_{30}\rfloor$)│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Invariant: Invoice Settlement Balance Match & Arithmetic Invariants

### 2.1 Settlement Balance Invariant
$$\forall \text{ Invoice } i: \quad i.\text{paid\_amount} + i.\text{balance\_due} \equiv i.\text{total\_amount}$$

Where:
$$i.\text{paid\_amount} \equiv \sum_{a \in \text{Allocations}(i), a.\text{status} = \text{'ACTIVE'}} a.\text{allocated\_amount}$$
$$i.\text{total\_amount} \equiv i.\text{subtotal} + i.\text{tax\_amount} - i.\text{discount\_amount}$$

### 2.2 Multi-Layer Enforcement Boundaries
1. **API Ingestion:** Schema rejects negative numbers and invalid discount ranges.
2. **Domain Service:** `InvoiceService.calculate_totals()` enforces exact Python `Decimal` arithmetic.
3. **Database Constraints:** `CHECK (subtotal >= 0 AND tax_amount >= 0 AND discount_amount >= 0 AND total_amount >= 0 AND discount_amount <= (subtotal + tax_amount))`.
4. **Issuance Freeze:** When `status = 'ISSUED'`, `subtotal`, `tax_amount`, `discount_amount`, and `total_amount` become immutable.

---

## 3. Transaction Immutability Contract

### 3.1 Immutable Financial Facts vs. Lifecycle Status
- **Strictly Immutable Historical Facts:** Columns `amount`, `currency`, `transaction_date`, `partner_id`, `created_by_user_id`, `created_at`, `payment_method`, and `reference_number` can **NEVER** be altered, overwritten, or deleted.
- **Controlled Lifecycle Metadata:** The `status` column may transition from `CONFIRMED` to `REVERSED` strictly through the formal reversal protocol.
- **Prohibition on Destructive Deletes:** No SQL `DELETE` operation is permitted on `business_transactions`.

### 3.2 Formal Reversal Protocol
When an authorized user (`OWNER` or `ADMIN`) reverses a transaction:
1. System validates that the caller has `transaction:reverse` permission and provided a non-empty `reason` string.
2. System inserts a counter-adjustment row into `business_transactions`:
   - `transaction_type = 'ADJUSTMENT'`
   - `amount = -original.amount`
   - `currency = original.currency`
   - `reversal_of_transaction_id = original.id`
   - `status = 'CONFIRMED'`
3. System transitions `original.status = 'REVERSED'`.
4. System transitions linked `business_payment_allocations.status = 'REVERSED'`.
5. System triggers `recalculate_invoice_balance(invoice_id)` to restore the invoice's `balance_due`.
6. System writes an immutable `business_audit_events` row with before/after state diff, actor ID, IP address, and reversal reason.

---

## 4. Deterministic Runway Days Precedence Order

$$\text{Runway Days} = \left\lfloor \frac{\text{Confirmed Cash}}{\text{ADBR}_{30}} \right\rfloor \quad \left(\text{where } \text{ADBR}_{30} = \frac{\sum \text{Expenses}_{[-30,0]} + \sum \text{Payables}_{[0,+30]}}{60}\right)$$

### Precedence Evaluation Table
1. **Priority 1 (`RUNWAY_NEGATIVE`):** Triggered if $\text{Confirmed Cash} \le 0.00$.
2. **Priority 2 (`RUNWAY_STALE`):** Triggered if last confirmed transaction or reconciliation $> 7$ calendar days ago.
3. **Priority 3 (`RUNWAY_INSUFFICIENT_HISTORY`):** Triggered if operational history $< 14$ days **AND** committed payables == 0.
4. **Priority 4 (`RUNWAY_ZERO_BURN`):** Triggered if $\text{Confirmed Cash} > 0.00$ **AND** $\text{ADBR}_{30} == 0.00$.
5. **Priority 5 (`CALCULATED`):** Evaluates normal numeric integer days.
