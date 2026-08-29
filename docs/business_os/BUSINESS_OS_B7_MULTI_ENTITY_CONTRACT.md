# DEADLINEOS BUSINESS OS — B7 MULTI-ENTITY CONTRACT
**Document ID:** `B7-DOC-005`
**Status:** `BINDING SPECIFICATION`
**Classification:** Domain Specification

---

## 1. Core Domain Entities

1. **`BusinessEntity` (`business_entities`):**
   - Represents a legally registered company, subsidiary, LLP, or operating branch.
   - Fields: `id`, `workspace_id`, `name`, `legal_name`, `entity_code`, `tax_identifier`, `currency`, `is_default`, `status`.

2. **`InterEntityTransfer` (`business_inter_entity_transfers`):**
   - Represents capital, loan, or service transfers between two distinct entities.
   - Fields: `id`, `source_workspace_id`, `source_entity_id`, `destination_workspace_id`, `destination_entity_id`, `amount`, `currency`, `status`.
