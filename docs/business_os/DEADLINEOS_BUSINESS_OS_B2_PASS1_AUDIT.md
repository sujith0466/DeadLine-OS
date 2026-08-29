# DEADLINEOS BUSINESS OS — B2 PASS 1 CODEBASE AUDIT

**Document ID:** `B2-DOC-001`

**Phase:** Business OS B2 — Capture & Staging

**Pass:** Pass 1 — Codebase Audit & Foundation Assessment

**Author:** DeadlineOS Principal Architecture & Security Due-Diligence Board

**Status:** COMPLETE / REVIEW ONLY (NO APPLICATION CODE IMPLEMENTED)

**Date:** 2026-08-29T15:50:00+05:30



---



## 1. Executive Summary & Certified Baseline Verification



This audit evaluates the DeadlineOS repository immediately following the certified release of **Business OS Phase B1 (Business Foundation)**. The objective is to verify certified baselines, inspect reusable platform primitives, identify B2 architectural gaps, and construct an airtight implementation blueprint for **Phase B2 (Capture & Staging)** without introducing premature Phase B3–B8 scope or violating Personal OS isolation.



### 1.1 Certified Baseline Verification (Direct Git Evidence)



```text

Commit Lineage Verification:

f72cab4 (HEAD -> main, tag: business-os-b1-certified, origin/main) feat: implement Business OS B1 foundation

872a1bb (tag: business-os-b0-frozen) docs: freeze Business OS B0 architecture

32e1770 (tag: personal-os-v1.0-certified) fix: harden planner timezone handling

```



| Baseline Entity | Certified Git Tag | Commit SHA Target | Status |

|---|---|---|:---:|

| **Personal OS Phase 0–8 Baseline** | `personal-os-v1.0-certified` | `32e177093c5e6859fcf3be9aa81f1d07a3fca901` | **FROZEN / UNTOUCHED** |

| **Business OS B0 Architecture** | `business-os-b0-frozen` | `872a1bbf9dfe08fd7da08c9af4d101a04c124868` | **FROZEN / BINDING** |

| **Business OS B1 Foundation** | `business-os-b1-certified` | `f72cab46e55a5ccf8fe55d1b46146b2c6b20a38c` | **RELEASED & VERIFIED** |

| **Active Working Tree** | `main` | `f72cab4` | **CLEAN** |



---



## 2. Codebase Discovery & Existing Primitives Audit



### 2.1 Backend Primitives Available for B2 Reuse



