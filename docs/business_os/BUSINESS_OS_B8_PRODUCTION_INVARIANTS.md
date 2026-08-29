# DEADLINEOS BUSINESS OS — B8 PRODUCTION INVARIANTS
**Document ID:** `B8-DOC-004`
**Status:** `BINDING SPECIFICATION`
**Classification:** Production & Security Hardening

---

## 1. Production Health Invariant

The `/api/business/health` diagnostic probe must return HTTP 200 with status `HEALTHY` when database and core services are operational, and must execute strictly in read-only mode without mutating application state.

---

## 2. Error Sanitization Invariant

All unhandled 500 exceptions in production must return structured JSON `{"status": "error", "error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred."}}` without exposing database names, SQL queries, or stack traces.
