# DEADLINEOS BUSINESS OS — B5 COLLECTION & RESCUE INVARIANTS
**Document ID:** `B5-DOC-005`
**Status:** `BINDING SPECIFICATION`
**Classification:** Recovery Workflows & Invariants

---

## 1. Overdue Aging Buckets

Invoices with `status = 'OVERDUE'` (or $	ext{balance\_due} > 0$ and $	ext{due\_date} < 	ext{today}$) are partitioned into 4 mutually exclusive aging buckets:
- **Bucket 1 (1–30 Days Overdue):** Minor delay; gentle payment reminder.
- **Bucket 2 (31–60 Days Overdue):** Moderate delay; polite follow-up.
- **Bucket 3 (61–90 Days Overdue):** Severe delay; urgent executive notice.
- **Bucket 4 (90+ Days Overdue):** Critical default; formal legal notice.

---

## 2. Priority Scoring Formula

$$	ext{Priority Score } P = 	ext{balance\_due} 	imes \left(1 + rac{	ext{days\_overdue}}{30}
ight)$$

---

## 3. Human Confirmation Invariant

No collection reminder shall be automatically transmitted to an external recipient without explicit review, tone verification, and human confirmation.
