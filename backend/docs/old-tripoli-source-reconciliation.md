# Old Tripoli heritage source reconciliation

## Purpose and status

This foundation preserves and evaluates the 430 placemarks in the institutionally held Old Tripoli KML. It is deterministic, self-contained, review-only evidence. It is not a runtime source, curated public GIS layer, canonical destination record, route, institutional approval, or publication decision.

The source is registered as `tripoli-old-city`; its verified SHA-256 is `26ffc9519ebccfaafbd029e070dd21e736c0f0bc839b36231668792d6866eab5`. The repository artifact records portable source labels and corrected external-audit hashes without storing local Windows paths. Ordinary validation uses the committed review artifact and does not require the external KML.

## Identity architecture

- `tripoli` remains the modern city and broad public tourism destination.
- `old-tripoli` is a proposed distinct nested historic urban heritage destination.
- `tripoli CONTAINS_HERITAGE_DESTINATION old-tripoli` is review-governance metadata only.

The relationship does not merge the identities, create a new public runtime destination, inherit a coordinate, or establish a boundary. No monument, service, point, line, polygon, bounding box, envelope, or point distribution becomes a destination anchor or boundary.

## Deterministic accounting

| Evidence class | Count |
|---|---:|
| Raw source placemarks | 430 |
| Points | 135 |
| Polygons | 10 |
| Site-oriented review geometries | 145 |
| LineStrings | 285 |
| Named LineStrings | 49 |
| Unnamed LineStrings | 236 |
| Technical quarantine | 0 |
| Safe duplicate members | 0 |
| Clean review representatives | 430 |
| Resolved source ordinals | 430 |

Every ordinal from 1 through 430 appears exactly once. No source record is deleted or silently consolidated.

## Review routing

| Review collection | Count |
|---|---:|
| `CONTEXTUAL_URBAN_NETWORK_REVIEW` | 285 |
| `RELIGIOUS_HERITAGE` | 30 |
| `ACCESS_AND_VISITOR_ROUTES` | 26 |
| `HISTORIC_BUILDINGS_AND_URBAN_HERITAGE` | 24 |
| `VISITOR_SERVICES_AND_FACILITIES` | 19 |
| `ARCHAEOLOGICAL_AND_MONUMENTAL_HERITAGE` | 13 |
| `REVIEW_POLYGONS_AND_AREAS` | 10 |
| `TRADITIONAL_MARKETS_AND_CRAFTS` | 8 |
| `UNRESOLVED_OTHER_CONTEXT` | 8 |
| `LANDSCAPE_AND_OPEN_SPACES` | 5 |
| `MUSEUMS_AND_CULTURAL_FACILITIES` | 2 |

Routing is a review aid and grants no canonical archaeological, religious, cultural, visitor-service, or publication classification.

## Contextual urban networks

All 285 LineStrings use `CONTEXTUAL_URBAN_NETWORK_REVIEW`. The 236 unnamed lines and 49 named lines preserve complete geometry, folder, style, description, and OSM-like fields such as `osm_id`, `fclass`, `oneway`, `maxspeed`, `layer`, `bridge`, and `tunnel`.

Neither names nor OSM-like metadata prove historical, heritage, canonical, official-route, or visitor-route status. The validator prohibits inferring those semantics from folder membership, spatial location, proximity to monuments, unnamed geometry, OSM fields, or a route name alone. Any collection value claiming that these lines are proven historic networks is forbidden.

## Polygon and boundary safeguards

All ten polygons remain under `REVIEW_POLYGONS_AND_AREAS`. They are not authoritative Old Tripoli boundaries, public boundaries, or automatically accepted footprints. The audit preserves the bounding-box overlap candidate between ordinals 136 and 137 solely as spatial review evidence. No boundary is derived from polygons, lines, envelopes, bounding boxes, or point distributions.

## Duplicate and conflict review

There are no safe automatic duplicate members. The exact-coordinate/different-name conflict between ordinal 23 (`الساحة ميدان الشهداء`) and ordinal 50 (`الساحة الشهداء`) remains two separate records. Fifteen same-name/different-geometry groups and thirty near-point pairs remain unresolved review evidence. Similar names, exact coordinates with conflicting identities, and proximity do not authorize automatic deduplication.

## Identity normalization review

Source identity values remain unchanged. Proposed normalization is stored separately and requires human review:

| Source value | Proposed review identity |
|---|---|
| `برج "القديس جورج"` | `برج القديس جورج` |
| `الكنيسة الأرتذوكسية` | `الكنيسة الأرثوذكسية` |
| `الحنفية (الشيشمة) العثمانية` | `الحنفية العثمانية` |

These proposals do not establish canonical identity.

## Media evidence

The artifact preserves 114 records containing media references. References remain source evidence only and grant no ownership, usage rights, identity authority, spatial authority, or publication permission. No media is copied into public assets.

## Governance and promotion gates

Every record remains `publication_approved: false`, `canonical_approval: false`, `public_visibility_enabled: false`, `institutional_review_status: UNRESOLVED`, `canonical_destination: null`, and `resolution: UNRESOLVED_NO_AUTOMATIC_REPAIR`.

Future promotion requires independently reviewed destination identity, feature identity, geometry semantics, authoritative boundary evidence if supplied, provenance, media rights, institutional approval, deterministic generation, and separately authorized public integration. This phase grants none of those outcomes and adds zero records to the publication-oriented national GIS count of 214.

## Validation

Run:

```powershell
python backend/scripts/old_tripoli_source_reconciliation.py
python -m pytest -q backend/tests/unit/scripts/test_old_tripoli_source_reconciliation.py
```

Offline regeneration from the governed external evidence is intentionally separate:

```powershell
python backend/scripts/old_tripoli_source_reconciliation.py build <audit-directory> <source-kml>
```
