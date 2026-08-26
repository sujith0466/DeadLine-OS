# DEADLINEOS BUSINESS OS — B0 PASS 2 MASTER ARCHITECTURE BLUEPRINT
**Document ID:** `B0-DOC-018`
**Status:** `B0 DESIGN DECISION`
**Classification:** Master Systems Architecture Blueprint

---

## 1. Master System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       CLIENT APPLICATION TIER                                    │
│   - React 18 + TypeScript + Tailwind CSS                                                         │
│   - Workspace Switcher [ Personal OS | Acme Studio ]                                             │
│   - Capture Drawer (OCR / PDF / Voice) | Cash Runway Header | Invoices & Ledger UI               │
└────────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                 │ HTTPS / Bearer JWT / X-Workspace-Id
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       API & GATEWAY TIER (Flask)                                 │
│   ├── Authentication Layer (`utils/auth.py`): JWKS RS256/ES256 Verification                     │
│   ├── Business Tenancy Middleware (`@require_workspace`): Resolves `g.workspace_id` & RBAC       │
│   └── Blueprint Routes (`/api/business/*`): Workspaces, Invoices, Transactions, Staging, Copilot │
└────────────────────────┬───────────────────────────────────────────────────────┬─────────────────┘
                         │                                                       │
                         ▼                                                       ▼
┌───────────────────────────────────────────────────┐ ┌────────────────────────────────────────────┐
│              BUSINESS DOMAIN TIER                 │ │          SHARED PLATFORM TIER              │
│   ├── Workspace & Member Service                  │ │   ├── Hybrid AI Provider (`ai/provider.py`)│
│   ├── Commercial Partner Registry                 │ │   ├── AI Safety & Schema (`ai/safety.py`)  │
│   ├── Ingestion & Staging Service                 │ │   ├── Timezone Utilities (`utils/timezone`)│
│   ├── Invoice & Receivable Service                │ │   ├── Blinker Event Bus (`runtime/event_bus`)│
│   ├── Financial Ledger & Cash Runway Engine       │ │   ├── Outbox Dispatcher (`runtime/outbox`) │
│   ├── Business Risk Engine                        │ │   └── Standard Responses & Error Envelopes │
│   └── Business Copilot Service                    │ └────────────────────────────────────────────┘
└────────────────────────┬──────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      PERSISTENCE & STORAGE TIER                                  │
│   ├── PostgreSQL 16 Database (Neon): Isolated `business_*` tables with `workspace_id` keys       │
│   ├── Cloud Object Storage (Supabase Storage): Private document PDFs with signed 15-min URLs     │
│   └── Transactional Outbox & Append-Only Audit Event Tables                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Personal OS Regression Protection Guarantee
The certified Personal OS v1.0 baseline remains protected by the following architectural invariants:
1. **Zero Model Modifications:** Existing models (`Task`, `Goal`, `Habit`, `ScheduleSlot`, `User`) remain completely untouched.
2. **Zero Route Collisions:** All Business OS APIs are namespaced under `/api/business/*`.
3. **Forward-Only Alembic Migrations:** New migrations will ONLY introduce `business_*` tables.
4. **Independent Regression Gate:** Continuous integration runs all 162 Personal OS backend tests on every PR.

---

## 3. Architecture Scorecard

| Domain | Status | Architectural Rationale & Controls |
|---|:---:|---|
| **Product Definition** | 🟢 GREEN | Explicit MSME target chosen; ERP non-goals clearly established. |
| **Multi-Tenancy** | 🟢 GREEN | Row-level tenant isolation with composite primary keys designed. |
| **RBAC / Authorization** | 🟢 GREEN | 5-tier role hierarchy enforced at middleware layer. |
| **Financial Arithmetic**| 🟢 GREEN | Decimal precision (`NUMERIC(15, 2)`) mandated; float math banned. |
| **Ledger Immutability** | 🟢 GREEN | Reversible adjustment model without destructive deletes. |
| **AI Safety & Boundaries**| 🟢 GREEN | Mandatory staging queue barrier for document extraction. |
| **Copilot Security** | 🟢 GREEN | Zero-bypass prompt building from role-filtered database queries. |
| **Event & Outbox** | 🟢 GREEN | Transactional outbox with 24h idempotency keys. |
| **Storage & Cloud** | 🟢 GREEN | Supabase cloud object storage with signed URLs for Render. |
| **Integration Bridge** | 🟢 GREEN | Polymorphic schedule slot adapter to personal Today view. |
| **Auditability** | 🟢 GREEN | Immutable `business_audit_events` with actor and diff logging. |
| **Deployability** | 🟢 GREEN | Seamless integration with existing Render web service & Neon DB. |
