# DEADLINEOS BUSINESS OS — B6 RECURRING OBLIGATIONS CONTRACT
**Document ID:** `B6-DOC-005`
**Status:** `BINDING SPECIFICATION`
**Classification:** Recurring Domain Specification

---

## 1. Obligation Types & Schema

1. **`RECEIVABLE`:** Recurring client retainers / subscriptions. Generates `RECEIVABLE` invoices.
2. **`PAYABLE`:** Recurring vendor bills, office rent, SaaS subscriptions. Generates `PAYABLE` invoices.
3. **`TAX_COMPLIANCE`:** Statutory deadlines (GST returns, TDS deposit, advance income tax).
4. **`PAYROLL`:** Monthly staff salary disbursement obligations.

---

## 2. State Transitions

ACTIVE <-> PAUSED -> COMPLETED
ACTIVE | PAUSED -> CANCELLED
