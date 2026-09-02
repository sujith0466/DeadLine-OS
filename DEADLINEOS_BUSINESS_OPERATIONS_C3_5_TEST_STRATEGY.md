# DEADLINEOS BUSINESS OPERATIONS — PHASE C3.5 TEST STRATEGY
**Milestone:** C3.5 — Cross-Border Supply Chain Operations Hub & Copilot Grounding
**Mode:** Quality Assurance & Verification Architecture
**Date:** 2026-09-02T15:14:00+05:30
**Baseline Commit:** `d849c0d`

---

## 1. Test Layer Architecture

| Test Layer | Framework / Target | Target Gate |
| :--- | :--- | :--- |
| **Migration Verification** | `pytest tests/test_migration_chain_verification.py` | 100% PASS (11/11) |
| **Dedicated Unit & Service Tests** | `pytest tests/test_business_cross_border.py` | 100% PASS |
| **Live Neon PostgreSQL E2E** | `python scratch/e2e_c3_5_live.py` (E2E-1 through E2E-19) | 100% PASS (19/19) |
| **Full Backend Regression** | `pytest tests/ -k "not test_gemini" -q` | 100% PASS (385+ tests) |
| **Frontend Production Build** | `npm --prefix frontend run build` | 0 errors |
| **Personal OS Protected Files** | `git diff -- <7 protected files>` | 0 bytes diff |

---

## 2. Dedicated Unit & Service Test Scenarios (`test_business_cross_border.py`)

1. `test_shipment_creation_and_defaults`: Creates cross-border shipment, validates status machine defaults.
2. `test_shipment_state_transitions`: Validates state machine (`PLANNED` $\rightarrow$ `BOOKED` $\rightarrow$ `IN_TRANSIT` $\rightarrow$ `CUSTOMS_HOLD` $\rightarrow$ `CUSTOMS_CLEARED` $\rightarrow$ `DELIVERED`).
3. `test_invalid_shipment_state_transition_rejection`: Rejects invalid transitions deterministically.
4. `test_customs_clearance_lifecycle`: Validates customs state progression (`PENDING` $\rightarrow$ `SUBMITTED` $\rightarrow$ `CLEARED`).
5. `test_hub_operations_summary`: Verifies aggregation of in-transit shipments, customs holds, open POs, and alerts.
6. `test_hub_shipment_correlation`: Verifies correlation linking Supplier $\rightarrow$ PO $\rightarrow$ Shipment $\rightarrow$ GRN $\rightarrow$ Batches $\rightarrow$ Serials $\rightarrow$ Landed Cost.
7. `test_deterministic_operational_timeline`: Verifies chronological event compilation from authoritative source timestamps.
8. `test_copilot_grounded_context_assembly`: Verifies comprehensive assembly of C1, C2, C3.1, C3.2, C3.3, C3.4, and C3.5 telemetry.
9. `test_copilot_semantic_separation`: Verifies strict separation of `FACTS`, `SIGNALS`, `FORECASTS`, and `RECOMMENDATIONS`.
10. `test_copilot_insufficient_data_behavior`: Verifies explicit `INSUFFICIENT_DATA` response when records are missing.
11. `test_copilot_deterministic_factual_query`: Verifies direct deterministic routing for factual questions (SKU stock, landed cost).
12. `test_copilot_prompt_injection_defense`: Verifies malicious prompt injection inside notes does not override system instructions.
13. `test_copilot_mutation_safety_staged_proposal`: Verifies AI-suggested actions route to `StagedExtraction` with human-review gate.
14. `test_cross_tenant_isolation_cross_border`: Cross-tenant lookup/mutation fails safely.
15. `test_rbac_cross_border_matrix`: 5-tier matrix strictly maintained across all permissions.

---

## 3. Live Neon PostgreSQL E2E Scenarios (`e2e_c3_5_live.py`)

- **E2E-1:** Create cross-border procurement fixture spanning Supplier $\rightarrow$ PO $\rightarrow$ GRN.
- **E2E-2:** Associate currency and historical FX information.
- **E2E-3:** Associate landed-cost voucher and verify authoritative allocation.
- **E2E-4:** Verify batch provenance from GRN through inventory.
- **E2E-5:** Verify serial provenance where serialized products are involved.
- **E2E-6:** Create and verify cross-border shipment operational context.
- **E2E-7:** Verify operational timeline composed strictly from authoritative records.
- **E2E-8:** Verify deterministic factual hub query.
- **E2E-9:** Ask Copilot a grounded factual question; verify answer is supported by actual database facts.
- **E2E-10:** Ask Copilot for a derived signal; verify it is labeled as `SIGNAL`, not `FACT`.
- **E2E-11:** Ask a forecast question; verify forecast is separated from facts.
- **E2E-12:** Ask for a recommendation; verify recommendation is separated and does not mutate data.
- **E2E-13:** Ask a question with insufficient data; verify explicit insufficiency rather than hallucination.
- **E2E-14:** Attempt cross-tenant Copilot retrieval; must fail safely.
- **E2E-15:** Inject malicious instructions into a business document/note; verify prompt injection does not override system behavior.
- **E2E-16:** Attempt AI-triggered unauthorized mutation; verify no direct mutation occurs.
- **E2E-17:** Verify mutation proposal is staged for human review.
- **E2E-18:** Verify audit trail for approved AI-assisted operational action.
- **E2E-19:** Verify C3.1/C3.2/C3.3/C3.4 authoritative data remains unchanged.
