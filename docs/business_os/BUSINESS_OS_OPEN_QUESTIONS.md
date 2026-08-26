# DEADLINEOS BUSINESS OS — OPEN QUESTIONS REGISTER
**Document ID:** `B0-DOC-016`
**Status:** `B0 DESIGN DECISION`
**Classification:** Architectural Governance

---

## 1. Active Open Questions

| Q ID | Architecture Question | Why It Matters | Current Options | Recommended B0 Decision | Blocking B1? |
|---|---|---|---|---|:---:|
| **`OPN-001`** | **Cloud Storage Provider Selection:** Should we use Supabase Storage or an AWS S3 bucket? | Document persistence on ephemeral Render containers. | A) Supabase Storage (already configured credentials).<br>B) AWS S3 (requires new IAM setup). | **Option A (Supabase Storage):** Zero new infrastructure dependencies; reuses existing Supabase project keys. | **NO (Resolved for B1)** |
| **`OPN-002`** | **Workspace Context Transport:** Should `workspace_id` be passed via HTTP Header (`X-Workspace-Id`) or URL prefix (`/api/business/:ws_id/...`)? | API ergonomics, frontend caching, and middleware consistency. | A) HTTP Header `X-Workspace-Id`.<br>B) URL path parameter. | **Option A (HTTP Header):** Keeps API routes clean and allows transparent Axios interceptor injection. | **NO (Resolved for B1)** |
| **`OPN-003`** | **Tally Export Format Compatibility:** Should MVP generate raw CSV or strict Tally XML? | Usability for Indian accountants. | A) CSV standard ledger.<br>B) Complete Tally XML `<ENVELOPE>`. | **Option A for B1 MVP; Option B for B2:** Start with 100% compliant CSV; add XML generator in B2. | **NO (Resolved for B1)** |
| **`OPN-004`** | **Async Concurrency Evolution:** When should Eventlet be migrated to ASGI (Uvicorn)? | Eventlet deprecation warnings on Python 3.13. | A) Immediate migration in B1.<br>B) Deferred migration in B8. | **Option B (Deferred to B8):** Keep the live, certified production deployment completely stable during initial B1–B7 business feature delivery. | **NO (Resolved for B1)** |
