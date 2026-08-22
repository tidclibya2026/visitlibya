# Ghadames GIS source reconciliation

## Purpose and governance

This foundation deterministically reconciles institutionally held ArcGIS evidence for Ghadames. It is review-only and is not loaded by the frontend, API, backend runtime, database, or public map. It grants no canonical identity, destination membership, archaeological classification, boundary authority, UNESCO status, institutional approval, publication eligibility, or public visibility.

The geodatabases are institutionally held, but fields such as `osm_id` support describing much of their underlying content as OSM-derived. Institutional custody does not establish institutional authorship of the original OSM content.

## Identity architecture

`ghadames` is the broader tourism destination. `old-city-ghadames` is a distinct heritage core. Their governed relationship is:

`ghadames CONTAINS_HERITAGE_CORE old-city-ghadames`

The identities are not merged. The Old City coordinate and source polygon are not inherited by broader Ghadames. Records are represented once, not duplicated to express containment, and the two identities retain separate evidence and publication requirements.

## Source-copy decision

Three `gadamas.gdb` copies were inspected. Each contains six feature classes, no tables, and 770 records. All three are byte-identical and logically identical across layer identity, ordered schema, attributes, and canonicalized geometry.

| Source | Decision | Records represented |
|---|---|---:|
| `gadamas_flash16` | Primary | 770 |
| `gadamas_flash16_cloud` | Exact duplicate excluded from derived counting | 0 |
| `gadamas_flash8_cloud` | Exact duplicate excluded from derived counting | 0 |

The two excluded copies account for 1,540 redundant record copies. Consolidation loses zero unique records, introduces zero schema conflicts, introduces zero geometry conflicts, and leaves zero unique complementary records.

## Primary layers

| Layer | Geometry | Records | Clean collection |
|---|---|---:|---|
| `buildings` | Polygon | 81 | `buildings_context` |
| `natural` | Polygon | 15 | `natural_context` |
| `places` | Point | 4 | `places_context` |
| `roads` | Polyline | 599 | `access_roads` |
| `select_landuse` | Polygon | 20 | `landuse_context` |
| `select_point` | Point | 51 | Routed by exact preserved source name into review collections |
| Total |  | 770 |  |

Every record preserves its original layer, ordered attribute values, complete source geometry, WKID 4326, and deterministic content-derived review ID. Mutable ArcGIS OIDs are never the sole identity.

## Clean review collections

| Collection | Records | Meaning |
|---|---:|---|
| `buildings_context` | 81 | Building context; no ownership or heritage interpretation |
| `natural_context` | 15 | Natural-context polygons |
| `places_context` | 4 | Source place points |
| `access_roads` | 599 | Source road network context |
| `landuse_context` | 20 | Source land-use context |
| `heritage_core_candidates` | 5 | Spatial review candidates only |
| `visitor_services` | 28 | Exact-name review routing for accommodation, services, markets, and visitor facilities |
| `other_tourism_context` | 18 | Ambiguous or broader tourism/context points retained without forced classification |
| Total | 770 |  |

Collection placement is review routing, not canonical destination membership or publication approval.

## Boundary evidence and quarantine

Three source polygons are preserved separately and quarantined under `UNRESOLVED_BOUNDARY_SEMANTICS`:

- `old_city.shp`: one polygon named `مدينة غدامس القديمة`; plausible Old City identity evidence, but authority unresolved.
- `zone.shp`: one polygon; semantic meaning unresolved.
- `المنطقة _الثالثة.shp`: one polygon; semantic meaning unresolved.

No polygon is described as an authoritative UNESCO boundary, protection zone, or buffer zone. Canonical boundary approval, UNESCO boundary approval, UNESCO buffer-zone approval, publication approval, public visibility, and canonical approval remain false. Institutional review remains unresolved.

## Spatial review evidence

Five points geometrically intersect the unresolved `old_city` polygon:

- `مدينة غدامس القديمة`
- `ساحة الجامع العتيق`
- `الجامع العتيق`
- `ساحة جرسان`
- `مقهى توجدة`

This intersection grants no canonical membership, archaeological classification, UNESCO membership, boundary authority, or publication eligibility.

## False-positive protection

Name similarity never establishes destination membership. In particular, `فندق الغدامسية` is documented by existing repository review evidence as a Tripoli record and is excluded from this reconciliation. No broad search result is promoted into Ghadames evidence merely because its name resembles Ghadames.

## Deterministic accounting

- Database copy records inspected: 2,310
- Duplicate source-copy records excluded: 1,540
- Unique primary database records: 770
- Boundary evidence records: 3
- Total represented evidence: 773
- Publication-oriented GIS records added: 0
- National Destination Registry GIS total: 214

## Promotion gates

Future promotion requires independent identity review, feature classification, authoritative boundary semantics, provenance review, institutional approval, deterministic generation, publication approval, and explicit public-map integration. None occurs in this phase.

## Validation

```text
python backend/scripts/ghadames_source_reconciliation.py
python backend/scripts/destination_registry.py
python -m pytest -q backend/tests/unit/scripts/test_ghadames_source_reconciliation.py backend/tests/unit/scripts/test_destination_registry.py
python -m pytest -q backend/tests/unit
python backend/scripts/publication_governance.py
python backend/scripts/publication_generation.py validate-manifest
python backend/scripts/publication_generation.py verify
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
git diff --check
```
