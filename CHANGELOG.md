# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-09-02
### Added
- **Business Operations Phase C2.6 — Business Copilot Operational Grounding**:
  - Conversational AI assistant grounding expanded to incorporate real-time operational facts: active stock valuation, Days of Inventory Remaining (DIR), critical stockout risks, open and overdue purchase orders, and active operational alerts.
  - Deterministic anti-hallucination context builder with fallback schema ensuring 100% test reliability.
  - Strict 5-tier RBAC authorization (OWNER, ADMIN, MEMBER, ACCOUNTANT allowed; VIEWER denied).
  - Row-level multi-tenant context isolation preventing cross-workspace telemetry exposure.

## [1.6.0] - 2026-09-02
### Added
- **Business Operations Phase C2.5 — Voice-Assisted Business Operations**:
  - Hands-free voice operations processing engine translating speech-to-text transcripts into operational candidates (stock adjustments, two-sided stock transfers, task allocations, purchase requisitions).
  - Multi-entity fuzzy & exact resolver against live workspace registers (products, SKUs, locations, partners, members).
  - Strict Zero-Bypass trust boundary routing spoken commands exclusively into `business_staged_extractions` (`status='NEEDS_REVIEW'`).
  - Enhanced `FinancialConverterService` domain commit gateway supporting stock adjustments, stock transfers, purchase requests, and business tasks upon human verification.
  - REST API endpoints mounted at `/api/business/operations/voice` (`POST /process`, `GET /history`).
  - Voice Command modal and operations dictation interface integrated into Business Staging Hub.

## [1.5.0] - 2026-09-02
### Added
- **Business Operations Phase C2.4 — Automation & Alerting**:
  - Proactive operational telemetry and signal evaluation covering stockouts, safety stock buffer breaches, overdue POs, supplier quality degradation, and dead stock.
  - SHA-256 deduplication fingerprinting preventing alert spamming across periodic evaluation cycles.
  - 24-hour cooldown suppression preventing re-triggering of resolved and dismissed alerts.
  - Full operational alert lifecycle management (`ACTIVE` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED` / `DISMISSED`) with forensic audit logging.
  - 1-Click Signal-to-Task synthesis generating assignable `BusinessTask` instances linked directly to source operational alerts.
  - Operational Alerts REST API endpoints mounted at `/api/business/operations/alerts` with RBAC enforcement and pagination.
  - Operational Alerts Radar view and task generation modal integrated directly into Business Tasks Control Hub.
  - Alembic migration `o2l3m4n5o6p7` (business_os_operational_alerts_c2_4).

## [1.4.0] - 2026-09-02
### Added
- **Business Operations Phase C2.3 — Operational Intelligence**:
  - Deterministic inventory consumption analytics and daily burn rate calculation ($v = \frac{\sum \text{OUT}}{N}$).
  - Days of Inventory Remaining ($DIR = \frac{\text{Stock}}{v}$) and projected stockout date forecasting with strict FACT vs FORECAST cognitive separation.
  - Dead stock / slow-moving inventory detection for products with zero OUT movements in $>60$ days.
  - Deterministic supplier reliability scorecard computing On-Time In-Full (OTIF) %, quality acceptance %, and average lead time actuals from completed Goods Receipts.
  - Guaranteed `INSUFFICIENT_HISTORY` fallback handling when completed deliveries $< 3$ to prevent score fabrication.
  - Actionable smart replenishment recommendation engine generating reorder quantities based on safety stock buffers and consumption velocity.
  - Operational Intelligence REST API endpoints mounted at `/api/business/intelligence/operations/` with `intelligence:read` RBAC protection.
  - Executive Operations Intelligence tab in frontend Business Intelligence Hub with Stockout Risk Radar, Supplier Scorecard, and Replenishment Center.

## [1.3.0] - 2026-09-02
### Added
- **Business Operations Phase C2.2 — Goods Receiving / GRN**:
  - Sequential GRN generator (`GRN-{YYYY}-{SEQUENCE:04d}`) with atomic transaction guarantees.
  - Multi-line receiving inspection capturing accepted vs rejected quantities, carrier name, delivery note #, and structured rejection reasons.
  - Partial receiving support with PO lifecycle state tracking (`PARTIALLY_RECEIVED` $\rightarrow$ `FULLY_RECEIVED`).
  - Immutable Inventory Ledger integration emitting `PURCHASE_RECEIVED` (`IN`) movements exclusively for accepted quantities.
  - Staging Trust Boundary integration staging `INVOICE_PAYABLE` proposals (`confidence_score=100`, status `NEEDS_REVIEW`) into Accounts Payable queue without direct ledger mutation.
  - Over-receiving discrepancy detection and forensic audit event logging (`GRN_CREATED`, `GRN_DISCREPANCY_DETECTED`).
  - Strict 5-tier RBAC enforcement with `procurement:receive` permission and tenant isolation.
  - Full frontend Goods Receipts / GRNs dashboard, Receiving Modal with real-time math validation, and GRN Detail Drawer.

- **Business Operations Phase C2.1 — Procurement Foundation**:
  - Purchase Requests (`/business/procurement`) with itemized submission, priority ratings, and approval workflows.
  - Purchase Orders (`/business/procurement`) with multi-line ordering, supplier binding, and lifecycle progression.
  - PR $\rightarrow$ PO conversion with automated line copying and audit trails.

## [1.2.0] - 2026-09-01
### Added
- **Business Operations Foundation (Phase C1)**:
  - Multi-facility Location Registry (`/business/locations`) with composite unique constraints and location categorization.
  - SKU & Product Catalog (`/business/products`) with reorder/safety stock thresholds, pricing, and supplier linkage.
  - Immutable Inventory Ledger (`/business/inventory`) derived dynamically via SQL `SUM(IN) - SUM(OUT)` over append-only stock movements.
  - Strict Negative Stock Prevention with immediate `HTTP 400 INSUFFICIENT_STOCK` rejection.
  - Atomic Inter-Location Transfers (`TRANSFER_OUT` + `TRANSFER_IN`) linked by single `transfer_batch_id`.
  - Operations Task Queue & Work Allocation (`/business/tasks`) with priority state machine and assignee lifecycle.
  - Staging Review & Commit Gateway for operational inventory adjustments and voice task candidates.
  - Executive Attention Radar integration on Business Dashboard (`/business/dashboard`) surfacing overdue tasks, blocked tasks, low stock, and out-of-stock items.
  - Extended 5-Tier RBAC permissions for operational management (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`).

