# DEADLINEOS BUSINESS OS — UX & INFORMATION ARCHITECTURE
**Document ID:** `B0-DOC-012`
**Status:** `B0 DESIGN DECISION`
**Classification:** User Experience & Frontend Architecture

---

## 1. Information Architecture & Navigation Hierarchy

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: Workspace Switcher [ Acme Studio ▼ ] | Quick Capture [+] | Copilot Drawer [⚡]│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ SIDEBAR NAVIGATION                                                                     │
│                                                                                        │
│ 🏢 BUSINESS OVERVIEW                                                                   │
│   ├── Cash Runway & Dashboard                                                          │
│   └── Daily Obligations & Calendar                                                     │
│                                                                                        │
│ 📥 CAPTURE & STAGING                                                                   │
│   ├── Quick Ingest (PDF / Audio / OCR)                                                 │
│   └── Review Queue (3 Staged Extractions)                                              │
│                                                                                        │
│ 💼 COMMERCIAL OPERATIONS                                                               │
│   ├── Receivables (Invoices Outbound)                                                  │
│   ├── Payables (Vendor Bills Inbound)                                                  │
│   ├── Customers & Suppliers Registry                                                   │
│   └── Transaction Ledger                                                               │
│                                                                                        │
│ 🛡️ INTELLIGENCE & RISKS                                                                │
│   ├── Cash Shortfall & Overdue Alerts                                                  │
│   └── Business Copilot                                                                 │
│                                                                                        │
│ ⚙️ WORKSPACE SETTINGS                                                                  │
│   ├── Members & Roles                                                                  │
│   ├── Currency & Invoicing Info                                                        │
│   └── Accountant Export                                                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core UI Surfaces

### 2.1 The "Cash Reality" Executive Header
Displays three prominent, unambiguous metrics on every business page:
1. **Confirmed Cash in Bank:** `₹4,82,500` (Verified from settled transactions).
2. **Expected Net (Next 14 Days):** `+₹1,15,000` (Receivables ₹2.10L minus Payables ₹95k).
3. **Projected Runway:** `52 Days` (Deterministic burn-rate formula).

### 2.2 The "Human-in-the-Loop" Staging Drawer
When documents or audio are uploaded:
- Opens a side-by-side verification interface: Original PDF/Image on the left, AI-extracted structured draft fields on the right.
- High-confidence fields are highlighted in Emerald; ambiguous or estimated fields are flagged in Amber with explicit validation prompts.
- Prominent button: **"Confirm & Record to Ledger"**.

### 2.3 The Workspace Context Switcher
- Placed persistently at the top-left of the shell.
- Allows immediate switching between **Personal OS** and any joined **Business Workspaces**.
- Switching workspaces immediately updates the active `X-Workspace-Id` context without full page reloads.
