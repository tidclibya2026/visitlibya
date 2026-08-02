# Health Check Contract

| Endpoint | Success | Failure | Intended use |
|---|---|---|---|
| `/health/live` | 200 when the process serves requests | Connection failure or non-200 | Load-balancer/process liveness with conservative restart thresholds |
| `/health/ready` | 200 when the database is reachable and Alembic is current | 503 when connectivity or migration-head checks fail | Readiness traffic gating; remove an instance from service on failure |
| `/health/db` | 200 when database and PostGIS checks pass | 503 when either fails | Restricted operational diagnosis; not a public uptime probe |
| `/health` | Same as readiness | Same as readiness | Compatibility alias only |

Probe timeouts must be shorter than platform routing timeouts and long enough for the configured database connect timeout; exact intervals, thresholds, and restart policy require staging evidence. Responses expose status only and must never reveal credentials, connection strings, hosts, SQL, stack traces, extension details, or migration identifiers. Readiness blocks traffic when migration heads are not current. The database probe treats PostGIS failure as unavailable. Operational access to `/health/db` must be restricted by the approved network/monitoring policy.

