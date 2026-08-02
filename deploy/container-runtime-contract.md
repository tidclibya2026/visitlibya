# Container Runtime Contract

- Baseline image: Python 3.13, with reviewed/pinned application dependencies.
- Identity: non-root `visitlibya` user; no privilege escalation.
- Release identity: immutable image tag plus an approved digest. Record the previous digest for rollback.
- Network: container port 8000; `PORT` is environment-driven and validated.
- Workers: `WEB_CONCURRENCY` is environment-driven, load-tested, and included in the database pool budget.
- Runtime command: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${WEB_CONCURRENCY} --proxy-headers --forwarded-allow-ips ${FORWARDED_ALLOW_IPS}`.
- Proxy boundary: enable proxy headers only with an explicit, verified `FORWARDED_ALLOW_IPS`; wildcard trust is prohibited.
- Health: `/health/live` for process liveness, `/health/ready` for traffic readiness, `/health/db` for operational database/PostGIS validation, and `/health` as compatibility readiness.
- Lifecycle: provide a bounded graceful-shutdown window and stop new traffic before termination.
- Logging: structured application and access logs to stdout/stderr; never log secrets.
- Storage: assume no persistent local filesystem. Durable files require a separately approved service.
- Migrations: never run migrations during web startup. Use an explicit one-shot release job.
- Sizing placeholders: CPU `<APPROVED_CPU>`, memory `<APPROVED_MEMORY>`, minimum/maximum replicas `<APPROVED_REPLICA_RANGE>`.
- Rollback reference: `<PREVIOUS_APPROVED_IMAGE_DIGEST>`.

