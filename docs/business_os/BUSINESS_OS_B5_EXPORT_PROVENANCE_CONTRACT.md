# DEADLINEOS BUSINESS OS — B5 EXPORT PROVENANCE CONTRACT
**Document ID:** `B5-DOC-004`
**Status:** `BINDING SPECIFICATION`
**Classification:** Financial Export Integrity & Cryptographic Provenance

---

## 1. Accountant Export Package Structure

The accountant export package is returned as an in-memory ZIP archive containing:

```
accountant_package_<workspace_id>_<timestamp>.zip
├── manifest.json                  # Cryptographic SHA-256 checksums, metadata, filters
├── invoices_export.csv            # All invoices with subtotal, tax, discount, total, paid, balance
├── transactions_export.csv        # Append-only ledger transactions with settlement dates
├── payment_allocations_export.csv # Settlement allocation links
└── financial_summary.json         # Cash position, burn rate, and runway snapshot
```

---

## 2. Cryptographic Manifest Schema

```json
{
  "workspace_id": "ws-123",
  "generated_at": "2026-08-29T16:30:00Z",
  "generated_by_user_id": "usr-456",
  "filter_date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-08-29"
  },
  "file_checksums": {
    "invoices_export.csv": "sha256:...",
    "transactions_export.csv": "sha256:...",
    "payment_allocations_export.csv": "sha256:..."
  },
  "package_sha256": "sha256:..."
}
```
