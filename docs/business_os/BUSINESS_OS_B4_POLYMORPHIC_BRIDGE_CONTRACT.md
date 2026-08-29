# DEADLINEOS BUSINESS OS — B4 POLYMORPHIC BRIDGE CONTRACT
**Document ID:** `B4-DOC-005`
**Status:** `BINDING INTEGRATION SPECIFICATION`
**Classification:** Cross-Domain Architecture

---

## 1. Cross-Domain Projection Schema

The Polymorphic Bridge exposes virtual obligations using the following read-only projection schema:

```json
{
  "id": "virt-inv-<invoice_id>",
  "source_domain": "BUSINESS_OS",
  "entity_type": "INVOICE_RECEIVABLE",
  "title": "Collect ₹50,000 from Ravi Enterprises",
  "due_date": "2026-09-15",
  "urgency": "HIGH",
  "amount": "50000.00",
  "currency": "INR",
  "workspace_id": "ws-123",
  "action_url": "/business/invoices/inv-456"
}
```

---

## 2. Non-Contamination Invariant

- No foreign keys linking Personal OS tables to Business OS tables.
- Querying the unified feed performs on-the-fly aggregation without persisting duplicate records.
