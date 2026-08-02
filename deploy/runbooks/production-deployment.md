# Production Deployment Runbook

1. Confirm the approved change window, change record, go/no-go authority, incident path, and named role assignments: release owner `<OWNER_REQUIRED>`, database owner `<OWNER_REQUIRED>`, operations owner `<OWNER_REQUIRED>`, security owner `<OWNER_REQUIRED>`, and acceptance owner `<OWNER_REQUIRED>`.
2. Confirm all release gates and staging evidence are approved; freeze the reviewed source and immutable image digest. Record the previous approved image/configuration references.
3. Inject production configuration and secret references through approved systems. Never display or place secrets in command history, source, images, or logs.
4. Verify private database readiness, PostgreSQL/PostGIS compatibility, TLS, roles, connection budget, monitoring, and current backup/PITR health.
5. Confirm a recoverable pre-change backup and its retention/reference. Reconfirm restore decision authority.
6. Stop if there is schema drift. Run reviewed Alembic migrations as one explicit one-shot job using the migration identity; never in web workers.
7. Verify the database is at every expected Alembic head and record non-sensitive evidence.
8. Deploy the approved immutable API image using the application identity, non-root runtime, resource limits, and explicit proxy trust.
9. Validate `/health/live`, then `/health/ready`; validate restricted `/health/db` and `/health` compatibility behavior. Do not admit traffic until readiness passes.
10. Validate exact approved CORS behavior and rejection of unknown/path-bearing origins.
11. Validate the confirmed trusted host and rejection of invalid Host headers.
12. Validate authentication, expiry, protected endpoints, and secret/log redaction with approved production-safe test procedures.
13. Validate administrative permissions and denial for anonymous/non-admin identities without changing tourism content.
14. Confirm API error rate, latency, saturation, restarts, database connections/latency/storage, backup/PITR, and certificate signals.
15. Confirm centralized logs, correlation IDs, access controls, retention, and alert routing without sensitive output.
16. Obtain technical and business acceptance; record outcomes, owners, times, image/configuration references, and remaining observations.
17. Keep frontend API activation as a separate later approved change. Do not modify or deploy frontend runtime configuration in this release.

