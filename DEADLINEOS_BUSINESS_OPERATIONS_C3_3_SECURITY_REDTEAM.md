# DEADLINEOS BUSINESS OPERATIONS — MILESTONE C3.3 SECURITY RED TEAM
# THREAT MODEL & IDOR DEFENSE SPECIFICATION

**Document ID**: `C3-3-SEC-001`
**Milestone**: Phase C3.3 (Serial Number Tracking & Unit-Level Provenance)
**Status**: APPROVED & ACTIVE

---

## 1. Threat Vectors & Attack Scenarios

| Attack ID | Vector / Threat | Target Boundary | Mitigation & Defense Mechanism |
| :--- | :--- | :--- | :--- |
| **THREAT-01** | Cross-Tenant Serial Lookup (IDOR) | Tenant boundary | Filter all queries by `workspace_id == g.workspace_id`. Cross-tenant lookup returns HTTP 404 `SERIAL_NOT_FOUND`. |
| **THREAT-02** | Cross-Tenant Serial Mutation | Tenant boundary | Mutation queries verify row ownership before updating; returns HTTP 404. |
| **THREAT-03** | Serial Duplication Attack | Data integrity | Unique DB constraint on `(workspace_id, product_id, serial_number)`. Attempted duplicate returns HTTP 400 `DUPLICATE_SERIAL`. |
| **THREAT-04** | Serial Reuse Across Different Products | Data integrity | Permitted across products (if manufacturer numbers overlap), but uniquely keyed to product. Cross-product dispatch rejected. |
| **THREAT-05** | Double-Dispatch / Race Condition | Financial & Inventory Ledger | Row-level locking (`with_for_update()`) during dispatch; status checked atomically within transaction. |
| **THREAT-06** | Dispatch of Non-Existent Serial | Inventory integrity | Checked prior to movement; rejects with HTTP 404 `SERIAL_NOT_FOUND`. |
| **THREAT-07** | Dispatch of Non-Stock Serial (`SHIPPED`/`DEFECTIVE`) | Inventory integrity | State machine strictly enforces `status in ('IN_STOCK', 'ALLOCATED')`; rejects with HTTP 400 `SERIAL_NOT_AVAILABLE`. |
| **THREAT-08** | Batch-Serial Mismatch | Provenance integrity | If movement specifies batch attribution, serial's `batch_id` must match. Rejects with HTTP 400 `BATCH_SERIAL_MISMATCH`. |
| **THREAT-09** | Movement Quantity vs Serial Count Mismatch | Mathematical ledger invariant | Total count of serials attributed must exactly equal `int(movement.quantity)`. Rejects with HTTP 400 `SERIAL_COUNT_MISMATCH`. |
| **THREAT-10** | Lifecycle Transition Bypass | Governance & State Machine | Only allowed transitions defined in transition matrix succeed. Invalid jumps reject with HTTP 400 `INVALID_LIFECYCLE_TRANSITION`. |
| **THREAT-11** | Privilege Escalation (Viewer Mutation) | RBAC 5-Tier Boundary | `serial:write` enforced server-side. `VIEWER` and `ACCOUNTANT` rejected with HTTP 403 `FORBIDDEN`. |
| **THREAT-12** | Unauthorized Disposal / Quarantine | RBAC 5-Tier Boundary | `serial:quarantine` restricted strictly to `OWNER` and `ADMIN`. `MEMBER` rejected with HTTP 403 `FORBIDDEN`. |
| **THREAT-13** | Forged Workspace Header | Tenant boundary | `g.workspace_id` resolved exclusively from verified JWT membership context; client headers cannot override. |
| **THREAT-14** | Partial Transaction Ledger Desynchronization | Atomicity | All serial attributions, lifecycle updates, and stock movements committed within a single database transaction. Rollback on failure. |

---

## 2. Concurrency Safety Proof

To prevent double-dispatch in concurrent execution environments:
```python
# Atomic row-lock acquisition
serials = BusinessSerialNumber.query.filter(
    BusinessSerialNumber.workspace_id == workspace_id,
    BusinessSerialNumber.product_id == movement.product_id,
    BusinessSerialNumber.serial_number.in_(serial_numbers)
).with_for_update().all()

for s in serials:
    if s.status not in ('IN_STOCK', 'ALLOCATED'):
        raise APIError(
            f"Serial '{s.serial_number}' is not available for dispatch (Current status: {s.status}).",
            code="SERIAL_NOT_AVAILABLE",
            status=400
        )
```
Any competing transaction attempting to acquire the same serials blocks until the first transaction commits, after which the second transaction reads the updated `SHIPPED` status and immediately aborts.
