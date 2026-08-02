# Production Infrastructure Specification

Status: Provider-neutral proposed specification; not deployment authorization.

## Application runtime

- Run the existing FastAPI application in an immutable OCI-compatible image based on Python 3.13.
- Use the repository Uvicorn command targeting `app.main:app`, binding `0.0.0.0` to container port 8000, with `PORT`, `WEB_CONCURRENCY`, proxy headers, and explicit `FORWARDED_ALLOW_IPS` supplied by the environment.
- Run as the existing non-root `visitlibya` user. Do not write credentials or durable application data to the container filesystem.
- Use an approved immutable image digest and retain the previous digest for rollback. Never run Alembic in web startup.
- Start with a conservative worker count derived from allocated CPU and load testing; coordinate total workers with the database connection budget.

## Database

- Baseline: PostgreSQL 16, PostGIS 3.4, Psycopg 3, UTF-8, and UTC application timestamps.
- Use private networking only; prohibit a publicly exposed database port.
- Require database TLS. Prefer `verify-full` where the approved service exposes a verifiable CA and hostname; document any weaker approved mode.
- Set application pool size, overflow, timeout, recycle, pre-ping, and connect timeout from the environment. Sum maximum connections across all replicas and workers before approval.
- Use separate infrastructure, migration, application, backup/restore, and optional read-only identities.

## Release and networking

- Run Alembic as an explicit, auditable, one-shot migration job before directing traffic to a compatible image. Verify every head afterward.
- Put the API behind an approved HTTPS reverse proxy/load balancer. Trust only verified proxy IP addresses or CIDRs; never wildcard proxy trust.
- Configure the confirmed frontend CORS origin exactly as `https://tidclibya2026.github.io`; an origin never contains `/visitlibya/`.
- Configure trusted hosts with the future confirmed API hostname only. No API hostname is selected in this specification.

## Health and operations

- `/health/live`: process liveness. `/health/ready`: database connectivity and migration-head readiness. `/health/db`: database and PostGIS health. `/health`: compatibility alias with readiness semantics.
- Use readiness to gate traffic and liveness only for bounded restart decisions. Restrict detailed operational probes according to the access policy.
- Emit structured logs to stdout/stderr without secrets or sensitive request content. Centralize retention, search, correlation IDs, metrics, dashboards, and alert routing after approval.
- Monitor API availability/latency/errors, saturation, restarts, database connections/latency/storage/replication, backup/PITR status, certificate expiry, migration status, and recovery objectives.

## Secrets and configuration

- Inject `DATABASE_URL` and `JWT_SECRET_KEY` at runtime from an approved secret manager; never bake them into images, source, logs, or frontend files.
- Generate new environment-specific secrets only during an approved provisioning process. Restrict read access, audit retrieval, and define rotation and emergency revocation procedures.
- Keep non-secret configuration environment-driven and validated before release. Disable production documentation endpoints unless explicitly approved.

## Continuity and environments

- Maintain isolated staging services, database, credentials, network policy, backups, monitoring, and representative configuration. Staging must not share production data or secrets.
- Enable automated backups and approved PITR retention. Rehearse restore into isolation and record integrity, PostGIS, migration-head, RPO, and RTO evidence.
- Roll back application/configuration to the retained previous immutable image. Prefer forward-fix for migrations; never automatically downgrade. Restore only through an approved incident decision.
- Maintain an export/exit test and provider-neutral recovery documentation.
- Frontend API activation is a separate future change after backend production acceptance; the committed frontend remains API-disabled.

