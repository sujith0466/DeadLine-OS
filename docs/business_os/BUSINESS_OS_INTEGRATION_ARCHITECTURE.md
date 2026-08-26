# DEADLINEOS BUSINESS OS — INTEGRATION ARCHITECTURE
**Document ID:** `B0-DOC-010`
**Status:** `B0 DESIGN DECISION`
**Classification:** Systems Integration Architecture

---

## 1. Personal OS ↔ Business OS Integration Principles
1. **Preservation of Frozen Personal Baseline:** Personal OS models (`Task`, `Goal`, `Habit`, `ScheduleSlot`) are NEVER modified to include Business OS columns.
2. **Read-Only / Polymorphic Bridge Adapters:** Business OS projects operational obligations into Personal OS views via domain adapters:

```
┌─────────────────────────────────────────────────────────────┐
│                       BUSINESS OS DOMAIN                    │
│   - `Invoice` (Due: 2026-09-02, Amount: ₹50,000)            │
│   - `BusinessObligation` (Supplier Payment Due: 2026-09-01) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (Adapter Layer)
┌─────────────────────────────────────────────────────────────┐
│                    CROSS-DOMAIN BRIDGE ADAPTER              │
│   - `BusinessToPersonalAdapter.sync_due_obligations()`      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (Platform Primitive)
┌─────────────────────────────────────────────────────────────┐
│                       PERSONAL OS / TODAY                   │
│   - Creates virtual or linked ScheduleSlot:                 │
│     `entity_type="BUSINESS_INVOICE"`, `entity_id="inv_..."` │
│     `task_title="Collect ₹50,000 from Ravi Enterprises"`    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Platform Infrastructure Reuse Summary

| Platform Component | Location in Codebase | Reuse Modality |
|---|---|---|
| **AI Provider Gateway** | `backend/services/ai/provider.py` | Direct platform reuse via `get_default_ai_provider()` |
| **AI Safety Validator** | `backend/services/ai/safety.py` | Direct platform reuse with business-specific JSON schemas |
| **Timezone Normalizer** | `backend/utils/timezone.py` | Direct reuse for UTC database conversions and workspace local presentations |
| **Blinker Event Bus** | `backend/services/runtime/event_bus.py` | Namespaced extension (`business_signals = Namespace()`) |
| **Error Handling** | `backend/utils/errors.py` | Shared `APIError` and standard JSON error response envelopes |
| **Telemetry Logger** | `backend/services/telemetry_service.py` | Logs business agent inference and performance |

---

## 3. External Accounting & Export Interoperability
- **CSV / Excel Stream Exports:** Deterministic data exporters generating standard ledger summaries, receivable aging sheets, and expense categorization.
- **Accountant Audit Package:** Exports a complete zip archive containing all confirmed invoices (PDFs), settlement receipts, and a verified transaction ledger matching exact totals.
- **Tally XML / JSON Bridge (Phase B2+):** Prepares standard `<ENVELOPE>` Tally XML format for sales and purchase vouchers without requiring custom local accounting plugins.
