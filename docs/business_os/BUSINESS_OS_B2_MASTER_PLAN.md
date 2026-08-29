# DEADLINEOS BUSINESS OS — PHASE B2 MASTER IMPLEMENTATION PLAN

**Document ID:** `B2-DOC-002`

**Phase:** Business OS B2 — Capture & Staging

**Classification:** Authoritative Implementation Blueprint & Safety Contract

**Author:** DeadlineOS Principal Architecture & Engineering Board

**Status:** READY FOR SINGLE IMPLEMENTATION AUTHORIZATION (NO APPLICATION CODE IMPLEMENTED)

**Date:** 2026-08-29T15:50:00+05:30



---



## 1. Executive Summary & Purpose



Phase B2 establishes the **Capture & Staging Subsystem** of DeadlineOS Business OS. The mission of B2 is to build a high-integrity, multi-modal ingestion pipeline (Text, Audio, Documents) that extracts, normalizes, and stages candidate business data **without allowing probabilistic AI outputs to mutate authoritative business state or financial ledgers without human review**.



```text

========================================================================================

                                 B2 INGESTION PIPELINE

========================================================================================

[User Input] (Text / Audio / PDF / Image)

      │

      ▼

[Capture Gateway] ──► Validate MIME & Size (≤15MB) ──► SHA-256 Hash

      │

      ▼

[Object Storage] ──► Upload Raw Artifact (Supabase Storage / S3) ──► `business_ingestion_artifacts`

      │

      ▼

[AI Extraction] ──► HybridFailover Provider (Schema JSON Output)

      │

      ▼

[Deterministic Normalization] ──► Decimal Currency, ISO Dates, Entity Disambiguation

      │

      ▼

[Staging Table] ──► `business_staged_extractions` (Status: `NEEDS_REVIEW`)

      │

      ▼

[Human-in-the-Loop Review] ──► Split-Screen UI: Preview Source + Edit Fields

      │

      ├───► [REJECTED] ──► Reason Recorded + Audit Event

      │

      └───► [CONFIRMED] ──► `STAGED_EXTRACTION_CONFIRMED` Event

                                 │

                                 ▼ (Downstream B3 Hand-off — No B3 execution in B2)

```



---



## 2. Certified Baselines & Governance Rules



1. **Certified Baselines:**

   - Personal OS: `personal-os-v1.0-certified` (`32e1770`) — **FROZEN / UNTOUCHED**

   - Business OS B0: `business-os-b0-frozen` (`872a1bb`) — **BINDING ARCHITECTURE**

   - Business OS B1: `business-os-b1-certified` (`f72cab4`) — **FOUNDATION BASELINE**

2. **Zero Downstream Contamination:** B2 must NOT create ledger entries, invoices, payment allocations, cash runway math, or Copilot chat agents.

3. **Mandatory Regression Standard:** Every B2 verification step must pass all 162 Personal OS tests + new B2 tests.



---



## 3. Data Architecture & Schema Plan



### 3.1 Database Migration: `e2b3c4d5e6f7_business_os_capture_staging.py`

Downstream of `d1a2b3c4d5e6` (`d1a2b3c4d5e6_business_os_foundation.py`).



### 3.2 Tables Proposed



#### 1. `business_ingestion_artifacts`

Stores raw metadata and object storage pointers for all uploaded documents and audio files.

- `id`: `String(36)` Primary Key (UUID)

- `workspace_id`: `String(36)` Foreign Key $\rightarrow$ `business_workspaces.id` (`ON DELETE CASCADE`)

- `uploader_user_id`: `String(36)` Foreign Key $\rightarrow$ `users.id`

- `artifact_type`: `String(20)` (`DOCUMENT`, `AUDIO`, `TEXT_SNIPPET`)

- `storage_path`: `String(500)` (Relative object storage path)

- `file_name`: `String(255)`

- `file_size_bytes`: `Integer`

- `mime_type`: `String(100)`

- `sha256_hash`: `String(64)` (Indexed for workspace duplicate detection)

- `status`: `String(20)` (`STORED`, `PROCESSED`, `FAILED`, `ARCHIVED`)

- `created_at` / `updated_at`: `DateTime(timezone=True)`



#### 2. `business_staged_extractions`

Stores structured candidate business data awaiting human review.

- `id`: `String(36)` Primary Key (UUID)

- `workspace_id`: `String(36)` Foreign Key $\rightarrow$ `business_workspaces.id` (`ON DELETE CASCADE`)

