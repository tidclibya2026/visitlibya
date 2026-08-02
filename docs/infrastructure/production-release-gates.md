# Production Release Gates

Every blocking gate must be approved with durable evidence before production. Default status is `Not started`; no approval is implied.

| Gate name | Blocking | Owner | Required evidence | Status | Approval date | Notes |
|---|---|---|---|---|---|---|
| Source and CI | Yes | `<ENGINEERING_OWNER>` | Reviewed commit and passing required checks | Not started | — | — |
| Immutable Docker image | Yes | `<RELEASE_OWNER>` | Approved digest, provenance, scan, prior digest | Not started | — | — |
| Production configuration | Yes | `<APP_OWNER>` | Validation output and peer review | Not started | — | — |
| Secrets | Yes | `<SECURITY_OWNER>` | Secret-manager references, access and rotation approval | Not started | — | — |
| Database | Yes | `<DB_OWNER>` | PostgreSQL readiness and private connectivity evidence | Not started | — | — |
| PostGIS | Yes | `<DB_OWNER>` | Compatible extension validation | Not started | — | — |
| Migrations | Yes | `<RELEASE_OWNER>` | Staging rehearsal and one-shot plan | Not started | — | — |
| Backup | Yes | `<DB_OWNER>` | Successful backup and retention evidence | Not started | — | — |
| Restore test | Yes | `<RECOVERY_OWNER>` | Isolated restore and integrity report | Not started | — | — |
| RPO/RTO approval | Yes | `<BUSINESS_OWNER>` | Signed objectives and observed rehearsal | Not started | — | — |
| TLS | Yes | `<SECURITY_OWNER>` | API and database TLS validation | Not started | — | — |
| DNS | Yes | `<DNS_OWNER>` | Approved records and rollback plan | Not started | — | — |
| Proxy trust | Yes | `<NETWORK_OWNER>` | Verified proxy IP/CIDR allowlist | Not started | — | — |
| Trusted hosts | Yes | `<NETWORK_OWNER>` | Confirmed API hostname and negative tests | Not started | — | — |
| CORS | Yes | `<APP_OWNER>` | Exact frontend origin allow/deny tests | Not started | — | — |
| Health checks | Yes | `<OPS_OWNER>` | Liveness/readiness/database behavior evidence | Not started | — | — |
| Monitoring | Yes | `<OPS_OWNER>` | Dashboards and signal coverage | Not started | — | — |
| Logs | Yes | `<OPS_OWNER>` | Redaction, correlation, access, retention evidence | Not started | — | — |
| Alert routing | Yes | `<OPS_OWNER>` | Tested routes and escalation ownership | Not started | — | — |
| Staging acceptance | Yes | `<PRODUCT_OWNER>` | Signed staging test record | Not started | — | — |
| Security approval | Yes | `<SECURITY_OWNER>` | Threat/risk review and acceptance | Not started | — | — |
| Legal/privacy approval | Yes | `<LEGAL_PRIVACY_OWNER>` | Documented legal/privacy decision | Not started | — | — |
| Operational support | Yes | `<OPERATIONS_OWNER>` | Support coverage and escalation plan | Not started | — | — |
| Rollback | Yes | `<RELEASE_OWNER>` | Successful image/config rollback rehearsal | Not started | — | — |
| Frontend activation | Yes | `<FRONTEND_OWNER>` | Separate approved change after API acceptance | Not started | — | Must not be bundled with backend release |

