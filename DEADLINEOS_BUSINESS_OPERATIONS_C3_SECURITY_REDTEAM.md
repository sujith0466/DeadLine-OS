# DEADLINEOS BUSINESS OPERATIONS — PHASE C3 SECURITY & RED TEAM AUDIT
# ADVANCED LOGISTICS & CROSS-BORDER THREAT MODEL

**Document ID**: `C3-SEC-001`
**Execution Timestamp**: 2026-09-02T14:16:00Z
**Role**: Independent Principal Security Architect / Red Team Lead
**Governance Mode**: THREAT MODELING & AUDIT ONLY

---

## 1. Threat Model & Attack Surface Overview

Phase C3 introduces multi-currency conversions, complex cost allocation formulas, physical batch/lot expiration tracking, and individual serial number custody. This expands the attack surface across:
1. **Financial Valuation Integrity**: Manipulating FX rates or landed cost allocations to understate customs duty, inflate inventory assets, or distort tax liabilities.
2. **Physical Asset Tracking & Custody**: Replaying serial numbers, creating phantom serials, duplicate batch assignments, or bypassing expiry bans.
3. **Multi-Tenant Boundary**: Attempting to allocate costs from Tenant B's invoices to Tenant A's products, or reading international supplier pricing across workspaces.
4. **Trust Boundary Bypass**: Attempting to commit unverified OCR/voice logistics proposals directly into physical stock movements or financial books.

---

## 2. Red Team Threat Scenarios & Mitigations

### Threat 1: Cross-Tenant Landed Cost Cross-Contamination (IDOR)
- **Severity**: CRITICAL
- **Attack Path**: Attacker in Workspace A submits a `LandedCostVoucher` referencing a `goods_receipt_id` or `purchase_order_id` belonging to Workspace B. If the backend fails to validate `workspace_id` on every referenced line item, Workspace A could siphon or pollute inventory valuations of Workspace B.
- **Mitigation**:
  - The repository service enforces composite foreign key checks:
    `BusinessGoodsReceipt.query.filter_by(id=grn_id, workspace_id=actor_workspace_id).first_or_404()`.
  - Database schema enforces multi-tenant foreign keys and indexes.
- **Test Required**: Automated test in `test_business_landed_cost_security.py` where Tenant A attempts to allocate costs to Tenant B's GRN lines $\rightarrow$ Assert HTTP 404 / 403.

### Threat 2: Serial Number Duplication & Ghost Unit Creation
- **Severity**: HIGH
- **Attack Path**: Attacker submits concurrent receiving requests for the same serial number (e.g. `SN-109283`) or attempts to receive a serial number that was already registered in another location.
- **Mitigation**:
  - Database unique constraint: `UniqueConstraint('workspace_id', 'product_id', 'serial_number')`.
  - Database transaction isolation with row-level locks or pre-flight query checking `current_location_id` and `status != 'IN_STOCK'`.
  - A serial can only transition to `IN_STOCK` if it does not already exist in `IN_STOCK` state anywhere in the workspace.
- **Test Required**: Test receiving duplicate serial numbers concurrently $\rightarrow$ assert second transaction rejected with HTTP 409 / 400.

### Threat 3: Batch Quantity Inflation & Ledger Divergence
- **Severity**: CRITICAL
- **Attack Path**: Attacker attempts to update a batch's remaining balance directly, or dispatches 100 units from a batch that only has 40 units remaining in stock movements.
- **Mitigation**:
  - The batch balance is **never stored as a mutable balance column**. It is computed dynamically from `business_stock_movement_batches` and validated against `business_stock_movements`.
  - In `InventoryService.record_stock_movement`, for any movement with batch attribution:
    $$\text{sum(batch\_quantities)} \equiv \text{movement.quantity}$$
    $$\text{requested\_batch\_qty} \le \text{available\_batch\_qty}$$
  - Transaction rolls back if requested batch quantity exceeds available batch quantity.
- **Test Required**: Attempt to issue 50 units from a batch with 20 units available $\rightarrow$ assert HTTP 400 `INSUFFICIENT_BATCH_STOCK`.

### Threat 4: Expired Inventory Release Bypass
- **Severity**: HIGH
- **Attack Path**: Attacker attempts to fulfill a customer sales order using an expired batch (`current_date > expiry_date`) to clear damaged or toxic stock without reporting a write-off.
- **Mitigation**:
  - Server-side validation strictly blocks any `SALE` or `TRANSFER_OUT` movement for batches where `current_date > expiry_date` or `status == 'QUARANTINED'`.
  - Expired batches can ONLY be selected for `DAMAGED` write-offs or transfer to a dedicated `QUARANTINE` location type.
- **Test Required**: Attempt `SALE` movement with expired batch $\rightarrow$ assert HTTP 400 `BATCH_EXPIRED`.

### Threat 5: Exchange Rate Arbitrage & Historical FX Tampering
- **Severity**: HIGH
- **Attack Path**: Attacker modifies the exchange rate of a historical PO or landed cost voucher after commitment, altering reported costs and margins retroactively.
- **Mitigation**:
  - Documents lock their applied `exchange_rate` at moment of approval/commitment in immutable columns.
  - `business_exchange_rates` records maintain full audit provenance (`created_by_user_id`, `created_at`, `rate_source`).
  - Historical rate lookups are date-pinned and never mutate already-committed documents.
- **Test Required**: Modify today's exchange rate in registry $\rightarrow$ query historical PO valuation $\rightarrow$ assert reporting value remains exactly identical.

### Threat 6: Floating-Point Penny Siphoning in Cost Allocation
- **Severity**: MEDIUM
- **Attack Path**: Attacker exploits float rounding errors to generate fractional currency discrepancies across thousands of SKU line items.
- **Mitigation**:
  - All calculations enforce Python `Decimal` and SQL `NUMERIC(15, 2)` / `NUMERIC(18, 6)`.
  - Deterministic penny-residual allocation algorithm assigns remainder cents to the largest line item so that $\sum \text{allocated} \equiv \text{voucher total}$.
- **Test Required**: Allocate ₹100.00 across 3 identical line items $\rightarrow$ verify line amounts are [33.34, 33.33, 33.33], sum is exactly 100.00.

### Threat 7: RBAC Privilege Escalation (Non-Admin Approval)
- **Severity**: HIGH
- **Attack Path**: User with `MEMBER` or `ACCOUNTANT` role attempts to approve a `BusinessLandedCostVoucher` or release a quarantined batch.
- **Mitigation**:
  - Server-side decorator `@require_workspace('landed_cost:approve')` strictly restricted to `OWNER` and `ADMIN`.
  - Attempt by `MEMBER`, `ACCOUNTANT`, or `VIEWER` rejected with HTTP 403 Forbidden.
- **Test Required**: Submit approve endpoint using `MEMBER` credentials $\rightarrow$ assert HTTP 403.