- `artifact_id`: `String(36)` Foreign Key $\rightarrow$ `business_ingestion_artifacts.id` (Nullable for direct text capture)

- `created_by_user_id`: `String(36)` Foreign Key $\rightarrow$ `users.id`

- `reviewed_by_user_id`: `String(36)` Foreign Key $\rightarrow$ `users.id` (Nullable)

- `source_channel`: `String(20)` (`TEXT_PROMPT`, `VOICE_AUDIO`, `DOCUMENT_UPLOAD`)

- `candidate_type`: `String(50)` (`EXPENSE`, `INVOICE_RECEIVABLE`, `INVOICE_PAYABLE`, `PAYMENT_RECORD`, `NOTE`)

- `status`: `String(20)` (`RECEIVED`, `PROCESSING`, `EXTRACTED`, `NEEDS_REVIEW`, `CONFIRMED`, `REJECTED`, `FAILED`, `EXPIRED`)

- `raw_extracted_data`: `JSON` (Unmodified LLM/OCR JSON payload)

- `normalized_data`: `JSON` (Cleaned, Decimal-validated candidate fields: `amount`, `currency`, `date`, `partner_id`, `partner_name`, `tax_id`, `line_items`)

- `confidence_score`: `Integer` (0–100)

- `confidence_breakdown`: `JSON` (Field-level confidence mapping)

- `provenance_metadata`: `JSON` (Model name, provider, latency, prompt tokens, bounding box coordinates if PDF)

- `rejection_reason`: `Text` (Nullable)

- `confirmed_at` / `reviewed_at`: `DateTime(timezone=True)` (Nullable)

- `created_at` / `updated_at`: `DateTime(timezone=True)`



---



## 4. Extraction, Normalization & Entity Disambiguation Engine



### 4.1 Deterministic Number & Currency Normalizer

- Handles standard numbers and Indian format numbering expressions:

  - `5000` / `5,000` / `₹5,000` $\rightarrow$ `Decimal('5000.00')`

  - `5k` / `5K` $\rightarrow$ `Decimal('5000.00')`

  - `1.5 lakh` / `1.5L` $\rightarrow$ `Decimal('150000.00')`

  - `2 crore` / `2Cr` $\rightarrow$ `Decimal('20000000.00')`

- Strictly validates currency codes against ISO 4217 (Default: `INR`).

- Converts all monetary amounts to Python `Decimal` and serializes as fixed 2-decimal strings.



### 4.2 Deterministic Date Normalizer

- Normalizes absolute formats (`29/08/2026`, `2026-08-29`, `29 Aug 2026`) and relative expressions (`yesterday`, `today`, `due next Friday`) relative to the workspace's configured timezone (`Asia/Kolkata`).

- Output: Strict ISO 8601 date string `YYYY-MM-DD`.



### 4.3 Multi-Tenant Entity Disambiguation

- Queries `business_commercial_partners` scoped strictly to `workspace_id = g.workspace_id`.

- **Exact Match:** If extracted name matches existing partner (case-insensitive) $\rightarrow$ links `partner_id` with 100 confidence.

- **Ambiguous Match:** If multiple fuzzy matches exist (e.g., "Ravi Kumar" vs "Ravi Stores") $\rightarrow$ leaves `partner_id` null, flags `AMBIGUOUS_PARTNER`, and presents matching choices to reviewer.

- **No Match:** Leaves `partner_id` null, marks candidate as `NEW_PARTNER_SUGGESTION`, prompts user to create partner upon confirmation.



---



## 5. API Architecture Plan (`/api/business/...`)



All endpoints require `@require_workspace(permission)`.



### 5.1 Capture Endpoints

1. `POST /api/business/capture/text`

   - Role Permission: `staging:create` (`OWNER`, `ADMIN`, `MEMBER`)

   - Request: `{"text": "Bought office supplies for 12,500 from Reliance Retail"}`

   - Action: Runs extraction $\rightarrow$ normalization $\rightarrow$ creates staged extraction.

2. `POST /api/business/capture/upload`

   - Role Permission: `staging:create` (`OWNER`, `ADMIN`, `MEMBER`)

   - Request: `multipart/form-data` (`file`, `artifact_type`)

   - Action: Validates MIME/size $\rightarrow$ uploads to object storage $\rightarrow$ triggers async/sync extraction.



### 5.2 Staging & Review Endpoints

