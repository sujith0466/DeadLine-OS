# DEADLINEOS BUSINESS OPERATIONS — MILESTONE C3.3 TEST STRATEGY
# SERIAL NUMBER TRACKING & UNIT-LEVEL PROVENANCE

**Document ID**: `C3-3-TEST-001`
**Milestone**: Phase C3.3 (Serial Number Tracking & Unit-Level Provenance)
**Status**: APPROVED

---

## 1. Test Levels & Coverage Framework

```
Level 1: Unit & Domain Service Tests (backend/tests/test_business_serials.py)
Level 2: Migration Integrity Verification (backend/tests/test_migration_chain_verification.py)
Level 3: Live Neon PostgreSQL E2E Suite (scratch/e2e_c3_3_live.py)
Level 4: Full Backend Regression Suite (pytest tests/ -k "not test_gemini")
Level 5: Frontend Production Build & TypeScript Verification (npm run build)
Level 6: Personal OS Protected Files 0-Byte Diff Verification (git diff)
```

---

## 2. Dedicated Pytest Suite Specification (`test_business_serials.py`)

1. `test_serial_creation_and_uniqueness`:
   - Validates serial registration, workspace/product uniqueness (`uq_biz_serial_ws_prod_num`).
   - Confirms duplicate registration is rejected with HTTP 400 `DUPLICATE_SERIAL`.
2. `test_tenant_isolation_serials`:
   - Validates that Workspace B cannot read, mutate, or allocate Workspace A serial numbers.
3. `test_grn_serial_receiving_and_attribution`:
   - Verifies receiving serialized product on GRN lines creates `business_serial_numbers` in `IN_STOCK` status.
   - Verifies stock movement attribution created in `business_stock_movement_serials`.
   - Confirms `count(serials) == accepted_quantity`.
4. `test_quantity_serial_count_mismatch`:
   - Rejects movement when `count(serials) != quantity` with HTTP 400 `SERIAL_COUNT_MISMATCH`.
5. `test_serial_dispatch_and_status_transition`:
   - Dispatches a serialized unit on `SALE` movement.
   - Verifies transition to `SHIPPED`, location cleared, attribution recorded.
6. `test_double_dispatch_prevention`:
   - Attempting to dispatch the same serial twice fails atomically with `SERIAL_NOT_AVAILABLE`.
7. `test_batch_serial_consistency`:
   - Verifies that serial belonging to Batch A cannot be dispatched against movement attributed to Batch B (`BATCH_SERIAL_MISMATCH`).
8. `test_location_invariant`:
   - Verifies serial's location matches inventory location during transfer movements.
9. `test_lifecycle_transitions_and_audit`:
   - Verifies state changes (`IN_STOCK` $\rightarrow$ `ALLOCATED` $\rightarrow$ `SHIPPED` $\rightarrow$ `CONSUMED`, `DEFECTIVE` $\rightarrow$ `DISPOSED`).
   - Verifies invalid transitions are rejected.
   - Verifies `AuditEvent` records generated for all sensitive transitions.
10. `test_rbac_serial_permissions`:
    - Tests 5-tier permissions: `serial:read`, `serial:write`, `serial:quarantine`.

---

## 3. Live Neon PostgreSQL E2E Scenarios (`scratch/e2e_c3_3_live.py`)

- **E2E-1**: Create serialized product & PO.
- **E2E-2**: Receive N serialized units via GRN; verify stock == N and serial count == N.
- **E2E-3**: Verify each serial is `IN_STOCK` with correct location and product.
- **E2E-4**: Attempt duplicate serial registration; verify rejection.
- **E2E-5**: Dispatch one valid serial; verify stock decreases by 1, serial transitions to `SHIPPED`.
- **E2E-6**: Attempt to dispatch the already-shipped serial again; verify rejection.
- **E2E-7**: Attempt dispatch with wrong product serial; verify rejection.
- **E2E-8**: Attempt cross-tenant serial access; verify rejection with HTTP 404 `SERIAL_NOT_FOUND`.
- **E2E-9**: Verify batch + serial consistency where applicable.
- **E2E-10**: Transition serial to `DEFECTIVE` and verify audit event.
- **E2E-11**: Verify unauthorized role (`VIEWER`) cannot mutate serial lifecycle.
- **E2E-12**: Verify concurrent/transactional double-dispatch cannot succeed twice.
