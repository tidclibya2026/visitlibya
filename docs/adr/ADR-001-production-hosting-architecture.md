# ADR-001: Production Hosting Architecture

Status: Proposed

## Context

Visit Libya needs a production-capable home for its existing FastAPI container and PostgreSQL/PostGIS data layer. The static GitHub Pages frontend remains independently deployed and API-disabled until a later approval. This ADR records an architecture pattern, not a provider selection or deployment authorization.

## Decision drivers

- Managed operational controls without coupling application code to a vendor.
- PostgreSQL 16 and PostGIS 3.4 compatibility.
- Private database connectivity, TLS, backups, point-in-time recovery, monitoring, and auditable access.
- Immutable container releases, one-shot migrations, rollback, portability, and controlled cost.
- Staging parity and evidence-based security, privacy, legal, residency, and support review.

## Considered architecture patterns

1. Managed container service plus managed PostgreSQL/PostGIS.
2. Self-managed virtual machines for API and database.
3. Managed Kubernetes plus managed PostgreSQL/PostGIS.
4. Serverless functions plus managed PostgreSQL/PostGIS.

## Weighted evaluation

The editable criteria in `config/provider-evaluation.json` total 100. Architecture patterns and any future providers must be scored 0–5 only after authoritative evidence is recorded. Blocking criteria override weighted totals. No provider has been evaluated or selected.

## Provisional recommendation

Managed container service + managed PostgreSQL/PostGIS.

## Rationale

This pattern fits the current stateless container, preserves standard OCI and PostgreSQL interfaces, avoids unnecessary orchestration complexity, and places database durability operations with a managed control plane. It retains a practical exit path through image portability, Alembic migrations, standard database exports, and documented configuration contracts.

## Consequences

- Operations must approve a container platform and database service separately.
- Application workers remain stateless; persistent files require an approved external service.
- Migrations run as an explicit one-shot job, never in web-worker startup.
- Production requires managed secret injection, private database routing, TLS verification decisions, observability, backup, restore, and rollback evidence.
- Frontend activation remains a separate release.

## Risks

- Provider capabilities may not meet PostGIS, residency, recovery, support, or procurement requirements.
- Incorrect proxy trust, CORS, trusted hosts, pool sizing, or TLS settings can create security or availability failures.
- Managed-service portability can degrade if provider-specific features enter the application contract.
- An unrehearsed migration or restore can extend an incident.

## Exit strategy

Retain OCI-compatible images, provider-neutral environment variables, Alembic history, PostgreSQL-compatible logical/physical export options, documented role separation, and periodic export/restore evidence. Before adoption, document data egress, image export, DNS transition, secret replacement, recovery time, and contract termination steps.

## Unresolved decisions

- Provider, commercial terms, account, region, data residency, SLA, support tier, and procurement eligibility.
- Confirmed production API hostname, DNS owner, certificate owner, proxy CIDRs, and network topology.
- Database sizing, pool budget, storage growth, maintenance window, RPO/RTO, retention, and restore cadence.
- Monitoring platform, alert routes, on-call ownership, security/privacy approval, and launch window.

## Evidence requirements

Every candidate requires dated authoritative references for blocking criteria, technical validation results, procurement eligibility, residency, support, security controls, backup/PITR, export, and pricing. Claims without verified evidence receive no score.

## Approval fields

- Architecture owner: `<APPROVAL_REQUIRED>`
- Security owner: `<APPROVAL_REQUIRED>`
- Operations owner: `<APPROVAL_REQUIRED>`
- Privacy/legal owner: `<APPROVAL_REQUIRED>`
- Procurement owner: `<APPROVAL_REQUIRED>`
- Decision date: `<NOT_APPROVED>`
- Approval references: `<NOT_APPROVED>`

