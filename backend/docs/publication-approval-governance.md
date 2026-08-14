# Publication Approval Governance

## Purpose and ownership

This policy establishes a repository-level foundation for publication governance owned by the Tourism Information and Documentation Center. Phase 1 records policy, freezes the current compatibility baseline, defines deterministic content hashing, and validates that no governed approval event has occurred. It does not change runtime visibility, backend behavior, static deployment, or any existing approval value.

The current system can display curated static content even when `publication_approved` or `publicationApproved` is false. That compatibility visibility is an implementation fact, not institutional approval. The boolean fields remain compatibility metadata and are not the authoritative source of a governance decision.

## Lifecycle and responsibilities

The controlled lifecycle is `DRAFT`, `REVIEW_REQUIRED`, `UNDER_REVIEW`, `RECOMMENDED`, `APPROVED`, `REJECTED`, `DEFERRED`, `EXPIRED`, `REVOKED`, `SUPERSEDED`, and `CORRECTION_REQUIRED`.

Institutional duties are assigned to roles, never to named people in public artifacts:

- `data_preparer` assembles a specific subject version and its evidence.
- `technical_validator` verifies schemas, hashes, coordinates, and mechanical constraints.
- `subject_matter_reviewer` evaluates identity, meaning, accuracy, and suitability.
- `media_rights_reviewer` independently verifies licenses, attribution, and usage scope.
- `publication_approver` may authorize publication only after all applicable prerequisites pass.
- `final_release_operator` releases an eligible, approved version but cannot override failed eligibility.
- `auditor` reviews evidence and history without creating or altering decisions through validation.
- `emergency_revocation_authority` may initiate a documented emergency takedown or revocation.

A data preparer cannot approve the same subject and content version. A publication approver cannot operate the final release for that release. Technical validation does not substitute for subject review, and media-rights approval remains independent. No single preparer may approve and publish the same record.

## Decisions and evidence

Future ledger decisions must bind to a subject type, stable subject identifier, canonicalization version, lowercase SHA-256 content hash, decision type and lifecycle state. Institutional evidence must include the responsible reviewer role, a privacy-safe institutional reviewer identifier, decision date, rationale, source references, and an expiry or scheduled review date where applicable. Private evidence, personal data, credentials, and tokens must never be projected into public artifacts.

Publication approval does not imply canonical identity approval, coordinate approval, destination membership approval, or media approval. Each applicable prerequisite remains an independent decision. A recommendation may support review but cannot authorize publication.

## Canonical hashing and invalidation

Canonical content is UTF-8 JSON with deterministic key ordering, stable number representation, and a versioned field allowlist for each subject type. The hash includes visitor-visible bilingual fields, source identifiers, authoritative coordinates, and applicable media hashes. Approval and review metadata are excluded. The digest is SHA-256 encoded as lowercase hexadecimal.

Any change to an allowlisted content field produces a different hash. A decision bound to the prior hash cannot authorize the changed content; eligibility must be suspended until the new version completes review. Hashing establishes version binding, not factual correctness or approval.

## Append-only history and adverse decisions

The ledger is append-only. Existing events are never edited or deleted; correction, supersession, expiry, rejection, and revocation are expressed as later events that reference the affected decision. Phase 1 requires the ledger to contain zero events, which means no governed approvals exist.

Revocation stops eligibility for the bound content version. Corrections create a new content version and require new prerequisite reviews. Expiry moves the decision out of eligibility until renewed. Emergency takedown prioritizes removal from release while preserving the immutable audit trail and requiring subsequent review and rationale. Revocation never erases prior evidence.

## Legacy compatibility baseline

`legacy-publication-baseline.json` freezes hashes, byte sizes, tracked status, semantic roles, and deterministic counts for the existing public artifacts. Hashes and sizes use the canonical Git blob representation: valid UTF-8 bytes with LF newlines, exactly as committed and consumed by Linux GitHub Actions and GitHub Pages. A Windows checkout may contain Git-produced CRLF pairs; governance converts only those pairs back to LF before comparison. Lone carriage returns and invalid UTF-8 are rejected, and no whitespace trimming, Unicode normalization, key or record reordering, or final-newline change is permitted. Thus working-tree byte counts may differ from committed canonical byte counts without weakening direct-edit detection. Its classification, `LEGACY_PUBLIC_BASELINE_NOT_INSTITUTIONAL_APPROVAL`, is compatibility evidence only. It grants no identity, media, or publication approval and gives no permission to add or change content. A mismatch requires explicit review. Phase 1 prohibits removing or altering baseline entries and leaves current runtime behavior unchanged.

