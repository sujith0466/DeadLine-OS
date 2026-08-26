# DEADLINEOS BUSINESS OS — ARCHITECTURAL DECISION RECORDS (ADR) INDEX
**Document ID:** `B0-DOC-017`
**Status:** `B0 DESIGN DECISION`
**Classification:** Architectural Governance

---

## Index of Approved Architectural Decisions (ADR-001 to ADR-020)

### `ADR-001`: Product Scope — Operational OS vs. Statutory ERP
- **Decision:** Business OS is strictly an Operational Co-Pilot and Financial Clarity Engine for MSMEs. It is NOT a general ledger, statutory tax filing, or full ERP system.
- **Rationale:** Small business owners suffer from paperwork lag and unrecovered receivables, not lack of tax filing tools.

### `ADR-002`: Initial Target ICP
- **Decision:** Focus exclusively on Owner-Operated Service & Trade Micro-Enterprises (5–15 employees) in commercial hubs.
- **Rationale:** Highest pain from operational context-switching and delayed receivable follow-ups.

### `ADR-003`: Multi-Tenancy & Workspace Scoping
- **Decision:** Implement Row-Level Tenancy with explicit `workspace_id` foreign keys and composite indexes across all business tables.
- **Rationale:** Reusing `user_id` is mathematically incapable of supporting multi-member collaboration and tenant isolation.

### `ADR-004`: Role-Based Access Control (RBAC)
- **Decision:** Enforce a 5-tier role hierarchy (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`) at the API middleware level.
- **Rationale:** Prevents staff from viewing sensitive executive cash positions while allowing them to log operational jobs.

### `ADR-005`: Business Domain Boundary Isolation
- **Decision:** Business OS domain entities live in separate, new PostgreSQL tables (`business_*`) without modifying frozen Personal OS models.
- **Rationale:** Protects the certified Personal OS v1.0 baseline from breaking regressions.

### `ADR-006`: Four-Tier Cash Reality Model
- **Decision:** Model cash as Confirmed In-Hand Cash + Committed Inflows - Committed Outflows = Projected Position.
- **Rationale:** Prevents presenting speculative or uncollected money as actual bank balance.

### `ADR-007`: Monetary Precision & Currency Representation
- **Decision:** All monetary fields stored as `NUMERIC(15, 2)` in PostgreSQL, manipulated with Python `Decimal`, and serialized as Strings in JSON payloads.
- **Rationale:** Floating-point binary representation causes unacceptable rounding errors in financial transactions.

### `ADR-008`: Append-Only Financial Ledger & Reversals
- **Decision:** Prohibit destructive `DELETE` / in-place `UPDATE` on confirmed transactions. Corrections must create adjustment records.
- **Rationale:** Full historical traceability and accounting auditability.

### `ADR-009`: Mandatory Human-in-the-Loop Capture Barrier
- **Decision:** AI document extractions must pass through `StagedExtraction` and require explicit human review confirmation before committing.
- **Rationale:** Prevents probabilistic OCR hallucinations from corrupting the financial ledger.

### `ADR-010`: Deterministic Entity Disambiguation
- **Decision:** When natural language or voice commands match multiple partners, the system must prompt the user rather than guessing.
- **Rationale:** Assigning financial balances to the wrong commercial entity creates severe liability.

### `ADR-011`: Strict AI vs. Deterministic Separation
- **Decision:** Arithmetic, balances, state transitions, and authorization are 100% deterministic code. AI is restricted to advisory summaries, OCR, and NLU.
- **Rationale:** LLMs are non-deterministic and must not hold financial authority.

### `ADR-012`: Zero-Bypass Business Copilot Architecture
- **Decision:** Copilot prompts receive only pre-queried, role-filtered database context strictly bound to `g.workspace_id`.
- **Rationale:** Prevents prompt injection or role-escalation attacks from bypassing RBAC.

### `ADR-013`: Transactional Outbox Pattern for Business Events
- **Decision:** Events are written to `business_outbox_events` in the same database commit as entity mutations, then dispatched to Blinker signals.
- **Rationale:** Guarantees at-least-once event delivery without two-phase commit overhead.

### `ADR-014`: Polymorphic Bridge Integration to Personal OS
- **Decision:** Business deadlines and receivables project into personal Today/Calendar views using generic schedule slot adapters.
- **Rationale:** Integrates owner daily execution without contaminating Personal OS database schemas.

### `ADR-015`: Cloud Object Storage for Ingested Documents
- **Decision:** Store all uploaded PDFs, receipts, and audio in Supabase Storage with 15-minute presigned access URLs.
- **Rationale:** Overcomes Render's ephemeral container disk limitations securely.

### `ADR-016`: Cloud-First Sync Architecture
- **Decision:** Build as a cloud-first, mobile-responsive web architecture in MVP; defer local offline database syncing.
- **Rationale:** Small business financial data requires immediate real-time consistency across owner and accountant.

### `ADR-017`: Production Deployment Strategy on Render
- **Decision:** Deploy Business OS as an integrated `/api/business` blueprint extension within the existing certified Render web service.
- **Rationale:** Zero infrastructure expansion costs; unified SSL, DNS, and connection pooling.

### `ADR-018`: Scalability & Async I/O Evolution
- **Decision:** Retain Eventlet for B0/B1 MVP; schedule migration to ASGI (Uvicorn) for Phase B8.
- **Rationale:** Preserves production stability during active business domain feature construction.

### `ADR-019`: Immutable Audit Trail Specification
- **Decision:** Store every mutation in `business_audit_events` with actor ID, IP address, before/after diffs, and timestamp.
- **Rationale:** Provides irrefutable forensic auditability for accountant and tax inspections.

### `ADR-020`: Accountant Export Interoperability
- **Decision:** Provide one-click CSV ledger export, receivable aging report, and ZIP package of original invoice PDFs.
- **Rationale:** Drastically reduces friction when handing data to external bookkeepers and tax preparers.
