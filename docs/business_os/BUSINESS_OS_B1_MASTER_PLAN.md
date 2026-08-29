# DEADLINEOS BUSINESS OS — B1 MASTER IMPLEMENTATION PLAN
**Document ID:** `B1-DOC-002`
**Status:** `PLANNING ONLY / READ-ONLY / AWAITING APPROVAL`
**Classification:** Master Implementation Plan
**Author:** DeadlineOS Lead Systems Architect & Program Implementation Planner
**Timestamp:** 2026-08-29T15:32:00+05:30

---

## 1. Executive Summary
Phase B1 (**Business Foundation**) establishes the multi-tenant substrate, 5-tier role-based access control (RBAC), commercial partner registry, and permanent audit logging architecture for DeadlineOS Business OS.

**Core Objectives:**
1. Provision isolated workspaces (`business_workspaces`) with strict row-level scoping.
2. Implement 5-tier membership authorization (`business_workspace_members`) via `@require_workspace(permission)`.
3. Build the customer & supplier commercial partner registry (`business_commercial_partners`).
4. Establish append-only, non-cascading audit logging (`business_audit_events`).
5. Ensure 100% Personal OS test isolation (162 existing tests remain continuously green).

---

## 2. Frozen Baselines & Commit Lineage
- **Certified Personal OS Tag:** `personal-os-v1.0-certified` $\rightarrow$ `32e177093c5e6859fcf3be9aa81f1d07a3fca901`
- **Certified Business OS B0 Tag:** `business-os-b0-frozen` $\rightarrow$ `872a1bbf9dfe08fd7da08c9af4d101a04c124868`
- **Current HEAD:** `872a1bbf9dfe08fd7da08c9af4d101a04c124868` on `main` (Clean working tree)

---

## 3. Scope of Phase B1 vs. Out-of-Scope Boundaries

