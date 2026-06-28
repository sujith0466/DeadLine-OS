# DeadlineOS Disaster Recovery Plan

## 1. High Availability & Backups

### 1.1 Neon PostgreSQL
Neon automatically retains Point-In-Time-Recovery (PITR) history for the primary database cluster.
- **RPO (Recovery Point Objective):** 5 minutes.
- **RTO (Recovery Time Objective):** ~10 minutes.
- **Action:** If the database becomes corrupted, log into the Neon console and use the "Restore to Point in Time" branching feature. 

### 1.2 Supabase Authentication
Supabase handles its own redundant backups across regions.
- **Action:** In case of catastrophic Auth loss, use Supabase CLI to restore the most recent daily PG dump snapshot.
- *Warning:* Password hashes are heavily salted and cannot be re-imported outside the Supabase ecosystem. Keep the `SUPABASE_JWT_SECRET` backed up securely.

### 1.3 Hosting Environments (Vercel & Render)
Vercel (Frontend) and Render (Backend) are ephemeral stateless environments.
- **Action:** In the event of a datacenter outage, deploy to fallback regions by changing the deployment settings in the Render/Vercel dashboards and updating the DNS routing.

---

## 2. Rollback Procedures

### 2.1 Backend Rollback
If a newly deployed API version causes critical failures:
1. Revert the commit on GitHub (`git revert <commit-hash>`).
2. The GitHub Action will automatically re-deploy the `main` branch to Render.
3. Verify the `/health` endpoint.

### 2.2 Database Rollback
DeadlineOS uses SQLAlchemy. If a bad migration occurs, do not attempt to drop tables manually.
1. Run `alembic downgrade -1` (if Alembic is configured), OR
2. Branch the Neon database to a point before the migration, then promote the branch to production.

---

## 3. Incident Response Protocol
1. **Identify the Scope:** Check Sentry for the traceback. 
2. **Mitigate:** If it's a data corruption bug, immediately suspend the backend API on Render to stop the bleeding.
3. **Resolve:** Push a hotfix branch.
4. **Post-Mortem:** Document the incident in `docs/reports/` using the 5-Whys methodology.
