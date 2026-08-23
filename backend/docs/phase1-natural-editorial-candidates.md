# Phase 1 natural-resources editorial candidates

## Purpose and governance status

This self-contained foundation preserves the measured Phase 1 editorial review derived from the governed national natural-resources reconciliation. It is a national cross-destination review artifact, not a runtime source, public layer, publication approval, canonical destination assignment, or instruction to expose content.

The committed governed input SHA-256 is `501a23c24aeef24f84238a99d91a93de6f8a5b55e98763002f7da47cb617c8ac`. Explicit offline generation verifies that input and five external-audit hashes. Ordinary repository validation requires only committed repository evidence.

## Exact accounting

| Mutually exclusive resolution | Count |
|---|---:|
| Eligible new editorial candidates | 383 |
| Existing governed-overlap exclusions | 224 |
| Non-natural or mixed exclusions | 28 |
| Subtype-identity deferrals | 41 |
| Mandatory display exclusions | 4 |
| Other water resources deferred | 258 |
| Outside Phase 1 non-water scope | 7 |
| Technical or duplicate deferrals | 0 |
| **Governed ordinal closure** | **945** |

Phase 1 evaluates 676 records. Candidate selection requires clean governed natural routing, no inspected governed overlap, valid Point geometry, explicit subtype identity, no mandatory exclusion, and no non-natural, mixed, or technical quarantine state.

## Eligible institutional queues

| Priority category | Candidates |
|---|---:|
| `NATURAL_SPRINGS` | 91 |
| `DAMS_AND_RESERVOIRS_REVIEW` | 23 |
| `NATURAL_AND_DESERT_LAKES` | 9 |
| `CAVES_AND_ROCK_FORMATIONS` | 3 |
| `OASES_AND_PALM_LANDSCAPES` | 1 |
| `MOUNTAINS_AND_HIGHLANDS` | 0 |
| `NATURAL_COASTS_AND_BEACHES` | 0 |
| `ISLANDS` | 2 |
| `VALLEYS_AND_WADIS` | 254 |
| **Total** | **383** |

The queues are deterministic and sorted by priority band, descending readiness score, normalized name, and source ordinal. Queue position is a review aid only.

## Readiness scoring

| Band | Count |
|---|---:|
| `HIGH_EDITORIAL_PRIORITY` | 7 |
| `MEDIUM_EDITORIAL_PRIORITY` | 307 |
| `LOW_EDITORIAL_PRIORITY` | 69 |
| `DEFERRED` | 0 |

The 100-point score covers identity clarity (25), coordinate quality (20), description completeness (20), institutional provenance (15), duplicate/conflict safety (10), and media readiness and rights (10). It is triage, not approval.

## Identity, duplicate, and coordinate safeguards

All source names, normalized review names, descriptions, categories, properties, geometry, provenance, governed review IDs, and overlap evidence remain preserved. Deterministic editorial IDs bind the governed input hash, source ordinal, governed review ID, and priority category.

Seventy-one eligible records share a normalized name with records at different coordinates. They remain separate. Three eligible records retain near-coordinate review evidence. No record is consolidated based on names, coordinates, proximity, or source categories.

## Dam requirements

All 23 dam candidates remain infrastructure-associated natural-resource review evidence, not purely natural formations. Every dam queue entry requires:

- safety and operational-authority verification;
- visitor-accessibility verification;
- institutional-presentation authority.

No dam is publication approved or presented as visitor-ready.

## Gaps and exclusions

Mountains remain zero, with `FUTURE_GOVERNED_MOUNTAIN_SOURCE_ACQUISITION_REQUIRED`. New coast/beach candidates remain zero because the sole evaluated coastal record already overlaps governed evidence. No category is populated by reclassifying unrelated records.

The following mandatory exclusions remain outside every queue:

- `أطلال حصن بئر احكيم`
- `الفرارة موقع أثري مغمور بالمياه`
- `المقبرة الايطالية`
- `المنطقة الجنائزية`

The artifact also preserves 258 deferred wells, tanks, sulfuric waters, baths, fountains, pools, sabkhas, wetlands, and other water evidence outside the approved Phase 1 subtypes.

## Description and media safeguards

Among 383 candidates, 367 lack a source description, none has usable repository media, and none has independently cleared media rights. All candidates keep `publication_media_eligible: false`. Source media references remain evidence only and are not copied, exposed, or treated as ownership, rights, identity, classification, or approval.

## Protected invariants

- Green Mountain curated records remain 180.
- Libyan Sahara curated records remain 69.
- Curated natural frontend total remains 249.
- Publication-oriented national GIS count remains 214.
- Approval ledger remains empty.
- Registry, source manifest, curated layers, frontend, runtime, API, and database remain unchanged.

Every candidate remains `publication_approved: false`, `canonical_approval: false`, `public_visibility_enabled: false`, `publication_media_eligible: false`, `institutional_review_status: UNRESOLVED`, `canonical_destination: null`, and `editorial_selection_is_approval: false`.

## Validation and controlled regeneration

Ordinary validation is self-contained:

```powershell
python backend/scripts/phase1_natural_editorial_candidates.py
python -m pytest -q backend/tests/unit/scripts/test_phase1_natural_editorial_candidates.py
```

Controlled offline regeneration is explicit:

```powershell
python backend/scripts/phase1_natural_editorial_candidates.py build <EXTERNAL_AUDIT_DIRECTORY>
```

The validator fails closed on input and audit hashes, candidate queues, priorities, ordinal closure, eligibility, source evidence, overlaps, duplicates, coordinates, descriptions, media, governance, protected counts, serialization, paths, and changed-file scope.
