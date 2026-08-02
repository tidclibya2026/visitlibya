# Backend production runbook

## Deployment order

1. Confirm provider, HTTPS API hostname, proxy source addresses, PostGIS support, backup policy, and approvals.
2. Rotate the JWT signing value historically committed in `backend/.envpython`; treat the old value as exposed. Assess Git history and downstream clones separately. This repository does not rotate or rewrite history automatically.
3. Provision secrets through the selected secret manager. Never create a populated production `.env` in Git.
4. Provision PostgreSQL, enable PostGIS, require the approved SSL mode, and take/verify the required pre-migration backup.
5. Build the production image and run `python -m scripts.validate_production_config`.
6. Run `python -m scripts.wait_for_database`, then `python -m scripts.check_database`.
7. Execute the separate migration job: `alembic upgrade head`.
8. Verify `python -m scripts.check_migrations` exits zero.
9. Start API workers. Web startup never creates tables or runs migrations.
10. Verify `/health/live`, `/health/db`, and `/health/ready` through the proxy.
11. Validate CORS/preflight from `https://tidclibya2026.github.io` and complete security acceptance.
12. Activate the frontend only through the separately controlled procedure.

## Operations

Logs go to stdout/stderr and include request ID, method, path, status, and duration. They exclude bodies and authorization data. Monitor readiness failures, 5xx rates, latency, authentication anomalies, pool exhaustion, database capacity, backup results, and certificate expiry. Provider-specific metrics/alerts remain deferred.

## Incident placeholder

Record incident owner: **TBD**. Security contact: **TBD**. Legal/privacy contact: **TBD**. Preserve logs under the approved retention policy, revoke/rotate affected secrets through the secret owner, disable frontend API integration if necessary, and restore the last validated application/database state. Do not publish internal infrastructure details in health responses.

## Rollback

Stop routing new traffic to the new image, restore the previous validated image/configuration, and verify liveness. Prefer forward-fix migrations. Never run automatic downgrade. If schema rollback is approved, stop writers, take another backup, review the exact downgrade, execute it once through the migration job, then verify revision and data. Restore from a tested backup when downgrade is unsafe.
