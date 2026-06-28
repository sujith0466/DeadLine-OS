# Final Deployment Checklist - DeadlineOS v1.0.0

- [x] **Repository Verification**
  - [x] No orphan models/modules.
  - [x] `backend/docs/reports/` structured and complete.
  - [x] No `.env` secrets checked in.

- [x] **Frontend (Vercel) Readiness**
  - [x] Ensure `VITE_API_BASE_URL` points to live Render endpoint.
  - [x] Ensure `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are mapped.
  - [x] Ensure `npm run build` succeeds (Verified in pipeline).

- [x] **Backend (Render) Readiness**
  - [x] Configure Build Command: `pip install -r requirements.txt && flask db upgrade`
  - [x] Configure Start Command: `gunicorn --worker-class eventlet -w 1 app:app`
  - [x] Verify Neon PostgreSQL `DATABASE_URL` is correct.
  - [x] Map `SUPABASE_SERVICE_ROLE_KEY` for background async functions.
  - [x] Map `CORS_ORIGINS` to the live Vercel domain.

- [x] **Post-Deployment Smoke Test**
  - [x] Visit live frontend.
  - [x] Register new user account.
  - [x] Ask Voice Copilot a question (tests AI, DB, Auth).
  - [x] Verify no console errors in browser.
