# Cyrene (Shahat) source reconciliation

## Purpose and governance

This foundation reconciles institutional ArcGIS exports for the unified project identity قورينا – شحات / Cyrene (Shahat). It is deterministic, self-contained, review-only, and fail-closed. It does not create a canonical runtime destination, public GIS layer, authoritative boundary, archaeological interpretation, media-rights decision, institutional approval, or publication eligibility.

The artifact is not loaded by the frontend, backend runtime, API, or database. It adds zero records to the National Destination Registry's publication-oriented GIS count of 214.

## Source evaluation matrix

| Source | Role | Feature classes | Raw records | Decision |
|---|---|---:|---:|---|
| `cyrene_shahhat` / `Cyrene_shahhat.gdb` | Primary thematic | 18 | 1,537 | Retain with record-level review |
| `qurina_cy` / `Qurina_Cy.gdb` | Complementary | 13 | 1,519 | Retain unique evidence; consolidate only proven exact copies |
| `points_world_heritage` / `points_world_heritage.gdb` | Reference identity evidence | 1 | 27 | Retain as review evidence; never treat as publication approval |
| `cyrene1` | Excluded empty source | 0 | 0 | `EMPTY_SOURCE_DATABASE` |

All 32 exports and the portable manifest were parsed. Every export SHA-256, record count, geometry type, layer identity, and source CRS was verified; the manifest has zero export errors. No absolute backup path is stored.

## Raw layers

| Source | Relative layer | Export | Shape | Records |
|---|---|---|---|---:|
| cyrene_shahhat | شحات_ليبيا\استخدامات_الاراضي | `cyrene_shahhat__001.esri.json` | Polygon | 11 |
| cyrene_shahhat | شحات_ليبيا\اماكن | `cyrene_shahhat__002.esri.json` | Polygon | 22 |
| cyrene_shahhat | شحات_ليبيا\طرق | `cyrene_shahhat__003.esri.json` | Polyline | 1,376 |
| cyrene_shahhat | شحات_ليبيا\عيون | `cyrene_shahhat__004.esri.json` | Point | 5 |
| cyrene_shahhat | شحات_ليبيا\مباني | `cyrene_shahhat__005.esri.json` | Polygon | 38 |
| cyrene_shahhat | شحات_ليبيا\محطة_تزود_بالوقود | `cyrene_shahhat__006.esri.json` | Point | 3 |
| cyrene_shahhat | شحات_ليبيا\مدارس | `cyrene_shahhat__007.esri.json` | Point | 11 |
| cyrene_shahhat | شحات_ليبيا\مستشفيات | `cyrene_shahhat__008.esri.json` | Point | 2 |
| cyrene_shahhat | شحات_ليبيا\مسجد | `cyrene_shahhat__009.esri.json` | Point | 11 |
| cyrene_shahhat | شحات_ليبيا\مصرف | `cyrene_shahhat__010.esri.json` | Point | 3 |
| cyrene_shahhat | شحات_ليبيا\مطار_الابرق | `cyrene_shahhat__011.esri.json` | Point | 1 |
| cyrene_shahhat | شحات_ليبيا\مطعم | `cyrene_shahhat__012.esri.json` | Point | 7 |
| cyrene_shahhat | شحات_ليبيا\معبد | `cyrene_shahhat__013.esri.json` | Point | 8 |
| cyrene_shahhat | شحات_ليبيا\معبد_temple | `cyrene_shahhat__014.esri.json` | Polygon | 14 |
| cyrene_shahhat | شحات_ليبيا\مقهى | `cyrene_shahhat__015.esri.json` | Point | 2 |
| cyrene_shahhat | شحات_ليبيا\منتجع | `cyrene_shahhat__016.esri.json` | Point | 3 |
| cyrene_shahhat | شحات_ليبيا\مواقع_اثرية | `cyrene_shahhat__017.esri.json` | Point | 18 |
| cyrene_shahhat | شحات_ليبيا\نزل | `cyrene_shahhat__018.esri.json` | Point | 2 |
| qurina_cy | cyrene\اثار_شحات | `qurina_cy__001.esri.json` | Point | 14 |
| qurina_cy | cyrene\استراحة | `qurina_cy__002.esri.json` | Point | 6 |
| qurina_cy | cyrene\تسوق | `qurina_cy__003.esri.json` | Point | 34 |
| qurina_cy | cyrene\طرق_ش | `qurina_cy__004.esri.json` | Polyline | 1,376 |
| qurina_cy | cyrene\قسم_شرطة | `qurina_cy__005.esri.json` | Point | 4 |
| qurina_cy | cyrene\مباني | `qurina_cy__006.esri.json` | Polygon | 38 |
| qurina_cy | cyrene\محطة_وقود | `qurina_cy__007.esri.json` | Point | 3 |
| qurina_cy | cyrene\مدارس | `qurina_cy__008.esri.json` | Point | 11 |
| qurina_cy | cyrene\مسجد | `qurina_cy__009.esri.json` | Point | 11 |
| qurina_cy | cyrene\مصرف | `qurina_cy__010.esri.json` | Point | 4 |
| qurina_cy | cyrene\مطاعم | `qurina_cy__011.esri.json` | Point | 14 |
| qurina_cy | cyrene\مقاهي | `qurina_cy__012.esri.json` | Point | 2 |
| qurina_cy | cyrene\نزل | `qurina_cy__013.esri.json` | Point | 2 |
| points_world_heritage | points_world_heritage\مدينة_شحات_قورينا | `points_world_heritage__001.esri.json` | Point | 27 |