3. `GET /api/business/staging`

   - Role Permission: `staging:read` (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`)

   - Query params: `status`, `candidate_type`, `limit`, `offset`.

4. `GET /api/business/staging/<staging_id>`

   - Role Permission: `staging:read`

   - Returns full candidate data, source artifact signed URL, and confidence breakdown.

5. `PATCH /api/business/staging/<staging_id>`

   - Role Permission: `staging:update` (`OWNER`, `ADMIN`, `MEMBER`)

   - Request: `{"normalized_data": {"amount": "13000.00", "partner_id": "..."}}`

   - Updates candidate fields prior to confirmation.

6. `POST /api/business/staging/<staging_id>/confirm`

   - Role Permission: `staging:confirm` (`OWNER`, `ADMIN`, `MEMBER`)

   - Action: Validates all required fields present $\rightarrow$ transitions status to `CONFIRMED` $\rightarrow$ emits `STAGED_EXTRACTION_CONFIRMED` audit & outbox event.

7. `POST /api/business/staging/<staging_id>/reject`

   - Role Permission: `staging:reject` (`OWNER`, `ADMIN`, `MEMBER`)

   - Request: `{"reason": "Duplicate invoice"}`

   - Action: Transitions status to `REJECTED` $\rightarrow$ emits `STAGED_EXTRACTION_REJECTED` audit event.



---



## 6. Frontend Staging & Review Component Plan



1. **`CaptureModal.tsx`:** Unified modal supporting quick text prompt, audio dictation recording, and file drag-and-drop.

2. **`StagingQueue.tsx`:** Dashboard widget displaying pending candidate items requiring review.

3. **`ReviewDrawer.tsx`:** Split-screen verification surface:

   - Left: PDF/Image viewer with zoom or audio player / raw text view.

   - Right: Editable form fields (Candidate Type, Amount in ₹, Date, Partner selector dropdown with autocomplete, Notes).

   - Bottom: Confidence indicators, "Reject" button, and primary "Confirm Extraction" button.



---



## 7. Milestone Execution Sequence (B2.0 $\rightarrow$ B2.8)



| Milestone | Scope & Deliverables | Primary Artifacts |

|:---:|---|---|

| **B2.0** | Branch Setup & Pre-Flight Baseline Verification | Branch `feature/b2-capture-staging`, verify 162 Personal OS tests green. |

| **B2.1** | Database Migrations & Ingestion Models | Migration `e2b3c4d5e6f7`, `business_ingestion_artifacts`, `business_staged_extractions`. |

| **B2.2** | Object Storage Driver & Artifact Ingestion | Object storage adapter (Supabase Storage / signed URLs), MIME/SHA-256 validation. |

| **B2.3** | Extraction Pipeline & AI Normalization Engine | Multi-modal extractor, Indian numbering normalizer, date resolver, partner disambiguation. |

| **B2.4** | Business Capture & Staging API Routes | `/api/business/capture/*` and `/api/business/staging/*` endpoints. |

| **B2.5** | Frontend Capture & Split-Screen Review UI | `CaptureModal.tsx`, `StagingQueue.tsx`, `ReviewDrawer.tsx`. |

| **B2.6** | Security & Red-Team Verification Suites | Unit & integration tests for IDOR, prompt injection, MIME validation, RBAC boundaries. |

| **B2.7** | End-to-End Regression & Release Gate | 162 Personal OS tests + all B1/B2 tests + Vite production build. |

| **B2.8** | Final Certification & Release Tagging | Tag `business-os-b2-certified`, merge to `main`, update Master Tracker. |



---



## 8. Requirements Traceability Matrix



| B0 Requirement | B2 Architectural Implementation | Test Verification Suite |

|---|---|---|

| **Multi-Modal Capture** | `POST /api/business/capture/text` & `upload` | `test_capture_ingestion.py` |

| **Zero Auto-Commit Barrier** | `business_staged_extractions` (`NEEDS_REVIEW` $\rightarrow$ `CONFIRMED`) | `test_staging_lifecycle.py` |

| **Multi-Tenant Scoping** | `@require_workspace` on all artifact/staging tables | `test_staging_tenant_isolation.py` |

| **Indian Number Formatting** | Deterministic normalizer regex (`5k`, `1.5 lakh`, `₹5,000`) | `test_normalization.py` |

| **Partner Disambiguation** | Scoped search against `business_commercial_partners` | `test_entity_disambiguation.py` |

| **Forensic Audit Diff** | `AuditService.log_event` on staging state changes | `test_staging_audit.py` |



---



## 9. Next Steps

Stop and submit this Master Plan for user review and single authorization.
