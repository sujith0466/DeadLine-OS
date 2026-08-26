# DEADLINEOS BUSINESS OS — EVENT & OUTBOX ARCHITECTURE
**Document ID:** `B0-DOC-006`
**Status:** `B0 DESIGN DECISION`
**Classification:** Event & Messaging Architecture

---

## 1. Event Classification Taxonomy
Business OS defines three distinct tiers of events:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DOMAIN EVENTS (`BusinessDomainEvent`)                                                │
│    - Signals state changes within the business context                                  │
│    - Examples: `INVOICE_ISSUED`, `PAYMENT_RECEIVED`, `OBLIGATION_OVERDUE`               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. TRANSACTIONAL OUTBOX EVENTS (`BusinessOutboxEvent`)                                  │
│    - Persisted in the SAME database transaction as the business entity                  │
│    - Guarantees at-least-once delivery to async handlers without distributed locks      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. IMMUTABLE AUDIT EVENTS (`BusinessAuditEvent`)                                        │
│    - Permanent, append-only operational log recording actor, IP, action, diff & reason  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Business Event Catalog

| Event Name | Aggregate | Trigger Condition | Downstream Actions |
|---|---|---|---|
| `WORKSPACE_CREATED` | Workspace | Owner establishes new commercial workspace | Provision default settings, emit audit log |
| `PARTNER_CREATED` | Registry | New Customer/Supplier added | Index search vector, emit audit log |
| `INVOICE_ISSUED` | Invoice | Outbound invoice confirmed and sent | Create receivable obligation, map to Calendar |
| `PAYMENT_RECORDED` | Ledger | Inbound/outbound payment confirmed | Update invoice balance, adjust cash runway |
| `PAYMENT_REVERSED` | Ledger | Correction transaction confirmed | Re-open invoice balance, emit critical audit |
| `EXTRACTION_STAGED` | Capture | AI parses invoice/receipt draft | Send notification to reviewer |
| `OBLIGATION_OVERDUE`| Risk | Due date passes without settlement | Trigger Business Risk Engine alert |

---

## 3. Transactional Outbox Pattern Flow

```
 Application Service (e.g. `InvoiceService.issue_invoice`)
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 1. Single Database Transaction                              │
 │    - `db.session.add(invoice)`                              │
 │    - `db.session.add(BusinessOutboxEvent(event_type=...))`  │
 │    - `db.session.add(BusinessAuditEvent(...))`              │
 │    - `db.session.commit()`                                  │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼ (Committed in PostgreSQL)
 ┌─────────────────────────────────────────────────────────────┐
 │ 2. Outbox Dispatcher (`BusinessOutboxDispatcher`)           │
 │    - Polled periodically / triggered on commit              │
 │    - Queries `WHERE dispatched = FALSE ORDER BY id ASC`     │
 │    - Dispatches to Blinker signals safely                   │
 │    - Marks `dispatched = TRUE` upon successful execution    │
 └─────────────────────────────────────────────────────────────┘
```

---

## 4. Idempotency & Delivery Guarantees
1. **Idempotency Keys:** All transactional API requests require an `Idempotency-Key` header. Duplicate submissions within 24 hours return the cached response without re-executing transactions.
2. **Deterministic Re-delivery Handling:** Event consumers MUST be idempotent. If an event is re-dispatched, handlers verify entity state before mutating derived records.
