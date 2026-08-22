# Acacus institutional KML reconciliation

## Purpose and governance

This foundation deterministically reconciles the current institutional `اكاكوس.kml` source for review. It is not a runtime source, detailed GIS layer, public map, canonical classification, institutional approval, or publication decision. Every clean, duplicate-member, and quarantined record remains unapproved, non-canonical, non-public, and institutionally unresolved.

The KML is the current primary reconciliation source. Its SHA-256 is `641ab45b3ace5e77eae78e63931b08fb925f2494a536f3736d74e01bf5ed2988`. Earlier `akakuas.gdb` evidence cannot override it. Existing registered source hashes and the source manifest remain unchanged because the KML matches the registered `acacus-features` source.

## Destination architecture

The canonical destination remains `acacus` / `تادرارت أكاكوس` / `Tadrart Acacus`, modeled as `COMPOSITE_CULTURAL_NATURAL_DESTINATION` with five governed dimensions:

- `ARCHAEOLOGY`
- `ROCK_ART_AND_INSCRIPTIONS`
- `CULTURAL_HERITAGE`
- `NATURE_AND_DESERT_LANDSCAPE`
- `GEOLOGY_AND_GEOMORPHOLOGY`

Water, entrances, routes, settlements, visitor services, caves, shelters, and unresolved context support the composite destination without replacing those dimensions. Routing is review-only and grants no canonical classification.

The promotional wording `المتحف العالمي المفتوح` / `Open-air world museum` remains source-verification-required, unofficial, unapproved, and absent from runtime promotion.

## Deterministic accounting

| State | Count |
|---|---:|
| Raw source ordinals | 430 |
| Clean Acacus representatives | 360 |
| Safe duplicate-member references | 66 |
| Quarantined/cross-destination records | 4 |
| Reconciled review records: clean plus quarantine | 364 |

Every ordinal from 1 through 430 resolves exactly once. Safe duplicate members retain full source evidence under deterministic representatives and are not deleted.

## Clean routing

| Collection | Count |
|---|---:|
| `ARCHAEOLOGY` | 0 |
| `ROCK_ART_AND_INSCRIPTIONS` | 35 |
| `CULTURAL_HERITAGE` | 0 |
| `NATURE_AND_DESERT_LANDSCAPE` | 57 |
| `GEOLOGY_AND_GEOMORPHOLOGY` | 22 |
| `WATER_RESOURCES` | 19 |
| `ENTRANCES_AND_VISITOR_ROUTES` | 10 |
| `SETTLEMENTS_AND_VISITOR_SERVICES` | 43 |
| `CAVES_AND_SHELTERS` | 9 |
| `UNRESOLVED_OTHER_CONTEXT` | 165 |
| Total | 360 |

## Quarantine

Four source records remain preserved outside clean Acacus routing:

- Ordinal 23, `وادي ماتخيندوش`: `CROSS_DESTINATION_SCOPE_AND_COORDINATE_CONFLICT`.
- Ordinal 100, `بئر تنزه`: `MISSING_GEOMETRY`.
- Ordinal 197, blank identity: `MISSING_IDENTITY_AND_GEOMETRY`.
- Ordinal 199, administrative `Ghat` polygon: `EXTERNAL_ADMINISTRATIVE_POLYGON_UNRESOLVED_SCOPE`.

The Ghat polygon is not an Acacus boundary.

### Wadi Mathendous

Institutional clarification routes Wadi Mathendous to proposed `UBARI_MESSAK_REVIEW`, with proposed theme `ROCK_ART_AND_INSCRIPTIONS`, high review priority, and notable subject `نقش القطتين المتصارعتين`. Canonical destination assignment remains null.

The KML geometry 10.516772, 24.957273 and source X/Y values 12.245440 / 26103950 are preserved unchanged. The possible interpretation 12.245440, 26.103950 is review evidence only and does not replace the source geometry. Resolution remains `UNRESOLVED_NO_AUTOMATIC_REPAIR`. The fighting-cats description is institutional review evidence, not publication-approved copy.

## Uan Muhuggiag

Ordinal 191, `كهف وان موهجاج`, remains in `CAVES_AND_SHELTERS`. `Uan Muhuggiag` is recorded only as a proposed English identity requiring verification. Proposed cross-domain review tags cover archaeology, cultural heritage, rock art, and mummy-discovery association. These tags do not grant canonical classification, approval, visibility, or publication.

## Identity conflicts and hotel safeguard

Two exact-coordinate/different-name groups remain separate: ordinals 154/396 and 34/278. No name-based equivalence is approved.

Local `فندق أكاكوس` records 181 and 423 remain separate near-coordinate review records. Neither is associated with the unrelated Tripoli hotel, and no operational or publication-ready status is inferred.

## Registry treatment

The registry separately records 430 source ordinals, 364 reconciled review records, 360 clean representatives, four quarantined/cross-destination records, and 66 duplicate-member references. These values do not contribute to `gis_record_count`; the publication-oriented national GIS total remains 214.

## Validation

```text
python backend/scripts/acacus_source_reconciliation.py
python backend/scripts/destination_registry.py
python -m pytest -q backend/tests/unit/scripts/test_acacus_source_reconciliation.py backend/tests/unit/scripts/test_destination_registry.py
python -m pytest -q backend/tests/unit
python backend/scripts/publication_governance.py
python backend/scripts/publication_generation.py validate-manifest
python backend/scripts/publication_generation.py verify
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
git diff --check
```
