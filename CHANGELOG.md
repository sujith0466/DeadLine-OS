# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
