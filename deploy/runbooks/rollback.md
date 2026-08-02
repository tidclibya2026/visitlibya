# Rollback Runbook

1. Declare rollback authority and preserve the incident/change timeline, logs, metrics, image digests, configuration fingerprints, and migration state.
2. Stop routing new traffic to the new image; keep evidence-producing instances isolated if safe.
3. Restore the previous approved immutable image reference and compatible previous non-secret configuration/secret references.
4. Verify liveness, readiness, restricted database health, error rate, latency, authentication, and administrative authorization before restoring traffic.
5. If a separately activated frontend is affected, deactivate API access by restoring `apiEnabled: false` through its own controlled release and verify the static fallback.
6. For migration failure, stop the migration job, prevent incompatible application traffic, capture errors and revision state, and engage the database/release owners.
7. Prefer a reviewed forward fix. Never run an automatic Alembic downgrade.
8. Consider database restore only when corruption, irreversible incompatible change, or approved recovery criteria are met; require incident commander, database owner, business owner, RPO/RTO, and data-loss approval.
9. Escalate security/privacy exposure, credential compromise, data integrity risk, or missed recovery objectives through the approved incident route.
10. Preserve evidence and record decisions, timestamps, approvals, recovered state, validation results, and follow-up work without secrets.

