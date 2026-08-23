# National natural-resources source reconciliation

## Purpose and status

This foundation preserves and evaluates all 945 Point features in the institutionally held national natural-resources atlas with media. It is a national, cross-destination, review-only source contract. It is not a destination-specific GIS layer, runtime source, curated public layer, canonical destination dataset, institutional approval, or publication decision.

The registered source ID is `natural-atlas-media`. Its verified SHA-256 is `b389136b4d9f8fcc138f48999745b26b899747830489475b70988f679c442f49`. The exact content is already registered, so this phase changes no source manifest. Portable source and external-audit hashes are recorded without local Windows paths. Ordinary validation uses the committed artifact and does not require the external source.

## Deterministic accounting

| Resolution bucket | Count |
|---|---:|
| Raw source ordinals | 945 |
| Clean natural-resource review representatives | 876 |
| Category-scope mismatch | 4 |
| Mixed natural-cultural review | 6 |
| Other non-natural review | 59 |
| Safe duplicate members | 0 |
| Coordinate or identity quarantine | 0 |
| Resolved source ordinals | 945 |

Every ordinal from 1 through 945 resolves exactly once. No source record is deleted, repaired, merged, approved, or exposed publicly. Deterministic review identity binds the source SHA-256, source ordinal, raw ID as one evidence field, all 32 preserved source properties, proposed normalized review name, and complete geometry. Raw ID is never the sole identity.

## Clean natural-resource review routing

| Review collection | Count |
|---|---:|
| `WATER_RESOURCES_AND_SPRINGS` | 382 |
| `LAKES_AND_WETLANDS` | 92 |
| `OASES_AND_PALM_LANDSCAPES` | 1 |
| `VALLEYS_AND_WADIS` | 380 |
| `MOUNTAINS_AND_HIGHLANDS` | 0 |
| `DESERT_AND_DUNE_LANDSCAPES` | 2 |
| `GEOLOGY_AND_GEOMORPHOLOGY` | 1 |
| `CAVES_AND_ROCK_FORMATIONS` | 6 |
| `COASTS_BEACHES_AND_ISLANDS` | 3 |
| `FORESTS_AND_VEGETATION` | 1 |
| `PROTECTED_AREAS_AND_PARKS_REVIEW` | 7 |
| `WILDLIFE_AND_BIODIVERSITY_REVIEW` | 1 |
| `NATURAL_VIEWPOINTS_AND_LANDSCAPES` | 0 |
| `UNRESOLVED_NATURAL_CONTEXT` | 0 |
| **Total** | **876** |

Routing labels support institutional review only. They do not establish canonical natural classification, destination identity, public visibility, or publication eligibility.

## Non-natural and mixed routing

| Review collection | Count |
|---|---:|
| `CATEGORY_SCOPE_MISMATCH_REVIEW` | 4 |
| `ARCHAEOLOGICAL_OR_HERITAGE_REVIEW` | 23 |
| `HISTORICAL_OR_MEMORIAL_REVIEW` | 0 |
| `SETTLEMENT_OR_URBAN_REVIEW` | 3 |
| `VISITOR_SERVICE_OR_FACILITY_REVIEW` | 15 |
| `AGRICULTURAL_OR_PRODUCTIVE_SITE_REVIEW` | 6 |
| `INFRASTRUCTURE_OR_TRANSPORT_REVIEW` | 12 |
| `MIXED_NATURAL_CULTURAL_REVIEW` | 6 |
| `UNRESOLVED_NON_NATURAL_CONTEXT` | 0 |
| **Total** | **69** |

The filename, source category, water adjacency, or submersion does not prove that archaeological, historical, service, settlement, agricultural, or infrastructure evidence is a natural resource.

## Mandatory natural-display exclusions

The following evidence remains preserved under `CATEGORY_SCOPE_MISMATCH_REVIEW` and is absent from every clean natural collection:

| Ordinal | Source name |
|---:|---|
| 1 | `أطلال حصن بئر احكيم` |
| 2 | `الفرارة موقع أثري مغمور بالمياه` |
| 3 | `المقبرة الايطالية` |
| 4 | `المنطقة الجنائزية` |

