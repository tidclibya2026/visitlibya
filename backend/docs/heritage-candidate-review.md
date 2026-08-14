# Heritage candidate review

## Purpose and scope

`data/gis/heritage-candidates.review.json` is a governed, review-only queue for institutional GIS records that should leave natural-layer curation and receive specialist heritage review. Its initial scope is source features 832 and 913. It does not publish records, create destinations, approve coordinates, write frontend data, or write to the database.

The authoritative source values remain in `data/gis/natural-layer-cross-layer-review.json` and `data/gis/libyan-sahara-tourism-candidates.review.json`. Routing copies those values without renaming, geocoding, enriching, or deleting the source evidence.

## Separate decisions

The workflow keeps four decisions independent:

1. **Routing** assigns a candidate to an appropriate human review discipline.
2. **Canonical identity approval** determines whether the source record represents a verified heritage site and whether aliases refer to the same entity.
3. **Destination membership approval** determines whether a verified site belongs to an existing Visit Libya destination or requires separate destination governance.
4. **Publication approval** authorizes visitor-facing use only after identity, classification, coordinates, editorial content, and media rights are complete.

A routing decision is not evidence for any later approval. A source status such as `جاهز مبدئياً`, a category, a name signal, or geographic proximity cannot promote a record automatically.

## Controlled vocabulary

Artifact states:

- `HUMAN_REVIEW_ONLY_NOT_PUBLICATION_APPROVAL`
- `HERITAGE_REVIEW_REQUIRED`
- `REVIEW_REQUIRED`

Cross-layer routing state:

- `ROUTED_TO_HERITAGE_CANDIDATE_REVIEW`

Specialist review paths:

- `FORTIFICATION_HERITAGE_REVIEW`: routing based only on an observed fortification signal or separately tracked supporting occurrence.
- `ARCHAEOLOGICAL_SITE_REVIEW`: routing based only on an observed archaeological name signal.

Evidence scope:

- `ROUTING_ONLY_NOT_IDENTITY_APPROVAL`

No additional enum may be introduced without updating the validator, tests, and this governance document.

## Institutional review requirements

An authorized institutional review must record, in a future controlled decision artifact or schema revision:

- reviewer identity and institutional role;
- review date;
- identity decision and rationale;
- classification decision and supporting authority;
- exact institutional source reference and verified source hash;
- coordinate verification status and method;
- duplicate and alias review outcome;
- locality or municipality evidence, if any;
- destination-membership decision and rationale;
- media subject-match and media-rights decisions;
- unresolved issues and reviewer notes;
- publication decision, approver, date, and rationale when all gates are satisfied.

The current `institutional_review` and `publication_decision` fields must remain `null`. Every approval boolean must remain `false` during routing.

## Evidence, duplicate, and alias review

Names and categories are discovery evidence only. Reviewers must compare the original institutional record, source-native ID, coordinates, source context, and independent heritage authority before confirming identity or classification.

For ID 832, the fortification term and its occurrence in the tracked heritage document support only the fortification review path. For ID 913, the archaeological term supports only archaeological-site review. The nearby record ID 911 is unresolved geographic context and must not be treated as identity, settlement membership, municipality, or destination evidence.

Duplicate and alias review must preserve all source-native IDs, distinguish exact duplicates from related places, record the comparison basis, and avoid merging records by name or proximity alone.

## Media requirements

`media_companion_found: true` means only that the source pipeline detected companion media metadata. It is not media approval. Before use, reviewers must establish:

- correct subject identification;
- creator or photographer;
- source and stable delivery provenance;
- copyright owner;
- usage rights and permitted channels;
- editorial suitability and accessibility text approval.

No unresolved candidate may contain or infer a media URL or rights claim.

## Promotion gates

A candidate cannot progress to destination or publication data until all applicable identity, classification, coordinate, duplicate, destination-membership, editorial, media-rights, and publication decisions are explicitly approved by authorized reviewers. Promotion must use a separate controlled implementation with tests and code review.

Frontend content is never edited directly from an unresolved candidate. The natural curated JSON, natural frontend layer, canonical destination data, curated frontend destinations, and published heritage pages must remain free of IDs 832 and 913 until a later authorized promotion.

Future publication-approval governance should define reviewer roles, decision records, evidence retention, revocation, and regeneration of downstream data. This artifact deliberately does not anticipate or bypass that policy.

## Validation

Run from the repository root:

```text
python -m json.tool backend/data/gis/heritage-candidates.review.json
python -m json.tool backend/data/gis/natural-layer-cross-layer-review.json
python backend/scripts/heritage_candidate_review.py
cd backend
python -m pytest tests/unit/scripts/test_heritage_candidate_review.py
python -m pytest tests/unit/scripts/test_gis_registry.py tests/unit/scripts/test_coordinate_intake.py
cd ..
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
git diff --check
```

The validator is read-only. It fails on schema drift, changed source identity or coordinates, premature decisions or approvals, unsupported routing, untracked provenance, broken cross-layer references, or leakage into natural, destination, or frontend data.
