# Staging Deployment Runbook

This is a provider-neutral manual sequence. Record operator, reviewer, time, immutable references, outcomes, and evidence for every step.

1. **Approvals:** confirm scope, owners, data classification, change record, reviewed source, and permitted staging work.
2. **Isolated staging services:** verify separate compute, network, identities, logs, monitoring, and no production traffic or credentials.
3. **Staging database:** verify PostgreSQL/PostGIS baseline, private access, TLS, roles, encoding, timezone, connection budget, and no production data unless separately sanitized and approved.
4. **Staging secrets:** create new staging-only values through the approved secret process; verify access/audit without displaying them.
5. **Configuration validation:** run the environment validator and production-like policy checks against staged inputs without logging values.
6. **Database connectivity:** use the approved non-destructive helper from the migration job context; record only pass/fail evidence.
7. **PostGIS validation:** confirm required extension compatibility and health using approved non-destructive checks.
8. **Migration rehearsal:** take a staging backup, run reviewed Alembic upgrade as a one-shot job, verify current heads, and inspect timing/errors. Do not run migrations in web startup.
9. **Image deployment:** deploy the reviewed immutable digest with the approved non-root runtime, resources, environment references, and previous image recorded.
10. **Health validation:** validate liveness, readiness, database/PostGIS behavior, timeouts, and traffic gating.
11. **CORS validation:** allow the approved exact staging origin and reject unknown, path-bearing, credential-bearing, and wildcard origins.
12. **Authentication validation:** test token issuance, expiry, invalid signatures, protected routes, logging redaction, and negative cases using staging identities.
13. **Administrator authorization validation:** prove authorized administration works and non-admin/anonymous requests are denied.
14. **Destination and trip tests:** exercise representative read, filtering, destination detail, trip creation/edit authorization, concurrency, and fallback cases without production data.
15. **Logging and monitoring validation:** confirm correlation, redaction, dashboards, health signals, database signals, retention, and alert delivery.
16. **Backup and restore rehearsal:** create a staging backup, restore into a separate isolated target, and validate integrity, PostGIS, and migration heads.
17. **Rollback rehearsal:** route away from the new image, restore the prior image/configuration, validate health, and record timings. Do not automatically downgrade migrations.
18. **Evidence recording:** archive outputs, image digests, approvals, configuration fingerprints, migration revisions, observed RPO/RTO, issues, and sign-offs without secrets.
19. **Production approval gate:** present evidence against every release gate; unresolved blocking items prevent production approval.

