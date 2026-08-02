# Backend security checklist

## Required before deployment

- [ ] Rotate the JWT signing value historically tracked in `backend/.envpython`; treat it as exposed.
- [ ] Assess Git history, clones, caches, and access logs; history rewriting requires separate approval.
- [ ] Provision a strong JWT secret and database credentials through a secret manager.
- [ ] Confirm `APP_ENV=production`, `DEBUG=false`, HTTPS API hostname, exact trusted hosts, and exact proxy allowlist.
- [ ] Confirm CORS contains `https://tidclibya2026.github.io`, without `/visitlibya/`.
- [ ] Confirm Swagger, ReDoc, and OpenAPI policy.
- [ ] Run configuration, database, PostGIS, migration, test, container, and secret validations.
- [ ] Confirm content-admin membership and remove stale administrative access.
- [ ] Approve backup/restore, logging retention, monitoring, incident, privacy, and legal requirements.

## Implemented baseline

Argon2id passwords; bounded HS256 access-token expiry; masked signing secret; active-user and explicit `content_admin`/superuser authorization; generic authentication failures; trusted hosts; exact CORS; request IDs; conservative security headers; no-store authentication/trip/favorite responses; generic 500 responses; bounded DB pools/connect timeout; optional SSL mode; non-root container; separate migrations.

## Explicitly deferred

Rate limiting, account lockout, token revocation, JWT issuer/audience policy, registration enumeration policy, HSTS/HTTPS redirect, monitoring vendor, media-domain allowlist, RPO/RTO, and legal/organizational policy. These require approved product, proxy, operational, or legal decisions.

Never log Authorization headers, JWTs, passwords, database URLs, authentication bodies, secret settings, or full user records. Public errors and health checks must not expose hosts, SQL, credentials, or stack traces.