## Exact duplicate consolidation

Only five byte-identical pairs are consolidated. Each resulting record preserves both complete source references.

| Logical dataset | Records represented once | Second-copy records removed |
|---|---:|---:|
| Roads | 1,376 | 1,376 |
| Buildings | 38 | 38 |
| Schools | 11 | 11 |
| Mosques | 11 | 11 |
| Lodges | 2 | 2 |
| Total | 1,438 | 1,438 |

Raw records total 3,083. After removing only those proven second copies, 1,645 records remain represented: 1,634 clean thematic records and 11 quarantined records.

## Clean thematic inventory

| Collection | Clean records |
|---|---:|
| `heritage_points` | 31 |
| `heritage_polygons` | 14 |
| `natural_context_points` | 14 |
| `visitor_services_points` | 128 |
| `access_roads` | 1,376 |
| `buildings_context` | 71 |
| Total | 1,634 |

Every record preserves original attributes and source geometry. Review IDs bind source identity, relative layer, preserved values, source geometry, and any separate derived review geometry; mutable OBJECTIDs are not sole identities.

## Identity candidate groups

- Three fuel pairs are approximately 13.90–18.43 m apart. They remain six records.
- Three bank pairs are approximately 6.08–15.82 m apart. The fourth `qurina_cy` bank remains an unpaired unique review record.
- Twenty clean restaurant records form a union review group. One additional primary restaurant has invalid geometry and is quarantined.
- Four café records remain a spatially distinct review group.
- Fifty-seven clean cross-source heritage records remain a review union: 31 `heritage_points`, 9 `natural_context_points`, and 17 `visitor_services_points`. By source/layer, these are 26 world-heritage reference records, 14 `qurina_cy` archaeological records, 12 clean `cyrene_shahhat` archaeological-site records, and 5 clean `cyrene_shahhat` temple records. The group intentionally spans thematic collections because it audits cross-source identity evidence; it contains no polygons or quarantined records. Names and proximity do not consolidate them.
- The three quarantined source attribute/geometry misalignments remain linked separately through `geometry_conflicts` and their preserved `proposed_identity_evidence`; they are not clean group members.

## Geometry and identity conflicts

### Invalid heritage geometry

