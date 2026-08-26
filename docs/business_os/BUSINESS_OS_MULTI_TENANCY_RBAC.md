# DEADLINEOS BUSINESS OS — MULTI-TENANCY & RBAC ARCHITECTURE
**Document ID:** `B0-DOC-003`
**Status:** `B0 DESIGN DECISION`
**Classification:** Security & Tenancy Architecture

---

## 1. Tenancy Model: Scoped Logical Multi-Tenancy
Business OS implements **Row-Level Tenancy Scoping** within PostgreSQL. All commercial tables contain a mandatory, indexed `workspace_id` foreign key.

```
                    ┌────────────────────────────┐
                    │      Personal User         │  (Authenticated via Supabase JWT)
                    └─────────────┬──────────────┘
                                  │ 1:N
                    ┌─────────────▼──────────────┐
                    │      WorkspaceMember       │  (Role: OWNER / ADMIN / MEMBER / ACCOUNTANT)
                    └─────────────┬──────────────┘
                                  │ N:1
                    ┌─────────────▼──────────────┐
                    │     BusinessWorkspace      │  (Commercial Isolation Boundary)
                    └─────────────┬──────────────┘
                                  │ 1:N
           ┌──────────────────────┼──────────────────────┐
           ▼                      ▼                      ▼
  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
  │   Customers     │    │    Invoices     │    │  Transactions   │
  │ (workspace_id)  │    │ (workspace_id)  │    │ (workspace_id)  │
  └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 2. Role-Based Access Control (RBAC) Matrix

Business OS defines five standard commercial roles tailored to small business operational reality:

| Permission Category | Permission Name | Owner | Admin | Member (Staff) | Accountant | Viewer |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Workspace** | `workspace:update` | ✅ | ❌ | ❌ | ❌ | ❌ |
| | `workspace:delete` | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Members** | `members:invite` | ✅ | ✅ | ❌ | ❌ | ❌ |
| | `members:remove` | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Commercial Registry** | `partner:read` | ✅ | ✅ | ✅ | ✅ | ✅ |
| | `partner:create_update` | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Financial Ledger** | `transaction:read` | ✅ | ✅ | ❌ (Own only)| ✅ | ✅ (No PII)|
| | `transaction:create` | ✅ | ✅ | ✅ (Draft) | ✅ | ❌ |
| | `transaction:reverse`| ✅ | ✅ | ❌ | ❌ | ❌ |
| **Invoices / Bills** | `invoice:read` | ✅ | ✅ | ✅ | ✅ | ✅ |
| | `invoice:create_issue`| ✅ | ✅ | ✅ | ✅ | ❌ |
| **Staging & Capture** | `capture:upload` | ✅ | ✅ | ✅ | ✅ | ❌ |
| | `staging:confirm` | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Copilot & AI** | `copilot:financial_q` | ✅ | ✅ | ❌ | ✅ | ❌ |
| | `copilot:operational_q`| ✅ | ✅ | ✅ | ✅ | ✅ |
| **Export / Audit** | `audit:export_tally` | ✅ | ✅ | ❌ | ✅ | ❌ |

---

## 3. Request Authorization Pipeline

Authentication and authorization are separated into a strict two-stage middleware pipeline:

```
 Incoming Request (HTTP Bearer JWT)
         │
         ▼
 ┌─────────────────────────────────────────────────┐
 │ Stage 1: Authentication (`@require_auth`)       │  (Platform Gateway)
 │ - Decodes JWT via JWKS                          │
 │ - Resolves `g.user_id`                          │
 └───────────────────────┬─────────────────────────┘
                         │
                         ▼
 ┌─────────────────────────────────────────────────┐
 │ Stage 2: Tenancy & RBAC                         │  (Business Middleware)
 │   (`@require_workspace(permission)`)            │
 │ - Extracts `X-Workspace-Id` header or route arg │
 │ - Queries `WorkspaceMember` for active record   │
 │ - Validates `member.has_permission(permission)` │
 │ - Sets `g.workspace_id` & `g.member_role`       │
 └───────────────────────┬─────────────────────────┘
                         │
                         ▼
 ┌─────────────────────────────────────────────────┐
 │ Stage 3: Repository Scoped Execution            │  (Domain Service)
 │ - Queries enforce `WHERE workspace_id = g.ws_id`│
 └─────────────────────────────────────────────────┘
```

---

## 4. Security Guarantees
1. **No Workspace Inference from User ID:** An API request cannot operate on business data without specifying `X-Workspace-Id`. A user with multiple workspaces must explicitly declare the target workspace per request.
2. **Denial on Suspended Tenancy:** If `BusinessWorkspace.status != 'ACTIVE'`, all write endpoints return HTTP 403 `WORKSPACE_SUSPENDED`.
3. **No Cross-Tenant Data Leaks via Copilot:** The Business Copilot query engine receives only pre-filtered data strictly bound to `g.workspace_id` and filtered by the user's role permissions before prompt construction.
