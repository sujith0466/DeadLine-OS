# DEADLINEOS BUSINESS OS — B3 MASTER IMPLEMENTATION PLAN

**Document ID:** `B3-DOC-002`

**Status:** `MASTER PLAN DRAFTED / PENDING PASS 2 REVIEW`

**Classification:** Financial Ledger & Invoicing Architecture

**Author:** DeadlineOS Principal Architect & Financial Systems Lead

**Date:** 2026-08-29T16:10:00+05:30



---



## 1. Product Scope & Architectural Objectives



Phase B3 implements the foundational financial layer of DeadlineOS Business OS. It enables small businesses, freelancers, and agencies to track customer receivables, vendor bills, payments, and true operational runway with mathematical certainty.



### Core Objectives:

1. **Invoice Lifecycle Management:** Draft, issue, freeze, and track settlement of customer and vendor invoices.

2. **Operational Financial Event Ledger:** Immutable, append-only ledger of inbound, outbound, and adjustment money movements.

3. **Multi-Invoice Payment Allocation:** Allocate single or batch payments to outstanding invoices with balance recalculation.

4. **Append-Only Reversal Protocol:** Non-destructive corrections using counter-adjustment transactions and audit logging.

5. **Cash Reality & Deterministic Runway:** Implement the 4-tier Cash Reality hierarchy and 5-tier deterministic Runway Days formula.

6. **B2 $\rightarrow$ B3 Financial Gateway:** Bridge human-confirmed staging extractions to invoices or ledger transactions.



---



## 2. Domain Entities & Database Schema Design



### 2.1 Table: `business_invoices`

Stores customer (receivable) and supplier (payable) invoices.



```sql

CREATE TABLE business_invoices (

    id VARCHAR(36) PRIMARY KEY,

    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,

    invoice_number VARCHAR(50) NOT NULL,

    invoice_type VARCHAR(20) NOT NULL DEFAULT 'RECEIVABLE', -- RECEIVABLE, PAYABLE

    partner_id VARCHAR(36) REFERENCES business_commercial_partners(id) ON DELETE SET NULL,

    issue_date DATE NOT NULL,

    due_date DATE NOT NULL,

    currency VARCHAR(3) NOT NULL DEFAULT 'INR',

    subtotal NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    tax_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    discount_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    total_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    paid_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    balance_due NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', -- DRAFT, ISSUED, PARTIALLY_PAID, PAID, OVERDUE, VOID

    notes TEXT,

    created_by_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    staged_extraction_id VARCHAR(36) REFERENCES business_staged_extractions(id) ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_biz_inv_math CHECK (

        subtotal >= 0 AND tax_amount >= 0 AND discount_amount >= 0 AND total_amount >= 0 AND

        discount_amount <= (subtotal + tax_amount) AND

        paid_amount >= 0 AND balance_due >= 0 AND

        (paid_amount + balance_due = total_amount)

    )

);

CREATE UNIQUE INDEX uq_biz_inv_ws_num ON business_invoices(workspace_id, invoice_number);

CREATE INDEX idx_biz_inv_ws_status ON business_invoices(workspace_id, status);

CREATE INDEX idx_biz_inv_partner ON business_invoices(partner_id);

```



### 2.2 Table: `business_invoice_items`

Line-item breakdown for invoices.



```sql

CREATE TABLE business_invoice_items (

    id VARCHAR(36) PRIMARY KEY,

    invoice_id VARCHAR(36) NOT NULL REFERENCES business_invoices(id) ON DELETE CASCADE,

    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,

    description VARCHAR(255) NOT NULL,

    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00,

    unit_price NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx_biz_inv_items_inv ON business_invoice_items(invoice_id);

```



### 2.3 Table: `business_transactions`

Authoritative historical event ledger.



```sql

CREATE TABLE business_transactions (

    id VARCHAR(36) PRIMARY KEY,

    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,

    transaction_type VARCHAR(20) NOT NULL, -- INCOME, EXPENSE, TRANSFER, ADJUSTMENT

    amount NUMERIC(15, 2) NOT NULL,

    currency VARCHAR(3) NOT NULL DEFAULT 'INR',

    transaction_date DATE NOT NULL,

    settlement_date DATE,

    partner_id VARCHAR(36) REFERENCES business_commercial_partners(id) ON DELETE SET NULL,

    payment_method VARCHAR(50), -- BANK_TRANSFER, UPI, CARD, CASH, CHEQUE

    reference_number VARCHAR(100),

    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED', -- CONFIRMED, REVERSED

    reversal_of_transaction_id VARCHAR(36) REFERENCES business_transactions(id) ON DELETE SET NULL,

    created_by_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    staged_extraction_id VARCHAR(36) REFERENCES business_staged_extractions(id) ON DELETE SET NULL,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx_biz_tx_ws_date ON business_transactions(workspace_id, transaction_date);

CREATE INDEX idx_biz_tx_ws_status ON business_transactions(workspace_id, status);

CREATE INDEX idx_biz_tx_partner ON business_transactions(partner_id);

```



### 2.4 Table: `business_payment_allocations`

Settlement links between transactions and invoices.



