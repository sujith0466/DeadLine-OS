# DEADLINEOS BUSINESS OPERATIONS — MILESTONE C3.3 IMPLEMENTATION PLAN
# SERIAL NUMBER TRACKING & UNIT-LEVEL PROVENANCE

**Document ID**: `C3-3-PLAN-001`
**Milestone**: Phase C3.3 (Serial Number Tracking & Unit-Level Provenance)
**Status**: APPROVED

---

## 1. Execution Roadmap

```
Step 1: Architecture, Discovery & Threat Model Documentation [DONE]
Step 2: Database Migration (r5s6t7u8v9w0_business_os_serials_c3_3.py)
Step 3: ORM Models (BusinessSerialNumber, BusinessStockMovementSerial, Product extension)
Step 4: Domain Service (SerialService)
Step 5: Integration with GoodsReceiptService & InventoryService
Step 6: RBAC Permissions Update (serial:read, serial:write, serial:quarantine)
Step 7: REST API Endpoints (/api/business/serials) & Blueprint Registration
Step 8: Frontend Client Endpoints (frontend/src/api.ts)
Step 9: Dedicated Unit & Integration Test Suite (test_business_serials.py)
Step 10: Migration Chain Test Update (test_migration_chain_verification.py)
Step 11: Live Neon PostgreSQL E2E Gate (scratch/e2e_c3_3_live.py)
Step 12: Full Regression (360+ tests passing) & Frontend Build (0 errors)
Step 13: Protected Files Verification (0-byte diff)
Step 14: Final Implementation Audit & Freeze
```

---

## 2. Component Deliverables

### A. Database Layer
- Migration `backend/migrations/versions/r5s6t7u8v9w0_business_os_serials_c3_3.py`
  - Revisions: `q4r5s6t7u8v9` $\rightarrow$ `r5s6t7u8v9w0`
  - Adds `is_serialized` boolean column to `business_products`.
  - Creates `business_serial_numbers` table with constraints and indexes.
  - Creates `business_stock_movement_serials` table with unique constraint.

### B. Model Layer
- `backend/models/business/serial.py`: Defines `BusinessSerialNumber` and `BusinessStockMovementSerial`.
- `backend/models/business/product.py`: Adds `is_serialized` field.
- `backend/models/business/__init__.py`: Exports models in `__all__`.

### C. Domain Service Layer
- `backend/services/business/serial_service.py` (`SerialService`):
  - `register_or_receive_serials`: Atomic unit registration during GRN or initial stock.
  - `get_serial`: Workspace-scoped lookup with full provenance history.
  - `list_serials`: Filter by product, batch, status, location, with pagination.
  - `transition_lifecycle`: Validates state transition matrix, updates timestamps, logs `AuditEvent`.
  - `validate_and_attribute_movement`: Invariant validation, quantity check, row locking for concurrency safety, batch matching, and movement attribution.
  - `get_serial_provenance`: Full lifecycle chronological event history (GRN, movements, allocations, transitions).

### D. Integration Points
- `backend/services/business/goods_receipt_service.py`: Accepts `serial_numbers` per line, validates count, registers serials atomically.
- `backend/services/business/inventory_service.py`: Enforces serial attribution for serialized products on all stock movements.

### E. RBAC & Security Layer
- `backend/middleware/business_context.py`:
  - `serial:read`: `OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`
  - `serial:write`: `OWNER`, `ADMIN`, `MEMBER`
  - `serial:quarantine`: `OWNER`, `ADMIN`

### F. REST API Blueprint
- `backend/api/business/serials.py`:
  - `POST /api/business/serials`: Manual registration (where authorized).
  - `GET /api/business/serials`: List & search serials.
  - `GET /api/business/serials/<serial_id>`: Serial details and provenance.
  - `POST /api/business/serials/<serial_id>/transition`: Lifecycle state change.
  - `POST /api/business/serials/<serial_id>/quarantine`: Mark defective/quarantined.
  - `POST /api/business/serials/<serial_id>/dispose`: Mark disposed.
