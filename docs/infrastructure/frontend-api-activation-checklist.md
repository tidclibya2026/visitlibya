# Frontend API Activation Checklist

Frontend API activation is a separate future change. This checklist does not authorize changing `config/frontend-config.js`, deploying Pages, or enabling API traffic.

- [ ] Confirm an approved HTTPS API origin.
- [ ] Confirm the backend is healthy.
- [ ] Confirm PostgreSQL and PostGIS are healthy.
- [ ] Confirm the database is at the current Alembic head.
- [ ] Validate the exact CORS origin `https://tidclibya2026.github.io` (an origin must not contain a repository path).
- [ ] Confirm the trusted API host.
- [ ] Confirm proxy configuration and trusted IP/CIDR boundaries.
- [ ] Test authentication using approved test identities.
- [ ] Test administrative authorization and negative permissions.
- [ ] Preserve the static/unavailable fallback.
- [ ] Update `apiBaseUrl` only after explicit approval.
- [ ] Change `apiEnabled` to `true` only after explicit approval.
- [ ] Run Pages validation and a controlled deployment under a separate change record.
- [ ] Define rollback by restoring `apiEnabled: false` and validating static fallback behavior.

