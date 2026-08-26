# DEADLINEOS BUSINESS OS — DOMAIN ARCHITECTURE
**Document ID:** `B0-DOC-002`
**Status:** `B0 DESIGN DECISION`
**Classification:** Core Domain Architecture

---

## 1. Domain Overview & Bounded Contexts
Business OS is structured around five explicit Bounded Contexts, strictly separated from Personal OS:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BUSINESS OS BOUNDED CONTEXTS                             │
├──────────────────────────┬──────────────────────────┬────────────────────────────────────┤
│ 1. TENANCY & IDENTITY    │ 2. COMMERCIAL REGISTRY   │ 3. FINANCIAL LEDGER & OBLIGATIONS  │
│ - BusinessWorkspace      │ - Customer               │ - BusinessTransaction              │
│ - WorkspaceMember        │ - Supplier               │ - Invoice (Receivable / Payable)   │
│ - MemberRole / Perms     │ - CommercialContact      │ - PaymentRecord                    │
│                          │ - CommercialItem         │ - ObligationSchedule               │
├──────────────────────────┼──────────────────────────┴────────────────────────────────────┤
│ 4. CAPTURE & STAGING     │ 5. INTELLIGENCE & COPILOT                                     │
│ - IngestionArtifact      │ - BusinessRiskAssessment                                      │
│ - StagedExtraction       │ - BusinessMetricSnapshot                                      │
│ - ExtractionFieldReview  │ - CopilotContextSession                                       │
└──────────────────────────┴───────────────────────────────────────────────────────────────┘
```

---

## 2. Core Business Entities & Aggregates

### 2.1 Tenancy Aggregate
- **`BusinessWorkspace` (Root):** The commercial boundary. Owns all business entities, financial transactions, and configuration.
  - Attributes: `id`, `name`, `legal_name`, `tax_identifier` (e.g. GSTIN), `base_currency` (ISO 4217, e.g. `INR`), `timezone` (IANA, e.g. `Asia/Kolkata`), `status` (`ACTIVE`, `SUSPENDED`, `ARCHIVED`), `created_at`, `updated_at`.
- **`WorkspaceMember`:** Maps an individual user (`User.id` from Personal OS Auth) to a Workspace with a specific commercial role.
  - Attributes: `id`, `workspace_id`, `user_id`, `role` (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`), `status` (`ACTIVE`, `INVITED`, `DISABLED`), `joined_at`.

### 2.2 Commercial Entity Registry Aggregate
- **`Customer` / `Supplier` (`CommercialPartner`):**
  - Attributes: `id`, `workspace_id`, `type` (`CUSTOMER`, `SUPPLIER`, `DUAL`), `name`, `legal_name`, `phone`, `email`, `tax_id`, `credit_period_days` (default 30), `current_receivable_balance` (derived), `current_payable_balance` (derived), `created_at`.
- **`CommercialItem` (Product / Service Definition):**
  - Attributes: `id`, `workspace_id`, `name`, `sku`, `unit_price`, `tax_rate_percent`, `unit_of_measure` (`HOURS`, `UNITS`, `PROJECT`).

### 2.3 Financial Transaction & Ledger Aggregate
- **`BusinessTransaction`:** The atomic financial record.
  - Attributes: `id`, `workspace_id`, `transaction_type` (`INCOME`, `EXPENSE`, `TRANSFER`, `ADJUSTMENT`), `status` (`CONFIRMED`, `REVERSED`, `CORRECTED`), `amount` (`Numeric(15, 2)`), `currency` (`String(3)`), `transaction_date` (UTC timestamp), `partner_id` (`Nullable ForeignKey`), `payment_method` (`BANK_TRANSFER`, `UPI`, `CASH`, `CARD`, `CHEQUE`), `reference_number`, `description`, `created_by_user_id`, `created_at`.
- **`Invoice` (Receivable / Payable Contract):**
  - Attributes: `id`, `workspace_id`, `direction` (`RECEIVABLE_OUTBOUND`, `PAYABLE_INBOUND`), `invoice_number`, `partner_id`, `issue_date`, `due_date`, `subtotal`, `tax_amount`, `total_amount`, `paid_amount`, `balance_due`, `status` (`DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELLED`, `DISPUTED`), `source_artifact_id`.

### 2.4 Ingestion & Staging Aggregate (Human-in-the-Loop Barrier)
- **`IngestionArtifact`:** Stores raw uploaded documents or audio.
  - Attributes: `id`, `workspace_id`, `file_storage_uri`, `file_mime_type`, `file_hash_sha256`, `capture_source` (`DOCUMENT_UPLOAD`, `WHATSAPP_FORWARD`, `VOICE_NOTE`, `MANUAL_ENTRY`), `status` (`UPLOADED`, `EXTRACTING`, `STAGED`, `CONFIRMED`, `REJECTED`).
- **`StagedExtraction`:** Contains AI-extracted candidates prior to user confirmation.
  - Attributes: `id`, `artifact_id`, `workspace_id`, `target_entity_type` (`INVOICE`, `EXPENSE`, `RECEIVABLE`, `PAYABLE`), `raw_ai_payload` (`JSON`), `normalized_payload` (`JSON`), `overall_confidence` (`Integer 0-100`), `ambiguity_flags` (`JSON`), `review_status` (`PENDING_REVIEW`, `CONFIRMED`, `REJECTED`), `reviewed_by_user_id`, `reviewed_at`.

---

## 3. Domain Entity Relationships

```
                     ┌──────────────────┐
                     │ BusinessWorkspace│
                     └─────────┬────────┘
                               │ 1:N
        ┌──────────────────────┼───────────────────────┐
        ▼                      ▼                       ▼
┌───────────────┐      ┌───────────────┐       ┌───────────────┐
│WorkspaceMember│      │CommercialPrtnr│       │IngestionArtfct│
└───────┬───────┘      └───────┬───────┘       └───────┬───────┘
        │                      │ 1:N                   │ 1:1
        │                      ▼                       ▼
        │              ┌───────────────┐       ┌───────────────┐
        │              │    Invoice    │◄──────┤StagedExtractn │
        │              └───────┬───────┘       └───────────────┘
        │                      │ 1:N (Settlements)
        │                      ▼
        │              ┌───────────────┐
        └─────────────►│BusinessTransct│
                       └───────────────┘
```

---

## 4. Architectural Domain Invariants
1. **Workspace Boundary Invariant:** Every domain repository and database query MUST filter by `workspace_id`. Cross-workspace querying is strictly prohibited at the database and service levels.
2. **Financial Precision Invariant:** All monetary amounts MUST use exact decimal arithmetic (`Numeric(15, 2)` / Python `Decimal`). Floating-point arithmetic (`float`) is banned in the business domain.
3. **No Direct Probabilistic Mutation:** An AI extraction from a document, image, or voice recording CANNOT create a `BusinessTransaction` or `Invoice` directly; it MUST pass through `StagedExtraction` and require human confirmation.
4. **Historical Immutability Invariant:** Confirmed `BusinessTransaction` records CANNOT be deleted or overwritten with in-place updates. Corrections MUST be recorded as adjustment transactions or explicitly flagged reversals.
