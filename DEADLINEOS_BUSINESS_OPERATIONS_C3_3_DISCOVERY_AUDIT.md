# DEADLINEOS BUSINESS OPERATIONS — MILESTONE C3.3 DISCOVERY AUDIT
# SERIAL NUMBER TRACKING & UNIT-LEVEL PROVENANCE

**Document ID**: `C3-3-AUDIT-001`
**Milestone**: Phase C3.3 (Serial Number Tracking & Unit-Level Provenance)
**Baseline Revision**: `14e850d` (`release: freeze DeadlineOS Business Operations C3.2`)
**Alembic Baseline Head**: `q4r5s6t7u8v9`
**Timestamp**: 2026-09-02T14:41:00Z
**Status**: APPROVED & AUDITED

---

## 1. Executive Baseline & Current State Audit

Phase C3.2 established authoritative batch, lot, and expiry management:
- `business_batches`: Authoritative batch master registry with workspace scoping, product linking, expiry dates, and quarantine states.
- `business_stock_movement_batches`: Movement attribution linking stock movements to batches with strict mathematical quantity equality (`SUM(batch attributions) == movement.quantity`).
- Dynamic stock calculation: `SUM(IN) - SUM(OUT)` derived from `business_stock_movements`.
- 359 tests passed at 100%, 0 TypeScript errors, clean Git tree at commit `14e850d`.

### Current State Analysis for Serial Number Tracking
1. **Product Catalog (`business_products`)**:
   - Products currently have SKU, name, unit, cost price, selling price, currency, reorder level, and status.
   - Products do not currently declare an explicit serialization mode.
   - **Requirement**: Extend `BusinessProduct` with `is_serialized = Column(Boolean, default=False, nullable=False)` to enable unit-level serial enforcement for designated items while maintaining 100% backward compatibility for all existing items.
2. **Authoritative Movement Ledger (`business_stock_movements`)**:
   - Remains the SOLE operational inventory quantity truth (`SUM(IN) - SUM(OUT)`).
   - Serial records must NEVER become a competing quantity ledger.
   - For serialized products, every movement must be accompanied by concrete serial attributions where:
     $$\text{Count}(\text{serial attributions}) = \text{movement.quantity}$$
   - Quantities for serialized movements must be strictly positive whole numbers (`quantity % 1 == 0`).
3. **Goods Receiving (`GoodsReceiptService`)**:
   - Currently accepts `batch_number`, `expiry_date`, and `manufacture_date` on goods receipt lines.
   - Must be extended to accept `serial_numbers: List[str]` on goods receipt lines.
   - Enforces atomic invariant: `len(serial_numbers) == int(accepted_quantity)`.
4. **Location Invariant**:
   - A physical serialized item cannot exist in multiple locations simultaneously.
   - When in stock, a serial has exactly one `current_location_id`.
   - When dispatched (`SHIPPED`, `CONSUMED`, `DEFECTIVE`, `DISPOSED`), `current_location_id` is atomically cleared or updated to reflect the transition.
5. **Batch Integration**:
   - A serial number optionally belongs to a `batch_id`.
   - When both batch and serial tracking apply to an inventory movement, serials must belong to the attributed batch.
6. **5-Tier RBAC & Tenant Isolation**:
   - `serial:read`: `OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`.
   - `serial:write`: `OWNER`, `ADMIN`, `MEMBER`.
   - `serial:quarantine` / defect / dispose: `OWNER`, `ADMIN`.
   - Row-level workspace isolation: `workspace_id` must match authenticated session on every query.

---

## 2. Invariant Checklist

| Invariant | Description | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Quantity Ledger Primacy** | `business_stock_movements` is the sole source of quantity truth | Serial state is provenance only; no mutable unit counters |
| **Serial Uniqueness** | Unique per workspace and product | `UniqueConstraint('workspace_id', 'product_id', 'serial_number')` |
| **Exact Count Equality** | Serial count must exactly equal movement quantity | `len(serials) == int(movement.quantity)` |
| **Single-Location Invariant** | One unit can only be in one physical location | `current_location_id` updated atomically on movement |
| **Double-Dispatch Prevention** | A serial cannot be dispatched more than once from stock | Status checked & locked (`with_for_update`) during dispatch |
| **Tenant Isolation** | Workspace boundary cannot be breached | All queries filtered by `workspace_id`, IDOR tested |
| **Batch Consistency** | Serial's batch must match movement batch attribution | Validated during attribution linking |
| **Audit Immutability** | All lifecycle state changes logged | `AuditService.log_event` invoked on each transition |

---

## 3. Discovery Audit Conclusion

The existing architecture provides a clean, modular foundation for unit-level serial number tracking without modifying frozen financial boundaries or creating competing inventory ledgers. C3.3 will integrate seamlessly into `InventoryService`, `GoodsReceiptService`, and `AuditEvent` systems.
