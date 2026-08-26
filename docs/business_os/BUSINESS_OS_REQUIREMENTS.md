# DEADLINEOS BUSINESS OS — REQUIREMENTS SPECIFICATION
**Document ID:** `B0-DOC-014`
**Status:** `B0 ARCHITECTURAL SPECIFICATION`
**Classification:** Engineering Requirements Specification

---

## 1. Functional Requirements (FR)
- **`FR-001` (Workspace Scoping):** The system MUST permit any authenticated user to create, join, and switch between multiple isolated commercial workspaces.
- **`FR-002` (RBAC Enforcement):** The system MUST enforce 5-tier role permissions (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`) across all API endpoints.
- **`FR-003` (Multimodal Capture):** The system MUST accept PDF, DOCX, PNG, JPG, WebP, and audio uploads and route them to `IngestionArtifact` storage.
- **`FR-004` (Staging Workflow):** The system MUST stage all AI-extracted invoice and expense fields for human review before committing to the financial ledger.
- **`FR-005` (Receivable/Payable Tracking):** The system MUST calculate invoice aging (0–30, 31–60, 61–90, 90+ days) and track remaining balances due upon partial payments.
- **`FR-006` (Cash Runway & Runway Days):** The system MUST calculate real-time confirmed cash, committed inflows, committed outflows, and runway days ($\lfloor\text{Confirmed Cash} / \text{ADBR}_{30}\rfloor$) deterministically. If data is stale ($>7$ days) or history $<14$ days, it MUST return explicit state codes (`RUNWAY_STALE`, `RUNWAY_INSUFFICIENT_HISTORY`).
- **`FR-007` (Transaction Reversals):** The system MUST support reversible ledger adjustments with mandatory audit reason logging without deleting original transactions or rewriting historical financial facts.
- **`FR-008` (Business Copilot):** The system MUST provide a conversational Q&A interface answering questions strictly grounded in pre-queried workspace records.
- **`FR-009` (Accountant Export):** The system MUST generate standard CSV and PDF export packages covering transaction ledgers, aging reports, and stored invoices.
- **`FR-010` (Personal OS Sync):** The system MUST project business deadlines and collection reminders into the user's personal Today/Calendar views without mutating personal models.

---

## 2. Non-Functional Requirements (NFR)
- **`NFR-001` (Response Latency):** Read API endpoints MUST respond in $< 300\text{ms}$ at p95 under standard load.
- **`NFR-002` (Extraction Time):** Single-page PDF / image document extraction MUST stage within $< 5.0\text{s}$ at p90.
- **`NFR-003` (Storage Availability):** Ingested documents MUST be stored in persistent cloud object storage with 99.9% availability SLA.
- **`NFR-004` (Platform Isolation):** Zero changes in Business OS code or schema may break existing Personal OS Phase 0–8 automated tests.

---

## 3. Security Requirements (SEC)
- **`SEC-001` (Tenancy Isolation):** No database query or API endpoint may return data belonging to a workspace where the requesting user lacks an active membership.
- **`SEC-002` (Copilot Zero-Bypass):** The Business Copilot prompt MUST NOT receive or reveal records that the requesting user's RBAC role forbids them from reading directly.
- **`SEC-003` (Signed Document URLs):** Ingestion documents stored in object storage MUST NOT be public; access MUST require pre-signed URLs expiring within $\le 15\text{ minutes}$.
- **`SEC-004` (Prompt Injection Shield):** All document transcripts and voice inputs MUST pass through `AISafety.assert_prompt_safe` before processing.

---

## 4. Data Integrity Requirements (DIR)
- **`DIR-001` (Exact Decimal Arithmetic):** All monetary computations MUST use `Numeric(15, 2)` / Python `Decimal`. Floating-point math is strictly prohibited.
- **`DIR-002` (Settlement Balance Invariant):** An invoice's `paid_amount + balance_due` MUST exactly equal its `total_amount` ($\text{subtotal} + \text{tax\_amount} - \text{discount\_amount}$) at all times, matching raw allocation records.
- **`DIR-003` (Idempotent Submissions):** Mutation endpoints MUST enforce `Idempotency-Key` headers to prevent dual payments or duplicate invoice creation.
- **`DIR-004` (Immutable Audit Records):** `business_audit_events` rows MUST be strictly append-only and preserved across workspace lifecycle events.

---

## 5. AI Safety Requirements (AIR)
- **`AIR-001` (No Unsupervised State Mutation):** AI model output MUST NEVER directly mutate `business_transactions` or `business_invoices` without explicit human confirmation.
- **`AIR-002` (Schema Conformance):** All structured LLM responses MUST be validated against JSON schemas before downstream consumption.
- **`AIR-003` (Deterministic Fallback):** If AI providers (OpenRouter & Gemini) are unreachable, the system MUST gracefully degrade to deterministic heuristic mode without returning HTTP 500.