Each has `exclusion_from_natural_display: true` and `exclusion_from_natural_media: true`. No canonical destination, approval, visibility, or automated repair is granted. Their water-related source categories, adjacency, or submersion are not natural-resource identity evidence.

## Orthogonal overlap evidence

Overlap is separate from the 876/69 resolution decision:

| Mutually exclusive overlap state | Count |
|---|---:|
| `DIRECT_CURATED_SOURCE_ID_OVERLAP` | 249 |
| `INFERRED_CURATED_NAME_COORDINATE_OVERLAP_WITHOUT_DIRECT_ID` | 1 |
| `OTHER_GOVERNED_DATASET_ONLY_OVERLAP` | 8 |
| `NO_INSPECTED_GOVERNED_OVERLAP` | 687 |
| **Total** | **945** |

There are 258 source records with any inspected governed overlap and 250 with any curated natural overlap. Direct source-ID matches consist of 180 Green Mountain and 69 Libyan Sahara records. Ordinal 540 is the one inferred curated name-coordinate overlap without a direct source ID. Heritage source-ID evidence for ordinals 832 and 913 remains preserved.

Overlap does not create another public record, increase registry counts, grant canonical identity, overwrite curated data, or authorize consolidation.

## Duplicate and conflict review

- Duplicate raw IDs: 0.
- Exact complete-feature duplicates: 0.
- Safe duplicate members: 0.
- Normalized-name/exact-coordinate groups remain unresolved at ordinals 539/540 (`بحيرة العيون`) and 889/890 (`فوار العريبات`).
- The different-name/identical-coordinate conflict remains unresolved at ordinals 597/601 (`سبخة أم سيد` / `سبخة الحنية`).
- All 76 same-name/different-coordinate groups remain separate.
- Near-coordinate evidence remains preserved: 22 pairs within 10 m, 24 within 25 m, and 39 within 100 m.

Names, coordinates, proximity, and source categories do not authorize automatic consolidation.

## Spatial quality

All 945 source geometries are finite, Libya-plausible Points and remain unchanged. No coordinate is repaired automatically. Ordinals 579, 734, 792, 846, and 847 retain their inconsistent `geometry_type` or `coord_count` source properties and carry `source_geometry_metadata_mismatch: true`. Actual geometry never silently overwrites source metadata evidence.

## Source fields and status

All 32 property fields, raw categories, descriptions, origins, folders, status values, enrichment fields, and geometry are preserved. The value `جاهز مبدئياً` remains raw source text only. It does not mean approved, canonical, publication-eligible, institutionally reviewed, or publicly visible.

## Media safeguards

The source has 21 enriched/media-linked records, 14 records with nonempty image arrays, and 32 image references. All 32 references are absent from the repository and remain source evidence with `repository_asset_available: false` and `publication_media_eligible: false`. Four duplicate-linkage groups remain review evidence. No media is copied into public assets, and no ownership, usage right, natural classification, destination identity, approval, or visibility is inferred.

## Publication and registry invariants

- Green Mountain curated layer remains 180 features.
- Libyan Sahara curated layer remains 69 features.
- Curated natural frontend total remains 249.
- Publication-oriented national GIS count remains 214.
- The approval ledger remains empty.
- The destination registry and source manifest remain unchanged.
- This review adds zero runtime, public, canonical, or publication records.

Every record remains `publication_approved: false`, `canonical_approval: false`, `public_visibility_enabled: false`, `institutional_review_status: UNRESOLVED`, `canonical_destination: null`, and `resolution: UNRESOLVED_NO_AUTOMATIC_REPAIR`.

## Validation and controlled regeneration

Ordinary repository validation is self-contained:

```powershell
python backend/scripts/national_natural_resources_reconciliation.py
python -m pytest -q backend/tests/unit/scripts/test_national_natural_resources_reconciliation.py
```

Governed offline regeneration, when the verified external inputs are available, is explicit:

```powershell
python backend/scripts/national_natural_resources_reconciliation.py build `
  <EXTERNAL_AUDIT_DIRECTORY> `
  <AUTHORITATIVE_SOURCE_GEOJSON>
```

The build command verifies the source size and SHA-256 plus all five external audit hashes before writing. The validator fails closed on provenance, record accounting, routing, overlap, exclusions, media, geometry, governance, registry/curated counts, approval ledger state, absolute paths, and changed-file scope.
