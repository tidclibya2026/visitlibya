# Incident Response Runbook

## Classification and roles

Classify severity from observed safety, confidentiality, integrity, availability, and visitor impact using an approved severity matrix. Response-time and notification targets remain `<APPROVAL_REQUIRED>`; this document creates no commitment.

- Incident commander: `<ASSIGN_AT_INCIDENT>`
- Technical lead: `<ASSIGN_AT_INCIDENT>`
- Communication owner: `<ASSIGN_AT_INCIDENT>`
- Security/privacy owner: `<ASSIGN_AT_INCIDENT>`
- Database/recovery owner: `<ASSIGN_AT_INCIDENT>`

## Response

1. **Detection:** validate alerts/user reports, open an incident record, establish time zero, and avoid exposing sensitive details.
2. **Containment:** reduce traffic, isolate affected instances/identities/routes, preserve service where safe, and prevent uncontrolled changes.
3. **Evidence:** preserve immutable logs, metrics, audit trails, image/configuration references, migration state, and operator actions with controlled access.
4. **Credentials:** if compromise is suspected, revoke/rotate only under security approval, identify affected consumers, and never reveal values in the incident record.
5. **Database protection:** block unsafe writers, preserve backups/PITR, restrict administrative access, assess integrity, and do not run destructive SQL or unapproved restore operations.
6. **Rollback:** follow the rollback runbook for application/configuration regressions; prefer forward fixes for schema issues and prohibit automatic downgrades.
7. **Restore:** restore only to an isolated approved target first; assess data loss against approved RPO/RTO and obtain required authority.
8. **Recovery:** validate liveness/readiness, data/PostGIS integrity, migration heads, authentication/authorization, CORS/trusted hosts, monitoring, logs, and business acceptance before normal traffic.
9. **Communication:** issue factual, approved updates at the cadence `<APPROVAL_REQUIRED>`; route regulatory/privacy communications through the designated owner.
10. **Post-incident review:** document cause, contributing controls, response timeline, user/data impact, evidence gaps, corrective owners, due dates, and risk acceptance. Preserve unresolved response-time targets as approval-required.