The primary temple layer preserves and quarantines invalid geometry for `معبد باخوس`, `معبد الكابيتاليوم`, and `معبد افروديث`. The primary archaeological-sites layer similarly quarantines `منزل جايوس ماغنوس`, `مسرح 3`, and one unnamed record. No coordinates are invented.

The primary restaurant layer also contains one independently discovered invalid point, `مطعم الكرم العربي`; it is quarantined under the same fail-closed rule.

### Source attribute/geometry misalignment

Three primary archaeological-site records exactly occupy world-heritage coordinates carrying different identities:

- `متحف المنحوتاث` ↔ world reference `معبد الكبيتوليوم`.
- `نبع ابوللو` ↔ world reference `الحمامات الاغريقية`.
- `الحمامات الاغريقية` ↔ world reference `أثار قورينا`.

Original attributes and geometries are unchanged, flagged `SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT`, and quarantined with resolution `UNRESOLVED_NO_AUTOMATIC_REPAIR`. The corresponding geometry-conflict entries remain. The world records are preserved only as proposed identity evidence with approval false. No point is shifted, renamed, replaced, merged, or repaired.

### Qurina CRS conflict

The `qurina_cy` archaeological layer metadata identifies WGS 1984 UTM Zone 33N / EPSG 32633, while the exported JSON reports WKID 4326 although its source geometry values are UTM. Original UTM geometry and both metadata statements are preserved. Each of the 14 records has a separate deterministic WGS 84 review point derived only from its source `x`/`y` attributes and is flagged `CRS_METADATA_GEOMETRY_CONFLICT`.

### Spatial outlier

The world-heritage record `كافي الشلال شحات` at approximately 20.105524, 32.086851 is preserved and quarantined with `SPATIAL_OUTLIER`. It is neither moved nor deleted.

## Unresolved institutional decisions

- Repair or replace invalid geometries from authoritative evidence.
- Resolve the three attribute/geometry identity conflicts.
- Resolve the UTM/4326 metadata conflict and approve an authoritative geometry representation.
- Review fuel, bank, restaurant, café, and heritage candidate identities without proximity-only deduplication.
- Decide the outlier's correct identity and destination membership.
- Supply an authoritative site boundary independently of these inventories.
- Complete destination identity, archaeological interpretation, media rights, institutional review, and publication decisions independently.

Every clean, consolidated, derived, conflict, and quarantined record remains non-public with `publication_approved`, `canonical_approval`, and `public_visibility_enabled` false and institutional review `UNRESOLVED`.

## Deterministic reporting audit

The artifact includes exact source/layer/collection/state and thematic collection/state cross-tabs. Consolidated records contribute both preserved source references to the source cross-tab, so it totals the 3,083 raw references, while the state cross-tab totals the 1,645 represented records.

- State: 1,634 clean; 11 quarantined.
- Heritage review group: 57 clean; 0 quarantined.
- Quarantine reasons: 7 `INVALID_GEOMETRY`; 3 `SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT`; 1 `SPATIAL_OUTLIER`.
- Quality flags: 14 `CRS_METADATA_GEOMETRY_CONFLICT`; 7 `INVALID_GEOMETRY_QUARANTINED`; 3 `SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT`; 1 `SPATIAL_OUTLIER`.

The validator recomputes collection totals, proves clean/quarantine disjointness, requires every identity-group reference to resolve exactly once to a clean record, and rejects duplicate thematic membership. Quarantined evidence is referenced only through conflict and quarantine structures.

## Validation

```text
python backend/scripts/cyrene_source_reconciliation.py
python backend/scripts/destination_registry.py
python -m pytest -q backend/tests/unit/scripts/test_cyrene_source_reconciliation.py backend/tests/unit/scripts/test_destination_registry.py
python -m pytest -q backend/tests/unit
python backend/scripts/publication_governance.py
python backend/scripts/publication_generation.py validate-manifest
python backend/scripts/publication_generation.py verify
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
```