1. **Multi-Tenant Context & RBAC Middleware (`backend/middleware/business_context.py`):**

   - `@require_workspace(permission)` enforces `X-Workspace-Id` resolution, database membership verification, and 5-tier role validation (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`).

   - B2 capture and staging endpoints can reuse this decorator directly.

2. **Commercial Partner Registry (`backend/models/business/partner.py` & `PartnerService`):**

   - Provides Customer/Supplier registry with duplicate name detection and workspace scoping.

   - B2 entity disambiguation will resolve candidate counterparties directly against this table.

3. **Forensic Audit Service (`backend/services/business/audit_service.py`):**

   - Provides immutable, non-cascading `business_audit_events` emission for capture, extraction, edits, and human confirmation.

4. **AI Inference & Failover Pipeline (`backend/services/ai/provider.py` & `services/gemini_service.py`):**

   - Multi-tier provider abstraction: `OpenRouterAIProvider` $\rightarrow$ `GeminiAIProvider` $\rightarrow$ `DeterministicFallbackProvider`.

   - `AISafety.assert_prompt_safe` protects against direct prompt injection.

5. **Document Ingestion Drivers (`backend/services/document_service.py`):**

   - Existing drivers utilize `pypdf` for PDF parsing and `python-docx` for document parsing.

   - *Audit Finding:* Current Personal OS implementation directly parses files to create personal `Task` models in memory. B2 must decouple extraction from execution and route raw text/images to a staging entity.



### 2.2 Frontend Primitives Available for B2 Reuse



1. **Unified API Client (`frontend/src/api.ts`):**

   - Automatic `X-Workspace-Id` header injection from active session storage.

   - Centralized network error and retry handling.

2. **Workspace Switcher (`frontend/src/components/Business/WorkspaceSwitcher.tsx`):**

   - Reactive workspace switching emitting `deadline_workspace_changed`.

3. **Supabase Client (`frontend/src/lib/supabase.ts`):**

   - Configured client for Supabase Auth and Supabase Storage integration.



---



## 3. Gap Analysis for Phase B2 (Capture & Staging)



| Architectural Domain | Current Repository State | Required B2 Architecture | Gap Severity |

|---|---|---|:---:|

| **Raw Artifact Storage** | In-memory stream or ephemeral local disk (Render ephemeral storage risks data loss) | Object Storage Abstraction (Supabase Storage / S3 with signed upload/download URLs & SHA-256 fingerprinting) | **CRITICAL** |

| **Ingestion Entity Models** | None (only Personal OS transient task parsing exists) | `business_ingestion_artifacts` and `business_staged_extractions` with full field-level provenance | **CRITICAL** |

| **Staging State Machine** | None | 7-State lifecycle (`RECEIVED` $\rightarrow$ `PROCESSING` $\rightarrow$ `EXTRACTED` $\rightarrow$ `NEEDS_REVIEW` $\rightarrow$ `CONFIRMED` / `REJECTED` / `FAILED`) | **CRITICAL** |

| **Deterministic Normalizer** | None (LLM outputs unverified text) | Deterministic parser for INR numbers (`5k`, `1.2 lakh`, `₹5,000`), ISO dates, and phone/tax IDs | **HIGH** |

| **Entity Disambiguation** | None | Multi-tenant fuzzy/exact matcher against `CommercialPartner` with ambiguity detection | **HIGH** |

| **Human-in-the-Loop Barrier** | Personal OS auto-inserts tasks | Strict staging barrier: Zero ledger mutation without explicit human confirmation | **NORMATIVE (B0)** |

| **Review UI** | Personal OS task list | Split-screen Review Component with document/audio preview, confidence badges, and field editor | **HIGH** |



---



## 4. B0 Normative Compliance & Scope Isolation



### 4.1 Strict Phase Boundaries

- **B2 Scope:** Raw capture, object storage, AI extraction, deterministic normalization, partner disambiguation, staging lifecycle, human review & confirmation.

- **Excluded B3 Scope:** Double-entry ledger posting, invoice balance tracking, payment allocation, cash reality balance, runway calculations.

- **Excluded B4 Scope:** Business Copilot chatbot, natural-language ledger queries, proactive cash warnings.

- **Personal OS Isolation:** 100% untouched. All 162 Personal OS tests remain the mandatory regression baseline.



---



## 5. Security & Red-Team Audit Matrix (B2 Threat Analysis)



| Threat ID | Attack Vector | B2 Architectural Defense | Status |

|:---:|---|---|:---:|

| **T-B2-01** | Cross-tenant document download via predictable URL | Pre-signed URLs with 15-minute expiry + `@require_workspace` scoping | **PLANNED** |

| **T-B2-02** | Cross-tenant IDOR on staging extraction | All staging queries enforce `WHERE workspace_id = g.workspace_id` | **PLANNED** |

| **T-B2-03** | Prompt injection inside invoice PDF / OCR text | Text sanitized + extracted through strict JSON schema validation + Human review barrier | **PLANNED** |

| **T-B2-04** | Malicious MIME type or executable payload upload | Magic byte inspection, strict whitelist (`.pdf`, `.png`, `.jpeg`, `.mp3`, `.wav`, `.m4a`, `.txt`), size cap 15MB | **PLANNED** |

| **T-B2-05** | Duplicate document submission (Replay) | SHA-256 artifact hashing + duplicate warning within workspace | **PLANNED** |

| **T-B2-06** | Hallucinated AI financial amount | Deterministic Decimal regex parsing + Mandatory human confirmation barrier | **PLANNED** |

| **T-B2-07** | Ambiguous partner silent auto-assignment | Multi-match detection triggers `AMBIGUOUS_PARTNER` review flag | **PLANNED** |

| **T-B2-08** | Unauthorized confirmation by `VIEWER` role | `@require_workspace('staging:confirm')` restricts confirmation to `OWNER`, `ADMIN`, `MEMBER` | **PLANNED** |



---



## 6. Audit Verdict

```

B2 PASS 1 AUDIT COMPLETE — REPOSITORIES VERIFIED — PROCEED TO MASTER PLAN REVIEW

```
