# DeadlineOS Operations Runbook

## Daily Operations
- Monitor Sentry dashboard for new unhandled exceptions.
- Check Render dashboard for memory usage and CPU throttling.
- Check Vercel Analytics for frontend Web Vitals scores.

## Weekly Maintenance
- Run `npm audit` and `pip-audit` to detect zero-day vulnerabilities in the dependency chain.
- Review Supabase Auth limits to ensure rate limits haven't been breached by malicious actors.

## Deploying Updates
1. Merge feature branch into `main`.
2. The GitHub Action `.github/workflows/production.yml` will automatically lint, type-check, run `pytest`, and build.
3. If all tests pass, Render and Vercel will trigger zero-downtime deployments.

## Scaling Up
- **Backend:** Render allows horizontal scaling. Simply increase the instance count.
- **Database:** Neon autoscales compute automatically.
- **Frontend:** Vercel edge network autoscales globally.
