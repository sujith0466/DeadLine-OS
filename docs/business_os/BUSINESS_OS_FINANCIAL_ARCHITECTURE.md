# DEADLINEOS BUSINESS OS — FINANCIAL ARCHITECTURE
**Document ID:** `B0-DOC-004`
**Status:** `B0 ARCHITECTURAL SPECIFICATION`
**Classification:** Financial & Arithmetic Architecture

---

## 1. The Cash Truth Model
In small businesses, "Bank Balance" is often misleading. Business OS introduces a four-tier **Cash Reality Hierarchy**:

$$\text{Projected Runway Position} = \text{Confirmed Cash} + \sum \text{Committed Inflows} - \sum \text{Committed Outflows}$$

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CONFIRMED CASH (Authoritative In-Hand / In-Bank)                         │
│    - Sum of all verified, settled BusinessTransactions                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. COMMITTED INFLOWS (Receivables due within window W)                      │
│    - Invoices with status ISSUED / PARTIALLY_PAID                           │
│    - Represents contractual claims, NOT cash in hand                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. COMMITTED OUTFLOWS (Payables & Obligations due within window W)          │
│    - Invoices payable, statutory dues, recurring supplier payments          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. PROJECTED CASH POSITION (Deterministic Runway Forecast)                  │
│    - Never presented as "money you have"; strictly tagged as "Projected"    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Deterministic Runway Days Contract & Precedence

$$\text{PROJECTED CASH POSITION} \ne \text{RUNWAY DAYS}$$

Runway Days measures how long current confirmed cash will sustain operations without new sales, based on verified burn rate.

### 2.1 Average Daily Burn Rate ($\text{ADBR}_W$)
The standard baseline observation window $W = 30$ calendar days.

$$\text{ADBR}_{30} = \frac{\sum_{t \in \text{Settled Expenses}_{[-30, 0]}} t.\text{amount} + \sum_{p \in \text{Committed Payables}_{[0, +30]}} p.\text{balance\_due}}{60\text{ days}}$$

### 2.2 Deterministic Runway State Precedence Order

When evaluating Runway Days, conditions are evaluated strictly in the following precedence order:

| Precedence | Condition | Evaluated State | UI Representation & Behavioral Action |
|:---:|---|---|---|
| **Priority 1** | $\text{Confirmed Cash} \le 0.00$ | `RUNWAY_NEGATIVE` | Warning Alert: *"Zero or negative cash balance. Immediate capital injection required."* |
| **Priority 2** | Last confirmed transaction or reconciliation $> 7$ calendar days ago | `RUNWAY_STALE` | Warning Badge: *"Stale Data — Reconcile Bank Balance to View Runway."* |
| **Priority 3** | Workspace operational age $< 14$ days **AND** $\sum \text{Committed Payables} = 0.00$ | `RUNWAY_INSUFFICIENT_HISTORY` | Info Badge: *"Runway calculating (requires 14 days of operational history)."* |
| **Priority 4** | $\text{Confirmed Cash} > 0.00$ **AND** $\text{ADBR}_{30} = 0.00$ | `RUNWAY_ZERO_BURN` | Status Badge: *"Zero burn rate detected (no active expenses or payables)."* |
| **Priority 5** | $\text{Confirmed Cash} > 0.00$ **AND** $\text{ADBR}_{30} > 0.00$ | `CALCULATED` | Numeric Display: `⌊Confirmed Cash / ADBR_30⌋ Days` |

### 2.3 Prohibition on Hallucination
An LLM is **STRICTLY PROHIBITED** from estimating, synthesizing, or calculating Runway Days. The value must be produced by deterministic backend arithmetic.

---

## 3. Invoice Calculation, Discount Model & Multi-Layer Enforcement

### 3.1 Authoritative Total Formula
$$\text{total\_amount} = \text{subtotal} + \text{tax\_amount} - \text{discount\_amount}$$

### 3.2 Multi-Layer Enforcement Contract
The arithmetic invariant is enforced across four distinct architectural boundaries:
1. **API Validation Layer:** Request schema validates that `subtotal >= 0`, `tax_amount >= 0`, `discount_amount >= 0`, and `discount_amount <= subtotal + tax_amount`.
2. **Service Domain Layer:** `InvoiceService.calculate_totals()` executes exact Python `Decimal` arithmetic and asserts $\text{total\_amount} \ge 0.00$.
3. **Database Layer:** Table constraint:
   ```sql
   CONSTRAINT chk_biz_inv_math CHECK (
       subtotal >= 0 AND
       tax_amount >= 0 AND
       discount_amount >= 0 AND
       total_amount >= 0 AND
       discount_amount <= (subtotal + tax_amount)
   )
   ```
4. **Issuance Freeze Layer:** When an invoice transitions to `status = 'ISSUED'`, columns `subtotal`, `tax_amount`, `discount_amount`, and `total_amount` become **IMMUTABLE**. Modifications require creating an explicit credit note or cancellation adjustment.

---

## 4. Monetary Data Types & Representation
- **PostgreSQL Storage:** `NUMERIC(15, 2)`.
- **Backend Processing:** Python standard `decimal.Decimal` with explicit rounding context `ROUND_HALF_UP`.
- **JSON Serialization:** Serialized as **Strings** (e.g. `"amount": "15420.50"`) to prevent floating-point loss in JavaScript/V8 engines.
- **Frontend Client Type:** Displayed using localized Intl formatting, manipulated with `big.js` / integer cents for math.
