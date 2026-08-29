# DEADLINEOS BUSINESS OS — B6 AUTOMATION INVARIANTS
**Document ID:** `B6-DOC-004`
**Status:** `BINDING SPECIFICATION`
**Classification:** Automation Safety & Financial Integrity

---

## 1. Recurrence Stepping Rules

- **WEEKLY:** next_due = current_due + 7 days
- **BIWEEKLY:** next_due = current_due + 14 days
- **MONTHLY:** Step forward 1 month with month-end date clamping (e.g. Jan 31 -> Feb 28/29 -> Mar 31).
- **QUARTERLY:** Step forward 3 months with month-end date clamping.
- **ANNUALLY:** Step forward 1 year (handling Feb 29 leap years -> Feb 28).

---

## 2. Idempotent Execution Invariant

Unique Cycle Execution Key = (workspace_id, obligation_id, target_due_date)

If an execution record with `status = 'SUCCESS'` exists for a given cycle key, no secondary generation shall occur.