## Release and public projection

Frontend publication files must eventually be generated deterministically from governed authoritative content and valid decisions. Direct editing of generated publication files must be detected. A public projection may contain only the minimum non-sensitive decision facts needed to demonstrate eligibility; it must exclude personal identifiers, private evidence, secrets, and internal notes.

Phase 1 is validation only and changes no enforcement or deployment behavior. Phase 2 adds deterministic, diff-checked generation for outputs whose canonical mapping is proven; it does not add governed eligibility projections or change visibility. Phase 3 is expected to enforce eligibility rules in backend services and APIs while preserving static GitHub Pages deployment.

## Phase 2 deterministic publication artifacts

`publication-generation-manifest.json` is the machine-readable boundary between governed inputs and the three protected compatibility outputs. It records the generator contract, output hashes and counts, serialization rules, support status, and explicit blockers. Its generation classification is not institutional approval.

The natural-tourism frontend module is deterministically generated from these ordered, tracked review artifacts:

- `backend/data/gis/green-mountain-tourism-curated.review.json`
- `backend/data/gis/libyan-sahara-tourism-curated.review.json`

The mapping preserves source order, source IDs, Arabic names, coordinates, media state, source provenance, and false approval state. Category presentation uses a closed mapping already present in the protected output. IDs 832 and 913 are rejected because they belong only to governed heritage review. No text, coordinate, filename, path, or source identity is normalized silently.

Serialization is UTF-8 without a BOM, two-space JSON indentation, explicit object-key order, governed input record order, unescaped Arabic, canonical LF newlines, and a terminal newline inside the established ES-module wrapper. Identical inputs therefore produce byte-identical output on every platform. Verification compares generated bytes with the canonicalized governed checkout form, so Git-produced Windows CRLF does not cause a false mismatch while every other byte difference—including spaces and final-newline changes—remains detectable.

`assets/js/data/curated-destinations.js` remains frozen legacy verification-only because no independent governed canonical input preserves all editorial, media-path, and JavaScript projection fields. `backend/data/dev/destinations.json` also remains frozen verification-only: it is itself the documented development seed and no independent canonical input reproduces its backend-only fields and additional record. Neither limitation may be hidden by inventing a generator or treating the artifact as approved.

### Direct-edit detection and safe generation

Verification regenerates the supported natural artifact in memory, byte-compares it with the protected file, and validates the two frozen artifacts against Phase 1 hashes, sizes, and counts. It fails without repairing a mismatch. CI also generates the supported artifact beneath the runner's temporary directory and runs the same comparison.

Local commands from the repository root are:

```text
python backend/scripts/publication_generation.py validate-manifest
python backend/scripts/publication_generation.py verify
python backend/scripts/publication_generation.py generate --output-dir C:\path\outside\the\repository
```

Generation refuses an output directory inside the repository. Protected replacement is disabled unless the `replace` command receives `--allow-protected-replacement`. Even then, governance and input invariants are validated first, an unreviewed direct edit is refused, only deterministically supported outputs are eligible, and replacement is atomic where supported. Replacement never changes the ledger or any approval field. Normal review and CI use verification or external generation, not replacement.

Public visibility means content is currently reachable by visitors. Legacy compatibility means that existing behavior is frozen without an approval claim. Generated output means bytes can be reproduced from declared governed inputs. Institutional publication approval requires a future valid ledger decision bound to the approved content hash; none of the other three states implies it.

## Validation

Run from the repository root:

```text
python -m json.tool backend/data/governance/publication-policy.json
python -m json.tool backend/data/governance/legacy-publication-baseline.json
python -m json.tool backend/data/governance/publication-generation-manifest.json
python backend/scripts/publication_governance.py
python backend/scripts/publication_generation.py validate-manifest
python backend/scripts/publication_generation.py verify
cd backend
python -m pytest -q tests/unit/scripts/test_publication_governance.py
python -m pytest -q tests/unit/scripts/test_publication_generation.py
python -m pytest -q tests/unit/scripts
```

The repository-wide static checks remain:

```text
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
git diff --check
```

Phase 2 grants no approval, creates no decision event, changes no public bytes or visibility, publishes nothing, and assigns no person to an institutional role.

## Phase 3 backend enforcement foundation

Phase 3 adds a migration-free, framework-light enforcement boundary in
`app/publication/governance.py`. It separates publication class, editorial state,
technical validity, institutional decision, and runtime visibility. The possible
runtime outcomes are `LEGACY_VISIBLE`, `ELIGIBLE`, `INELIGIBLE`, `REVOKED`, and
`CONFIGURATION_BLOCKED`. A result of `LEGACY_VISIBLE` always carries
`institutionally_approved=false`.