### 3.1 In-Scope (Phase B1)
- Workspace creation, listing, switching, updating (`/api/business/workspaces`).
- Member invitations, role assignment, status updates (`/api/business/members`).
- 5-Tier RBAC middleware (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`).
- Commercial Partner Registry (Customers & Suppliers CRUD, `/api/business/partners`).
- Permanent Audit Trail emission (`business_audit_events`).
- Frontend Workspace Switcher component & Business API client headers (`X-Workspace-Id`).
- Automated Multi-Tenant Leakage & RBAC Security Test Suites.

### 3.2 Out-of-Scope (Strictly Gated for B2–B8)
- Invoices, Bills, and Payment Allocations (**Gated for B3**).
- Multimodal OCR, Voice Capture & Ingestion Artifacts (**Gated for B2**).
- AI Staging Barrier & Staged Extractions (**Gated for B2**).
- Cash Reality Runway Calculations & ADBR Math (**Gated for B3**).
- Business Copilot & AI Context Builders (**Gated for B4**).
- Accountant Tax/Tally CSV & ZIP Exports (**Gated for B5**).
- High-Throughput ASGI / Uvicorn Migration (**Gated for B8**).

---

## 4. Database Migration Plan (`business_*` Tables)

Create forward-only Alembic migration `d1a..._business_os_foundation.py` downstream of `c5e8b123987f`:

### 4.1 Table Specifications
```sql
-- 1. Workspaces
CREATE TABLE business_workspaces (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    tax_identifier VARCHAR(100),
    base_currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SUSPENDED', 'DELETED')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 2. Workspace Members
CREATE TABLE business_workspace_members (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'MEMBER' CHECK (role IN ('OWNER', 'ADMIN', 'MEMBER', 'ACCOUNTANT', 'VIEWER')),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INVITED', 'SUSPENDED')),
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_biz_ws_member UNIQUE (workspace_id, user_id)
);
CREATE INDEX idx_biz_ws_member_user ON business_workspace_members(user_id, status);

-- 3. Commercial Partners
CREATE TABLE business_commercial_partners (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    partner_type VARCHAR(20) NOT NULL CHECK (partner_type IN ('CUSTOMER', 'SUPPLIER', 'BOTH')),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    tax_identifier VARCHAR(100),
    credit_period_days INTEGER NOT NULL DEFAULT 30 CHECK (credit_period_days >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ARCHIVED')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_biz_partners_ws ON business_commercial_partners(workspace_id, partner_type, status);

-- 4. Audit Events (Non-Cascading)
CREATE TABLE business_audit_events (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    actor_user_id VARCHAR(36) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    before_state JSONB,
    after_state JSONB,
    reason TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_biz_audit_ws_entity ON business_audit_events(workspace_id, entity_type, entity_id);
```

---

## 5. Security & 5-Tier RBAC Permission Matrix

| Permission String | OWNER | ADMIN | MEMBER | ACCOUNTANT | VIEWER |
|---|:---:|:---:|:---:|:---:|:---:|
| `workspace:update` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `workspace:delete` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `members:invite` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `members:role_update` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `partners:read` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `partners:create` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `partners:update` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `audit:read` | ✅ | ✅ | ❌ | ✅ | ❌ |

---

## 6. API Endpoint Contracts (`/api/business/*`)

| Route Path | Method | Minimum Permission | Request Payload Summary | Response Payload Summary |
|---|---|---|---|---|
| `/api/business/workspaces` | `POST` | `@require_auth` | `{ "name": "Acme Corp", "legal_name": "Acme Inc", "tax_identifier": "GST123" }` | `{ "workspace": { "id": "...", "name": "Acme Corp", "role": "OWNER" } }` |
| `/api/business/workspaces` | `GET` | `@require_auth` | None | `{ "workspaces": [ { "id": "...", "name": "...", "role": "..." } ] }` |
| `/api/business/workspaces/current`| `GET` | `@require_workspace` | None | `{ "workspace": { ... }, "member": { "role": "..." } }` |
| `/api/business/members/invite` | `POST` | `members:invite` | `{ "email": "user@domain.com", "role": "MEMBER" }` | `{ "member": { "id": "...", "status": "INVITED" } }` |
| `/api/business/members` | `GET` | `@require_workspace` | None | `{ "members": [ ... ] }` |
| `/api/business/partners` | `POST` | `partners:create` | `{ "partner_type": "CUSTOMER", "name": "Apex Ltd", "credit_period_days": 30 }` | `{ "partner": { "id": "...", "name": "Apex Ltd" } }` |
| `/api/business/partners` | `GET` | `partners:read` | `?type=CUSTOMER&search=Apex` | `{ "partners": [ ... ], "total": 1 }` |
| `/api/business/audit` | `GET` | `audit:read` | `?entity_type=PARTNER&limit=50` | `{ "events": [ ... ] }` |

---

## 7. Phase B1 Milestone Breakdown & Task List

### B1.0: Implementation Readiness & Branch Setup
- Create branch `feature/b1-foundation`.
- Verify 162 Personal OS tests pass locally.

### B1.1: Database Migrations & Domain Models
- Create `backend/models/business/` directory.
- Implement SQLAlchemy models: `Workspace`, `WorkspaceMember`, `CommercialPartner`, `AuditEvent`.
- Author Alembic forward migration script `d1a..._business_os_foundation.py`.

### B1.2: Two-Stage Middleware & Tenancy Enforcement
- Implement `backend/middleware/business_context.py` containing `@require_workspace(permission)`.
- Register error handlers for `WORKSPACE_ACCESS_DENIED` and `PERMISSION_DENIED`.

### B1.3: Partner Registry & Audit Repositories
- Implement `backend/services/business/partner_service.py` with duplicate prevention and validation.
- Implement `backend/services/business/audit_service.py` with immutable append-only inserts.

### B1.4: Business Blueprint & API Routes
- Implement `backend/api/business/workspaces.py`.
- Implement `backend/api/business/members.py`.
- Implement `backend/api/business/partners.py`.
- Mount `business_bp` under `/api/business` in `backend/app.py`.

### B1.5: Frontend Workspace Foundation
- Update `frontend/src/api.ts` with `X-Workspace-Id` interceptor and Business OS API methods.
- Create `frontend/src/components/Business/WorkspaceSwitcher.tsx`.

### B1.6: Automated Security & Regression Test Execution
- Author `test_workspace_scoping.py`, `test_multi_tenant_leakage.py`, `test_rbac_permissions.py`.
- Execute full 162-test Personal OS regression suite.

### B1.7: Release Verification & Governance Gate
- Run frontend production build (`tsc -b && vite build`).
- Verify clean working tree and tag readiness.

---

## 8. Dependency Graph

```
B1.0 (Readiness)
       ↓
B1.1 (Migrations & Models)
       ↓
B1.2 (Tenancy & RBAC Middleware)
       ↓
B1.3 (Partner & Audit Services)
       ↓
B1.4 (API Routes & Blueprint)
       ↓
B1.5 (Frontend Client & Switcher)
       ↓
B1.6 (Security & Regression Tests)
       ↓
B1.7 (B1 Certification Gate)
```

---

## 9. Risk Register & Mitigation Controls

| Risk ID | Threat Vector | Severity | Mitigation Control | Verification Gate |
|---|---|:---:|---|---|
| `RSK-B1-01` | Cross-tenant partner leakage | **CRITICAL** | Every query enforces `WHERE workspace_id = g.workspace_id`. | `test_multi_tenant_leakage.py` |
| `RSK-B1-02` | RBAC bypass via manipulated role | **CRITICAL** | Middleware evaluates DB membership role, never client payload. | `test_rbac_permissions.py` |
| `RSK-B1-03` | Personal OS schema contamination | **HIGH** | Forward-only migration touching exclusively `business_*` tables. | 162 Personal OS test suite |
| `RSK-B1-04` | Audit trail erasure on tenant delete | **HIGH** | `business_audit_events.workspace_id` has no `ON DELETE CASCADE`. | `test_audit_immutability.py` |

---

## 10. Acceptance & Exit Criteria
1. **Migration Integrity:** Forward-only migration executes cleanly up and down against PostgreSQL.
2. **Tenancy Isolation:** Zero cross-tenant data leakage across all routes.
3. **RBAC Enforcement:** 100% test coverage of all 5 roles across all endpoints.
4. **Personal OS Zero-Regression:** All 162 Personal OS tests pass with 0 failures.
5. **Frontend Build:** `tsc -b && vite build` completes with 0 errors.

---

## 11. Final Implementation Plan Verdict

```
B1 MASTER IMPLEMENTATION PLAN — PASS (READY FOR APPROVAL)
IMPLEMENTATION STATUS: NOT STARTED (AWAITING USER AUTHORIZATION)
```
