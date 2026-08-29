# DEADLINEOS BUSINESS OS — B4 INTELLIGENCE INVARIANTS
**Document ID:** `B4-DOC-004`
**Status:** `BINDING ARCHITECTURAL SPECIFICATION`
**Classification:** AI Safety & Deterministic Boundaries

---

## 1. Core Invariants

1. **INVARIANT-B4-01 (Grounding Invariant):** AI models shall only answer financial queries using verified, structured domain data assembled by the backend. Raw SQL generation by LLM is strictly prohibited.
2. **INVARIANT-B4-02 (Deterministic Math Invariant):** The Copilot shall not compute cash totals or runway days via LLM arithmetic; it must cite pre-calculated figures from `FinancialTruthService`.
3. **INVARIANT-B4-03 (Action Barrier Invariant):** AI cannot directly write to `business_invoices` or `business_transactions`. All proposed actions must pass through human review.
4. **INVARIANT-B4-04 (Tenant Context Containment):** Under no circumstance shall prompt context contain data from multiple workspaces.
