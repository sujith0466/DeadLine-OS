# DEADLINEOS BUSINESS OS — B3 FINANCIAL INVARIANTS

**Document ID:** `B3-DOC-005`

**Status:** `AUTHORITATIVE FINANCIAL SPECIFICATION`

**Classification:** Financial & Arithmetic Invariant Contract

**Author:** DeadlineOS Principal Architect & Financial Systems Lead

**Date:** 2026-08-29T16:25:00+05:30



---



## 1. Primary Financial Invariants



### Invariant 1: Invoice Arithmetic & Discount Limit

$$\text{total\_amount} = \text{subtotal} + \text{tax\_amount} - \text{discount\_amount}$$

$$\text{discount\_amount} \le \text{subtotal} + \text{tax\_amount}$$

$$\text{subtotal} \ge 0, \quad \text{tax\_amount} \ge 0, \quad \text{discount\_amount} \ge 0, \quad \text{total\_amount} \ge 0$$



### Invariant 2: Settlement Balance Conservation

$$\forall \text{ Invoice } i: \quad i.\text{paid\_amount} + i.\text{balance\_due} \equiv i.\text{total\_amount}$$

$$i.\text{paid\_amount} = \sum_{a \in \text{Allocations}(i), a.\text{status} = \text{'ACTIVE'}} a.\text{allocated\_amount}$$

$$i.\text{balance\_due} = i.\text{total\_amount} - i.\text{paid\_amount}$$



### Invariant 3: Transaction Fact Immutability

Once a `BusinessTransaction` is persisted:

$$\text{amount}, \quad \text{currency}, \quad \text{transaction\_date}, \quad \text{partner\_id}, \quad \text{created\_by\_user\_id} \quad \text{are IMMUTABLE.}$$

No SQL `UPDATE` of financial fields. No SQL `DELETE` of rows. Corrections strictly executed via append-only `ADJUSTMENT` transactions with `-original.amount`.



### Invariant 4: Payment Allocation Conservation

For any `BusinessTransaction` $t$:

$$\sum_{a \in \text{Allocations}(t), a.\text{status} = \text{'ACTIVE'}} a.\text{allocated\_amount} \le t.\text{amount}$$

An allocation cannot exceed the unallocated portion of the transaction or the remaining `balance_due` of the target invoice.



### Invariant 5: Deterministic Runway Precedence

Runway Days evaluation must strictly adhere to the 5-tier precedence order:

1. `RUNWAY_NEGATIVE`: If $\text{Confirmed Cash} \le 0.00$.

2. `RUNWAY_STALE`: If last confirmed transaction or reconciliation $> 7$ calendar days ago.

3. `RUNWAY_INSUFFICIENT_HISTORY`: If operational history $< 14$ days **AND** committed payables == 0.

4. `RUNWAY_ZERO_BURN`: If $\text{Confirmed Cash} > 0.00$ **AND** $\text{ADBR}_{30} == 0.00$.

5. `CALCULATED`: $\lfloor \text{Confirmed Cash} / \text{ADBR}_{30} \rfloor$.



### Invariant 6: AI Isolation Barrier

No AI component (LLM, Vision OCR, or Speech-to-Text) may directly insert or mutate `business_invoices`, `business_transactions`, or `business_payment_allocations`. Ingestion strictly proceeds through `business_staged_extractions` with human review confirmation.