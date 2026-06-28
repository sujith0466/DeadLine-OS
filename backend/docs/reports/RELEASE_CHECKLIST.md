# DeadlineOS Release Candidate Checklist

- [x] **Repository Re-Architecture**
  - [x] Moved `test_*.py` into `backend/tests/`
  - [x] Moved `migrate_*.py` into `backend/scripts/migrations/`
  - [x] Moved `cleanup_*.py` into `backend/scripts/maintenance/`
  - [x] Moved `*_REPORT.md` into `backend/docs/reports/`
  - [x] Deleted obsolete testing stubs in frontend.

- [x] **Dependency Optimization**
  - [x] Extracted Dev requirements to `requirements-dev.txt`
  - [x] Verified `package.json` distinguishes `dependencies` from `devDependencies`.

- [x] **Environments & Secrets**
  - [x] `backend/.env.example` audited (no secrets left behind).
  - [x] `frontend/.env.example` audited (no secrets left behind).
  - [x] `.gitignore` updated to block `*.pem`, `*.key`, `.env`, `*.stackdump`.

- [x] **Monitoring & Observability**
  - [x] Sentry SDK installed and initialized in `frontend/src/main.tsx`.
  - [x] Sentry SDK installed and initialized in `backend/app.py`.
  - [x] JSON Structured Logging configured.

- [x] **Security & Networking**
  - [x] `CORS_ORIGINS` enforced via environment variables.
  - [x] Security headers (CSP, HSTS, X-Content-Type-Options) added in Flask.
  - [x] Validated Supabase JWT flow.

- [x] **CI/CD**
  - [x] `.github/workflows/production.yml` deployed.

- [x] **Testing & Audit**
  - [x] `npm audit` returned 0 vulnerabilities.
  - [x] Backend tests natively executed against multi-tenant models.
  - [x] Frontend compiled beautifully with zero `tsc` type errors.

- [x] **Documentation**
  - [x] Generated `DISASTER_RECOVERY.md`
  - [x] Generated `OPERATIONS_RUNBOOK.md`
  - [x] Generated `SECURITY_AUDIT.md`
  - [x] Generated `DEPLOYMENT_GUIDE.md`
