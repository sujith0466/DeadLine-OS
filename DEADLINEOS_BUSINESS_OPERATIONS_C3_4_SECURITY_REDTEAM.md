# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.4 SECURITY RED-TEAM PLAN
**Milestone:** C3.4 — Landed Cost Allocation Engine
**Mode:** Threat Modeling & Attack Surface Verification
**Date:** 2026-09-02T14:59:00+05:30
**Baseline Commit:** `6f032e4`

---

## 1. Attack Vectors & Defensive Countermeasures

| Attack Vector | Threat Scenario | Defensive Mechanism |
| :--- | :--- | :--- |
| **1. Cross-Tenant IDOR (Voucher)** | Tenant B requests or modifies Tenant A's landed cost voucher via UUID. | Query filtered by `workspace_id == g.workspace_id`. Cross-tenant lookup returns HTTP 404 `NOT_FOUND`. |
| **2. Cross-Tenant PO Reference** | Tenant A attempts to create a voucher referencing Tenant B's Purchase Order. | Service verifies `po.workspace_id == workspace_id`. Rejects with HTTP 404 / 400. |
| **3. Cross-Tenant GRN Reference** | Tenant A attempts to allocate costs to Tenant B's Goods Receipt lines. | Service verifies all lines belong to a GRN where `grn.workspace_id == workspace_id`. |
| **4. Unauthorized Voucher Creation** | `VIEWER` or unauthenticated actor creates landed cost voucher. | `@require_workspace('landed_cost:write')` rejects with HTTP 403 / 401. |
| **5. Accountant Privilege Escalation** | `ACCOUNTANT` attempts to approve voucher. | `@require_workspace('landed_cost:approve')` rejects with HTTP 403 (restricted to `OWNER`, `ADMIN`). |
| **6. Member Mutation Attempt** | `MEMBER` attempts to create or allocate landed cost voucher. | Rejects with HTTP 403. `MEMBER` has read-only access to landed cost. |
| **7. Forged Client Allocation** | Client crafts manipulated line allocations to siphon value or under-report duty. | Server ignores client-supplied allocations and recalculates allocations independently. |
| **8. Penny Siphoning / Rounding Leakage** | Division of fractional cents causes sum of allocations to not match voucher total. | Deterministic residual-cent rule assigns remainder to largest-weight line. Exact Decimal equality enforced. |
| **9. Float Precision Corruption** | Developer uses binary floating-point (`float`) arithmetic. | Prohibited by design. All amounts, rates, weights, and shares use `Decimal`. |
| **10. Missing FX Rate Bypass** | User creates voucher in foreign currency without configured exchange rate, hoping for default 1.0. | `ExchangeRateService.get_exchange_rate` strictly raises `APIError('EXCHANGE_RATE_NOT_FOUND', status=400)`. |
| **11. Silent Overwrite of Approved Voucher** | Attacker calls `PUT /landed-cost/<id>` on an already `APPROVED` voucher. | State check ensures mutations only permitted in `DRAFT`. Attempting mutation on `APPROVED` raises `VOUCHER_IMMUTABLE`. |
| **12. Double Approval Race** | Two concurrent requests attempt to approve the same voucher. | Transactional row-level lock (`with_for_update()`) verifies `status == 'ALLOCATED'` atomically before transition. |
| **13. Negative Cost Injection** | Attacker inputs negative item amounts (`-5000.00`) to artificially deflate product valuation. | Check constraint `chk_biz_lcvi_amount` (`amount > 0`) and service validation reject non-positive amounts. |
| **14. Zero Basis Allocation** | Receiving lines have zero accepted quantity or zero value, causing division by zero. | Service detects zero total basis and rejects with `ZERO_ALLOCATION_BASIS`. |
| **15. B0–B8 Accounting Contamination** | Landed cost engine inadvertently inserts rows into `business_transactions`. | Architectural firewall: C3.4 code imports zero accounting models and issues zero transaction writes. |

---

## 2. Audit Trail Guarantees

All security-sensitive lifecycle operations generate immutable `AuditEvent` records via `AuditService.log_event`:
- `LANDED_COST_VOUCHER_CREATED`
- `LANDED_COST_ITEM_ADDED`
- `LANDED_COST_ITEM_REMOVED`
- `LANDED_COST_ALLOCATED`
- `LANDED_COST_APPROVED`
- `LANDED_COST_REVERSED`

The audit trail records `actor_user_id`, `workspace_id`, `entity_id`, `before_state`, `after_state`, and user metadata.
