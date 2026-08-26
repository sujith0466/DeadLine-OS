# DEADLINEOS BUSINESS OS — DATA ARCHITECTURE & SCHEMA DESIGN
**Document ID:** `B0-DOC-008`
**Status:** `B0 ARCHITECTURAL SPECIFICATION`
**Classification:** Database Architecture (PostgreSQL)

---

## 1. Schema Namespacing & Migration Strategy
All Business OS tables are created within the existing PostgreSQL database using forward-only Alembic migrations (e.g. `d1a..._business_os_foundation.py`), prefixed with `business_` to guarantee zero collision with frozen Personal OS tables.

---

## 2. Table Definitions & Constraints

### 2.1 `business_workspaces`
```sql
CREATE TABLE business_workspaces (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    tax_identifier VARCHAR(50),
    base_currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'SUSPENDED', 'ARCHIVED', 'DELETED'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_biz_workspaces_status ON business_workspaces(status);
```

### 2.2 `business_workspace_members`
```sql
CREATE TABLE business_workspace_members (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'MEMBER', -- 'OWNER', 'ADMIN', 'MEMBER', 'ACCOUNTANT', 'VIEWER'
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, user_id)
);
CREATE INDEX ix_biz_members_ws_user ON business_workspace_members(workspace_id, user_id);
```

### 2.3 `business_commercial_partners`
```sql
CREATE TABLE business_commercial_partners (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    partner_type VARCHAR(20) NOT NULL, -- 'CUSTOMER', 'SUPPLIER', 'DUAL'
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    tax_id VARCHAR(50),
    credit_period_days INTEGER NOT NULL DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_biz_partners_ws_type ON business_commercial_partners(workspace_id, partner_type);
```

### 2.4 `business_invoices`
```sql
CREATE TABLE business_invoices (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    direction VARCHAR(20) NOT NULL, -- 'RECEIVABLE_OUTBOUND', 'PAYABLE_INBOUND'
    invoice_number VARCHAR(100) NOT NULL,
    partner_id VARCHAR(36) NOT NULL REFERENCES business_commercial_partners(id),
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    subtotal NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    tax_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00, -- Frozen upon issuance: subtotal + tax_amount - discount_amount
    paid_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00, -- Cached derived state
    balance_due NUMERIC(15, 2) NOT NULL DEFAULT 0.00, -- Cached derived state
    status VARCHAR(20) NOT NULL DEFAULT 'ISSUED', -- 'DRAFT', 'ISSUED', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'CANCELLED', 'DISPUTED'
    notes TEXT,
    created_by_user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_biz_inv_math CHECK (subtotal >= 0 AND tax_amount >= 0 AND discount_amount >= 0 AND total_amount >= 0)
);
CREATE INDEX ix_biz_invoices_ws_status_due ON business_invoices(workspace_id, status, due_date);
```

### 2.5 `business_transactions` & `business_payment_allocations`
```sql
CREATE TABLE business_transactions (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL, -- 'INCOME', 'EXPENSE', 'TRANSFER', 'ADJUSTMENT'
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED', -- 'CONFIRMED', 'REVERSED'
    amount NUMERIC(15, 2) NOT NULL, -- Immutable financial fact
    currency VARCHAR(3) NOT NULL DEFAULT 'INR', -- Immutable financial fact
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL, -- Immutable financial fact
    partner_id VARCHAR(36) REFERENCES business_commercial_partners(id), -- Immutable financial fact
    payment_method VARCHAR(50) NOT NULL DEFAULT 'BANK_TRANSFER',
    reference_number VARCHAR(100),
    description TEXT,
    reversal_of_transaction_id VARCHAR(36) REFERENCES business_transactions(id),
    created_by_user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_biz_tx_ws_date ON business_transactions(workspace_id, transaction_date DESC);

CREATE TABLE business_payment_allocations (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    transaction_id VARCHAR(36) NOT NULL REFERENCES business_transactions(id),
    invoice_id VARCHAR(36) NOT NULL REFERENCES business_invoices(id),
    allocated_amount NUMERIC(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'REVERSED'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_biz_allocations_tx_inv ON business_payment_allocations(transaction_id, invoice_id);
```

### 2.6 `business_ingestion_artifacts` & `business_staged_extractions`
```sql
CREATE TABLE business_ingestion_artifacts (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    file_storage_uri VARCHAR(512) NOT NULL,
    file_mime_type VARCHAR(100) NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL,
    capture_source VARCHAR(50) NOT NULL, -- 'DOCUMENT_UPLOAD', 'VOICE_NOTE', 'MANUAL_ENTRY'
    status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
    created_by_user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE business_staged_extractions (
    id VARCHAR(36) PRIMARY KEY,
    artifact_id VARCHAR(36) NOT NULL REFERENCES business_ingestion_artifacts(id) ON DELETE CASCADE,
    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,
    target_entity_type VARCHAR(50) NOT NULL, -- 'INVOICE', 'EXPENSE', 'PAYMENT'
    raw_ai_payload JSONB NOT NULL,
    normalized_payload JSONB NOT NULL,
    overall_confidence INTEGER NOT NULL DEFAULT 0,
    ambiguity_flags JSONB,
    review_status VARCHAR(20) NOT NULL DEFAULT 'PENDING_REVIEW', -- 'PENDING_REVIEW', 'CONFIRMED', 'REJECTED'
    reviewed_by_user_id VARCHAR(36) REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_biz_staged_ws_status ON business_staged_extractions(workspace_id, review_status);
```

### 2.7 `business_audit_events` (Non-Cascading Permanent Audit Log)
```sql
CREATE TABLE business_audit_events (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL, -- Logical reference; no cascading delete
    actor_user_id VARCHAR(36) NOT NULL, -- Logical reference
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    before_state JSONB,
    after_state JSONB,
    reason TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_biz_audit_ws_entity ON business_audit_events(workspace_id, entity_type, entity_id);
```
