# DEADLINEOS BUSINESS OS — AI & COPILOT ARCHITECTURE
**Document ID:** `B0-DOC-005`
**Status:** `B0 DESIGN DECISION`
**Classification:** Artificial Intelligence Architecture

---

## 1. Hybrid AI Provider Utilization (Platform Reuse)
Business OS directly reuses the certified **Hybrid Failover AI Provider** (`backend/services/ai/provider.py`):

$$\text{OpenRouter (Primary)} \longrightarrow \text{Gemini 2.0 Flash (Fallback)} \longrightarrow \text{Deterministic Heuristics (Safe Degradation)}$$

- **Primary:** `meta-llama/llama-3.3-70b-instruct:free` or specified model via OpenRouter API.
- **Fallback:** Google Gemini 2.0 Flash (`google-generativeai`).
- **Offline / Emergency Mode:** Deterministic Rule Engine producing schema-valid baseline summaries without external LLM calls.

---

## 2. The Deterministic vs. AI Separation Boundary

```
┌───────────────────────────────────────────────┬──────────────────────────────────────────────┐
│        AI RESPONSIBILITIES (Advisory)         │    DETERMINISTIC RESPONSIBILITIES (Authority)│
├───────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ 1. Document / OCR text parsing                │ 1. Arithmetic totals, subtotals, tax math    │
│ 2. Intent extraction from voice & text        │ 2. Ledger balance mutations & adjustments    │
│ 3. Semantic entity matching suggestions       │ 3. Role-based authorization & tenancy checks │
│ 4. Executive narrative generation             │ 4. State transitions (DRAFT $\rightarrow$ CONFIRMED) │
│ 5. Draft reminder message synthesis           │ 5. Transaction reversal & audit logging      │
│ 6. Predictive cash risk hypotheses            │ 6. Recurrence expansion & calendar mapping   │
└───────────────────────────────────────────────┴──────────────────────────────────────────────┘
```

**Golden Architectural Rule:**
> *"No AI model output is ever allowed to directly execute a database write to `business_transactions`, `invoices`, or `commercial_partners` without passing through deterministic schema validation, deterministic business rule checks, and mandatory human confirmation."*

---

## 3. Human-in-the-Loop Capture & Staging Workflow

```
 [Raw Input: PDF Invoice / Audio / WhatsApp text]
                       │
                       ▼
 ┌───────────────────────────────────────────────┐
 │ 1. Ingestion Pipeline (`IngestionArtifact`)   │
 └─────────────────────┬─────────────────────────┘
                       │
                       ▼
 ┌───────────────────────────────────────────────┐
 │ 2. AI Extraction (`StagedExtraction`)         │
 │    - Extracts fields (Vendor, Total, Due Date)│
 │    - Calculates confidence score (0-100)      │
 └─────────────────────┬─────────────────────────┘
                       │
                       ▼
 ┌───────────────────────────────────────────────┐
 │ 3. Deterministic Field Validation             │
 │    - Validates Math: Subtotal + Tax == Total  │
 │    - Validates Dates: DueDate >= IssueDate    │
 │    - Normalizes Currencies via `parse_money`  │
 └─────────────────────┬─────────────────────────┘
                       │
                       ▼
 ┌───────────────────────────────────────────────┐
 │ 4. UI Staging & Human Review Modal            │
 │    - User inspects extracted draft fields     │
 │    - Resolves ambiguities / Edits mistakes    │
 └─────────────────────┬─────────────────────────┘
                       │
        [User Clicks "Confirm & Record"]
                       │
                       ▼
 ┌───────────────────────────────────────────────┐
 │ 5. Authoritative Commit                       │
 │    - Creates `Invoice` / `BusinessTransaction`│
 │    - Emits `INVOICE_RECORDED` Domain Event    │
 └───────────────────────────────────────────────┘
```

---

## 4. Business Copilot Security & Context Scoping
The Business Copilot allows natural language questions (e.g. *"Who owes us money this week?"*, *"What are my top expenses this month?"*).

### 4.1 Zero-Bypass Security Pipeline
Copilot NEVER connects directly to the raw database or unfiltered LLM prompts:

```
 User Prompt ("Show me invoices due this week")
                      │
                      ▼
 ┌───────────────────────────────────────────────┐
 │ 1. Authentication & Workspace Scope Check     │  (`g.user_id`, `g.workspace_id`)
 └────────────────────┬──────────────────────────┘
                      │
                      ▼
 ┌───────────────────────────────────────────────┐
 │ 2. RBAC Permission Filtering                  │  Validates `copilot:financial_q`
 └────────────────────┬──────────────────────────┘
                      │
                      ▼
 ┌───────────────────────────────────────────────┐
 │ 3. Deterministic Data Retrieval               │  Queries repository:
 │                                               │  `get_invoices_due(ws_id, start, end)`
 └────────────────────┬──────────────────────────┘
                      │
                      ▼
 ┌───────────────────────────────────────────────┐
 │ 4. Grounded Context Construction              │  Injects ONLY verified DB records
 └────────────────────┬──────────────────────────┘
                      │
                      ▼
 ┌───────────────────────────────────────────────┐
 │ 5. LLM Synthesis & Schema Validation          │  Generates grounded natural answer
 └───────────────────────────────────────────────┘
```
