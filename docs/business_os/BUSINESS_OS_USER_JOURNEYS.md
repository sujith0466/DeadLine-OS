# DEADLINEOS BUSINESS OS — CORE USER JOURNEYS
**Document ID:** `B0-DOC-013`
**Status:** `B0 DESIGN DECISION`
**Classification:** Product Operational Workflows

---

## 1. Journey 1: Workspace Creation & Initial Provisioning
- **Actor:** Business Owner.
- **Trigger:** Clicks "Create Business Workspace" from personal profile dropdown.
- **Steps:**
  1. Owner enters Business Name (`Apex Creative Labs`), Legal Name, GSTIN, and selects Currency (`INR`).
  2. Frontend sends `POST /api/business/workspaces`.
  3. Backend creates `business_workspaces` row, inserts `business_workspace_members` row assigning `role="OWNER"`, and provisions default settings in a single database transaction.
- **Outcome:** Owner is immediately switched into the new workspace context with an empty ledger and audit log initialized.

---

## 2. Journey 2: Team Member Invitation & Role Scoping
- **Actor:** Owner / Admin.
- **Steps:**
  1. Owner enters email (`accountant@apex.com`) and selects role `ACCOUNTANT`.
  2. Backend validates that current user has `members:invite` permission.
  3. Inserts `business_workspace_members` with status `INVITED`.
- **Outcome:** Invited user receives access token; when logged in, can switch to Apex Creative Labs workspace with read-only access to commercial contracts and full access to audit exports.

---

## 3. Journey 3: PDF Invoice Capture & Staging Confirmation
- **Actor:** Owner / Staff Member.
- **Steps:**
  1. User drags & drops a vendor PDF bill (`AWS_Hosting_July.pdf`) into Quick Capture.
  2. Frontend posts file to `POST /api/business/capture/upload`.
  3. `IngestionService` saves document to object storage, creates `IngestionArtifact`, and calls `HybridFailoverAIProvider` to extract fields.
  4. AI returns vendor name, subtotal, GST amount, total (`₹18,450.00`), and due date.
  5. Deterministic validator checks that `subtotal + tax == total`. Creates `StagedExtraction` with status `PENDING_REVIEW`.
  6. Review Drawer opens in UI. User reviews extracted fields, clicks **"Confirm & Record"**.
  7. Backend creates authoritative `Invoice` (direction `PAYABLE_INBOUND`), emits `INVOICE_RECORDED` event, and marks extraction `CONFIRMED`.
- **Outcome:** Payable obligation is registered; cash runway updates; audit record is written.

---

## 4. Journey 4: Customer Invoice Issuance & Receivable Tracking
- **Actor:** Owner / Sales Staff.
- **Steps:**
  1. User creates new outbound invoice to client `Ravi Digital Media` for `₹75,000.00` due in 15 days.
  2. Backend validates customer identity, saves `Invoice` with status `ISSUED`.
  3. Bridge adapter emits domain event and registers calendar collection reminder for 14 days later.
- **Outcome:** `₹75,000.00` is tracked under **Committed Inflows (Receivables)**; aging timer starts ticking.

---

## 5. Journey 5: Payment Receipt & Invoice Settlement
- **Actor:** Owner / Admin.
- **Steps:**
  1. Client transfers `₹75,000.00` via UPI. Owner clicks "Record Payment" on invoice `INV-2026-004`.
  2. Submits amount `₹75,000.00`, payment method `UPI`, reference `UPI/98421048`.
  3. Backend creates `BusinessTransaction(type="INCOME", amount=75000.00)`, updates invoice `paid_amount=75000.00`, `balance_due=0.00`, `status="PAID"`.
- **Outcome:** Confirmed Cash increases by `₹75,000.00`; Receivable disappears from aging queue; Today surface marks collection done.

---

## 6. Journey 6: Vendor Bill Payment & Outflow Settlement
- **Actor:** Owner.
- **Steps:**
  1. Owner pays electricity bill `₹12,400.00`. Clicks "Record Outflow".
  2. Backend creates `BusinessTransaction(type="EXPENSE", amount=12400.00)`.
- **Outcome:** Confirmed Cash decreases; runway metrics update; audit log records creator and timestamp.

---

## 7. Journey 7: Disputed Invoice Transaction Reversal
- **Actor:** Owner.
- **Steps:**
  1. A payment was accidentally logged twice. Owner clicks "Reverse Payment" on transaction `tx_982`.
  2. Must input mandatory reason: *"Duplicate entry from bank statement"*.
  3. Backend verifies `transaction:reverse` permission. Creates counter-transaction `BusinessTransaction(type="ADJUSTMENT", amount=-75000.00, reversal_of_transaction_id="tx_982")`.
  4. Original transaction is marked `status="REVERSED"` (never deleted). Invoice balance is recalculated.
- **Outcome:** Immutable audit record created; ledger balance restored accurately with full historical traceability.

---

## 8. Journey 8: Ambiguous Voice Command Disambiguation
- **Actor:** Owner on mobile.
- **Steps:**
  1. Owner speaks: *"Log 50k payment from Sharma"*.
  2. NLU resolves intent `RECORD_PAYMENT`, amount `₹50,000.00`, partner name `"Sharma"`.
  3. Partner registry finds two matches: `Sharma Logistics` and `Sharma & Sons Hardware`.
  4. System DOES NOT guess. UI presents disambiguation modal: *"Did you mean Sharma Logistics or Sharma & Sons?"*
  5. Owner selects `Sharma Logistics` and confirms.
- **Outcome:** Transaction is logged against the correct customer record without dangerous ambiguity.

---

## 9. Journey 9: Querying Business Copilot for Cash Health
- **Actor:** Owner.
- **Steps:**
  1. Owner asks: *"Can I afford to buy a ₹60,000 workstation next week?"*
  2. Copilot verifies role, queries current confirmed cash (`₹1,20,000`), upcoming payables next 7 days (`₹85,000`), and committed receivables (`₹40,000`).
  3. Deterministic formula calculates net buffer: `₹1,20,000 - ₹85,000 = ₹35,000`.
  4. Copilot responds: *"Your confirmed cash is ₹1,20,000, but you have ₹85,000 in committed supplier bills due in 5 days, leaving a safe buffer of ₹35,000. Unless client Ravi pays his ₹40k invoice early, a ₹60k purchase will cause a ₹25,000 cash shortfall."*
- **Outcome:** Grounded, explainable financial clarity without fabricated LLM numbers.

---

## 10. Journey 10: Exporting Clean Data for the Accountant
- **Actor:** Accountant / Owner.
- **Steps:**
  1. At month-end, Accountant navigates to Settings $\rightarrow$ Accountant Export.
  2. Selects date range (e.g. `July 1 – July 31, 2026`). Clicks "Generate Export Package".
  3. Backend compiles CSV transaction ledger, receivable/payable aging report, and ZIP of all verified invoice PDFs.
- **Outcome:** Zero paperwork gap; accountant imports verified ledger into Tally in minutes.