### Bypass map and mitigations

Before Phase 3, destination list, detail, search, favorite admission, and trip
admission relied on database `status=published` and `is_active=true`. Destination
create/update accepted those ordinary workflow fields from `content_admin` or a
superuser. The development importer could also insert the frozen seed directly.
The static frontend reads separate protected JavaScript artifacts and does not use
the backend database.

The authoritative visitor-facing destination list/detail and search service
boundaries now apply the same frozen legacy fingerprint catalog after the existing
published/active query. A database row is legacy-compatible only when its slug and
complete seed projection still match the frozen `backend/data/dev/destinations.json`
contract. This does not turn legacy visibility into approval and cannot extend to a
new slug or changed content. Favorite and trip routes remain authenticated personal
features and continue to rely on the destination repository's public predicate;
they do not create public destination visibility.

Destination mutations centrally refuse an `approved` state and refuse a
`published` result unless the result is an exact legacy compatibility match.
`publication_approved`, institutional decisions, and evidence fields are not API
schema fields; explicit client attempts are rejected as extra input. Content admins
and superusers retain draft/editorial operations but are not institutional
approvers. The development importer remains restricted to development/test, rejects
conflicts, and can create only records from the governance-protected frozen seed.

### Eligibility matrix

| Class | Runtime published/active | Frozen match | Editorial ready | Technical valid | Effective decision | Outcome |
|---|---:|---:|---:|---:|---|---|
| Legacy compatibility | yes | yes | n/a | n/a | none | `LEGACY_VISIBLE` (not approved) |
| Legacy compatibility | yes | no | n/a | n/a | any | `INELIGIBLE` |
| Governed record | yes | n/a | yes | yes | matching, unexpired `APPROVED` | `ELIGIBLE` |
| Governed record | any | n/a | no | any | any | `INELIGIBLE` |
| Governed record | any | n/a | any | no | any | `INELIGIBLE` |
| Governed record | any | n/a | any | any | missing/rejected/expired/hash mismatch | `INELIGIBLE` |
| Governed record | any | n/a | any | any | revoked | `REVOKED` |
| Governed record | any | n/a | any | any | ambiguous | `CONFIGURATION_BLOCKED` |

### Transition matrix and separation of duties

The append-only contract permits `NOT_SUBMITTED -> PENDING`, `PENDING -> APPROVED`,
`PENDING -> REJECTED`, a new `REJECTED -> PENDING` submission, and
`APPROVED -> REVOKED/EXPIRED`. Every event requires version, unique event ID,
subject type and ID, action, previous/resulting state, content hash, actor ID,
institutional role, evidence reference, reason, and timestamp. Previous state and
event-ID uniqueness are checked against immutable history. Approval requires the
`publication_approver` institutional role and rejects self-approval. Neither
`admin`, `content_admin`, an unknown role, nor a missing actor/evidence value is
sufficient.

No approval mutation endpoint is exposed. The in-memory decision source exists for
isolated unit tests only. The repository JSONL adapter is read-only. The committed
ledger is not a concurrency-safe production database and must never be used as one.

### Configuration, rollout, privacy, and operations

`LEGACY_COMPATIBILITY` preserves only exact frozen content. `GOVERNED_ENFORCEMENT`
fails closed for new or changed records. `APPROVAL_MUTATIONS` defaults off and cannot
be enabled without governance, institutional role mapping, evidence-reference
policy, actor identity provider, trusted deployment conditions, and durable atomic
decision storage. Since durable storage is intentionally unconfigured, production
validation rejects approval mutations even if other values are asserted.

Public responses contain no actor identity, evidence reference, event history, or
approval metadata. Stable errors contain only non-sensitive policy codes. Rollback
consists of reverting the backend enforcement code; it must never edit ledger
history or rewrite protected public artifacts.

Safe rollout is: validate legacy fingerprints; deploy read enforcement with
mutations disabled; provision an institutionally approved actor/role/evidence
policy; design and review concurrency-safe durable storage; then separately review
an authenticated, separation-of-duties mutation API. Remaining institutional
decisions are the authorized identity provider, recognized role mapping, evidence
reference rules, expiry policy, and operational authorities. No value is inferred
in this phase.

Phase 3 validation adds:

```text
cd backend
python -m pytest -q tests/unit/publication tests/unit/core/test_publication_config.py tests/unit/schemas/test_destination_publication_fields.py
python -m pytest -q tests/integration/api/test_destinations.py tests/integration/api/test_search.py tests/integration/api/test_production_security.py
```