## [1.1.0] - 2026-08-31
### Added
- **Business OS (Commercial Enterprise Edition)**:
  - Executive Command & KPI Telemetry (`/business/dashboard`) with real-time liquidity and burn rate monitoring.
  - Decision Intelligence, cash flow forecasting, and 30/60/90-day scenario planning (`/business/intelligence`).
  - Immutable Financial Ledger with double-entry precision and Python `Decimal` arithmetic (`/business/invoices`, `/business/transactions`, `/business/partners`).
  - Staging and document extraction pipeline with human-in-the-loop review (`/business/staging`).
  - Accounts Receivable collection rescue workflows and reminder automation (`/business/rescue`).
  - Recurring obligation scheduler and idempotent automation runners (`/business/recurring`).
  - Commercial multi-entity registry, subsidiary governance, and inter-entity eliminations (`/business/entities`, `/business/consolidation`).
  - 5-Tier RBAC access matrix (`OWNER`, `ADMIN`, `MEMBER`, `ACCOUNTANT`, `VIEWER`), immutable forensic audit logs, and workspace branding (`/business/team`, `/business/audit`, `/business/settings`).
  - Deep production health diagnostics, liveness/readiness probes, and 14-Gate Release Certification surface (`/business/health`).

## [1.0.0] - 2026-06-28
### Added
- Initial Release of DeadlineOS Personal OS.
- AI Command Center with Local Intelligence Engine parsing.
- Multimodal inputs: Voice, Vision, and Document Intelligence.
- Monte-Carlo simulated Digital Twin.
- Predictive Rescue Center for interventions.
- Full multi-tenant isolation via Supabase JWT Auth.
- Complete API schema validation.
