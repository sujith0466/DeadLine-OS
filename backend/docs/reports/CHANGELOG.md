# Changelog - DeadlineOS

## [1.0.0] - 2026-06-27
### Added
- **AI Command Center**: Integrated NLP routing for tasks, goals, and analytics via Gemini.
- **Digital Twin**: Live Monte Carlo simulations for schedule capacity.
- **Rescue Center**: Automated risk detection and intervention generation.
- **Document & Vision Agents**: Semantic chunking, OCR, and automated task extraction.
- **Sentry Integration**: Global application performance monitoring.
- **Multi-Tenant Supabase Authentication**: JWT/JWKS asymmetric validation.
- **CI/CD Pipeline**: GitHub actions for testing and deployment validation.

### Changed
- **Intervention Engine**: Transitioned from a standalone UI to an internal orchestration mechanism running in the backend to proactively detect threats and power the Command Center and Analytics.
- **Database Architecture**: Migrated to Neon PostgreSQL for serverless scale.
- **Repository Structure**: Enforced strict segregation of `tests/`, `scripts/`, and `docs/`.

### Fixed
- Rebuilt AuthContext to strictly persist and synchronize Supabase sessions.
- Resolved backend initialization failures stemming from orphaned modules.
- Hardened all SQLAlchemy queries with `g.user_id` bounds to prevent cross-user data leakage.