```sql

CREATE TABLE business_payment_allocations (

    id VARCHAR(36) PRIMARY KEY,

    workspace_id VARCHAR(36) NOT NULL REFERENCES business_workspaces(id) ON DELETE CASCADE,

    transaction_id VARCHAR(36) NOT NULL REFERENCES business_transactions(id) ON DELETE CASCADE,

    invoice_id VARCHAR(36) NOT NULL REFERENCES business_invoices(id) ON DELETE CASCADE,

    allocated_amount NUMERIC(15, 2) NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, REVERSED

    allocated_by_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_biz_alloc_amount CHECK (allocated_amount > 0)

);

CREATE INDEX idx_biz_alloc_tx ON business_payment_allocations(transaction_id);

CREATE INDEX idx_biz_alloc_inv ON business_payment_allocations(invoice_id);

```



---



## 3. Financial Services & Arithmetic Engines



### 3.1 `InvoiceService`

- `create_invoice(workspace_id, user_id, data)`: Computes subtotal, tax, discount, total, balance_due using exact Decimal. Generates sequential invoice number. Status = `DRAFT`.

- `issue_invoice(workspace_id, invoice_id, user_id)`: Transitions `DRAFT` $\rightarrow$ `ISSUED`. Freezes total arithmetic.

- `void_invoice(workspace_id, invoice_id, user_id, reason)`: Only allowed if `paid_amount == 0.00`. Transitions `ISSUED` $\rightarrow$ `VOID`.

- `recalculate_invoice_balance(workspace_id, invoice_id)`: Computes `paid_amount = sum(active allocations)` and `balance_due = total - paid`. Updates status (`PARTIALLY_PAID`, `PAID`, `ISSUED`, `OVERDUE`).



### 3.2 `TransactionService`

- `record_transaction(workspace_id, user_id, data)`: Ingestion of money movement. Status = `CONFIRMED`.

- `reverse_transaction(workspace_id, transaction_id, user_id, reason)`:

  - Generates counter-adjustment transaction (`ADJUSTMENT` with `-original.amount`).

  - Sets original status to `REVERSED`.

  - Reverses linked allocations and recalculates invoice balances.

  - Logs `TRANSACTION_REVERSED` audit event.



### 3.3 `AllocationService`

- `allocate_payment(workspace_id, user_id, transaction_id, allocations)`:

  - Asserts sum of allocations $\le$ transaction unallocated amount.

  - For each invoice: asserts allocation $\le$ invoice `balance_due`.

  - Inserts `PaymentAllocation` records and triggers `recalculate_invoice_balance`.



### 3.4 `FinancialTruthService` (Cash & Runway)

- `get_cash_position(workspace_id)`:

  - `Confirmed Cash`: $\sum$ settled non-reversed transactions.

  - `Committed Inflows`: $\sum$ unpaid receivables due in window (default 30 days).

  - `Committed Outflows`: $\sum$ unpaid payables due in window (default 30 days).

  - `Projected Position`: Confirmed Cash + Inflows - Outflows.

- `calculate_runway_days(workspace_id)`:

  - Evaluates 5-tier deterministic precedence:

    1. `RUNWAY_NEGATIVE` (Confirmed Cash $\le 0.00$)

    2. `RUNWAY_STALE` (Last transaction $> 7$ days ago)

    3. `RUNWAY_INSUFFICIENT_HISTORY` (Age $< 14$ days and payables == 0)

    4. `RUNWAY_ZERO_BURN` (Confirmed Cash $> 0$ and $\text{ADBR}_{30} == 0$)

    5. `CALCULATED` ($\lfloor \text{Confirmed Cash} / \text{ADBR}_{30} \rfloor$)



---



## 4. API Endpoints



### 4.1 Invoices (`/api/business/invoices`)

- `GET /api/business/invoices` (`transaction:read`)

- `POST /api/business/invoices` (`transaction:create`)

- `GET /api/business/invoices/<id>` (`transaction:read`)

- `PATCH /api/business/invoices/<id>` (`transaction:create`)

- `POST /api/business/invoices/<id>/issue` (`transaction:create`)

- `POST /api/business/invoices/<id>/void` (`transaction:reverse`)



### 4.2 Transactions (`/api/business/transactions`)

- `GET /api/business/transactions` (`transaction:read`)

- `POST /api/business/transactions` (`transaction:create`)

- `GET /api/business/transactions/<id>` (`transaction:read`)

- `POST /api/business/transactions/<id>/reverse` (`transaction:reverse`)



### 4.3 Allocations & Financial Dashboard (`/api/business/allocations`, `/api/business/financial`)

- `POST /api/business/allocations` (`transaction:create`)

- `GET /api/business/financial/cash-position` (`transaction:read`)

- `GET /api/business/financial/runway` (`transaction:read`)



---



## 5. Milestone Execution Sequence (`B3.0` $\rightarrow$ `B3.8`)



- **B3.0:** Readiness & Branch Setup (`feature/b3-ledger-invoicing`).

- **B3.1:** Database Models (`Invoice`, `InvoiceLineItem`, `BusinessTransaction`, `PaymentAllocation`) & Alembic Migration `f3c4d5e6f7a8_business_os_ledger_invoicing.py`.

- **B3.2:** Invoice Domain & Calculation Engine (`InvoiceService`).

- **B3.3:** Operational Ledger & Reversal Engine (`TransactionService`).

- **B3.4:** Payment Allocation & Settlement Engine (`AllocationService`).

- **B3.5:** Cash Reality & Deterministic Runway Engine (`FinancialTruthService`).

- **B3.6:** B2 $\rightarrow$ B3 Staging Financial Converter & API Layer.

- **B3.7:** Automated Security & Financial Integrity Test Suites.

- **B3.8:** Full Regression Gate, Release Certification & Tagging (`business-os-b3-certified`).