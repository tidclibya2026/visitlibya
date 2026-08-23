# National Destination Registry review foundation

## Purpose and governance role

The National Destination Registry is a deterministic, read-only review artifact. It describes repository coverage and development gaps for fifteen national coverage units. It is not loaded by the backend application or static frontend and cannot publish content, change runtime visibility, grant institutional approval, or replace publication-governance decisions.

The authoritative validator is `backend/scripts/destination_registry.py`. Missing or ambiguous evidence is recorded explicitly and remains fail-closed for governed publication.

## Two-tier development model

`PRIMARY` identifies the nine destinations prioritized for initial content and GIS development. `COMPLEMENTARY` identifies six destinations for the subsequent expansion phase. The tier is a planning label only: it grants neither institutional approval nor runtime eligibility, and it cannot convert a repository mention, media asset, published flag, or spatial feature into a canonical destination.

Primary: Tripoli, Benghazi, Acacus, Shahat/Cyrene, Ghadames, Sabratha, Leptis Magna, Green Mountain, and natural/desert lakes.

Complementary: Waddan, Hun, Sokna, Nafusa Mountains, Awjila, and Girza.

## Entity and representation distinctions

- An **independent canonical destination** has its own slug in `backend/data/dev/destinations.json`.
- A **geographic city or region** can contain many sites; a sub-feature coordinate is not automatically its representative coordinate.
- An **archaeological or heritage site** needs a stable identity distinct from nearby settlements where evidence requires it.
- A **natural destination** can combine landscape and cultural evidence without merging their review requirements.
- A **thematic or nested collection** belongs to a parent destination and gains no independent identity from media or GIS coverage.
- A **repository mention** is visitor-facing text without a canonical record or route.
- A **GIS layer** is reviewed spatial evidence, not institutional publication approval.

## Public visibility and approval

The committed approval ledger is empty. Every registry record therefore sets `institutional_publication_approved` to `false`. Existing public or mentioned material uses `LEGACY_PUBLIC_BASELINE_NOT_INSTITUTIONAL_APPROVAL`; an absent future governed record is `GOVERNED_RECORD_INELIGIBLE`. Development priority never changes either result.

Identity-model resolution is equally non-authoritative for publication. A regional relationship describes geography; a canonical identity describes a governed destination concept; a public runtime route is an implementation artifact; and institutional publication approval requires a separate effective governance decision. None implies another.

## Resolved project identity models

### قورينا – شحات / Cyrene (Shahat)

The project model resolves Cyrene and Shahat as one unified destination, `UNIFIED_CYRENE_SHAHAT_DESTINATION`, within the Green Mountain region through `WITHIN_REGION`. Its proposed future slug is `cyrene`. The authoritative runtime dataset still has no `cyrene` record, so the current canonical slug remains `null`, the existing visitor link still routes through `green-mountain`, and runtime promotion is `NOT_PROMOTED`. Destination-level coordinates, archaeological GIS scope, Shahat service context, evidence completion, and institutional publication review remain required.

A self-contained source reconciliation now evaluates 3,083 raw records from 32 institutional exports. It consolidates only 1,438 proven byte-identical second copies, preserves 1,637 clean thematic records, and quarantines 8 records. This is non-public review evidence, not a detailed GIS layer, runtime source, canonical coordinate, boundary, or approval, and it adds zero to the registry-scoped GIS count of 214.

### Ghadames and Old City of Ghadames

`ghadames` remains the broader tourism destination. It contains the separately canonical `old-city-ghadames` historic and World Heritage core through `CONTAINS_HERITAGE_CORE`. The broader project model may encompass the modern city, Old City, oasis, surrounding desert, and cultural landscape, but it defines no GIS boundary. The Old City coordinate is not inherited by broader Ghadames, and each identity retains separate evidence and publication requirements.

The review-only Ghadames source reconciliation represents 770 unique primary-geodatabase records plus three quarantined boundary-evidence records. It excludes 1,540 records from two byte-identical database copies, adds zero publication-oriented GIS records, and does not change the registry GIS total of 214. Its 773 evidence records are tracked separately from detailed GIS coverage; `gis_layer_present` remains false.

### Acacus

Acacus is modeled as `COMPOSITE_CULTURAL_NATURAL_DESTINATION` with five governed dimensions: `ARCHAEOLOGY`, `ROCK_ART_AND_INSCRIPTIONS`, `CULTURAL_HERITAGE`, `NATURE_AND_DESERT_LANDSCAPE`, and `GEOLOGY_AND_GEOMORPHOLOGY`. Future GIS design must separate or explicitly relate archaeological features, rock-art features, natural landscapes, geology and geomorphology, and visitor routes and services.

The review-only Acacus source reconciliation accounts for 430 KML source ordinals as 360 clean representatives, 66 safe duplicate-member references, and four quarantined or cross-destination records. Clean plus quarantine produces 364 reconciled review records. These counters are separate from detailed/publication GIS coverage: `gis_layer_present` remains false, `gis_record_count` remains zero, and the national publication-oriented total remains 214.

`المتحف العالمي المفتوح` / `Open-air world museum` is recorded only as a proposed promotional identity. The exact phrase was not found as an authoritative repository title, so it remains `SOURCE_VERIFICATION_REQUIRED`, is not an official UNESCO title, and grants no approval.

### Tripoli and Old Tripoli

`tripoli` remains the modern city and broad public destination. `old-tripoli` is recorded only as a proposed distinct nested historic urban heritage identity through `CONTAINS_HERITAGE_DESTINATION`; this relationship is review-governance metadata and creates no new public runtime destination, route, anchor, or boundary.

The review-only Old Tripoli source reconciliation preserves all 430 KML source records: 145 site-oriented point or polygon review geometries and 285 contextual urban-network LineStrings. The 236 unnamed and 49 named LineStrings remain contextual evidence rather than proven historic, heritage, canonical, official, or visitor routes. All ten polygons remain non-authoritative review areas. The reconciliation adds zero publication-oriented GIS records, leaves `gis_layer_present` false and `gis_record_count` zero, and does not change the national total of 214.

## Sources inspected

The audit covered development and curated destination datasets, bilingual home and experience routes, detail galleries, responsive-image mappings, reviewed coordinate artifacts, both curated natural-tourism GIS reviews, heritage candidate review, the generated natural-tourism layer, and publication governance policy and ledger. Records cite stable relative repository paths without volatile line numbers.

## Fifteen-unit coverage matrix

| Tier | Coverage unit | Canonical slug / representation | Page and media | Coordinates | Destination GIS | Provenance / identity | Approval |
|---|---|---|---|---|---|---|---|
| PRIMARY | Tripoli — طرابلس | `tripoli`; independent city | EN/AR detail; gallery and responsive media | Review required; candidates are sub-features | None | Canonical repository identity; governed provenance incomplete | False |
| PRIMARY | Benghazi — بنغازي | `benghazi`; independent city | EN/AR detail; gallery and responsive media | Review required; candidates are sub-features | None | Canonical repository identity; governed provenance incomplete | False |
| PRIMARY | Acacus — أكاكوس | `acacus`; composite cultural-natural destination | Existing EN/AR detail; no identity-model copy change | Reviewed pair preserved | None | Five-domain project model; promotional phrase needs source verification | False |
| PRIMARY | Cyrene (Shahat) — قورينا – شحات | Future `cyrene`; currently represented through `green-mountain` | No dedicated route; existing parent link/media unchanged | Identity-specific pair unresolved | No identity-specific layer | Unified project model within Green Mountain; evidence completion required | False |
| PRIMARY | Ghadames — غدامس | `ghadames` contains distinct `old-city-ghadames` heritage core | Existing EN/AR detail/gallery unchanged | Broader record has no reviewed pair; Old City pair not borrowed | None | Containment model resolved; boundaries and separate approvals pending | False |
| PRIMARY | Sabratha — صبراتة | `sabratha`; independent heritage site | EN/AR detail; gallery | Reviewed pair | None | Reviewed coordinate provenance | False |
| PRIMARY | Leptis Magna — لبدة الكبرى | `leptis-magna`; independent heritage site | EN/AR detail; gallery | Reviewed pair | None | Reviewed coordinate provenance | False |
| PRIMARY | Green Mountain — الجبل الأخضر | `green-mountain`; aggregate region | EN/AR detail; gallery and responsive media | Aggregate representative point unresolved | 180 reviewed records | Governed review layer; not approval | False |
| PRIMARY | Natural/desert lakes — البحيرات الطبيعية والصحراوية | No independent slug; nested under `desert` | EN/AR parent route; responsive media | Not applicable to collection | 34 lake-category records in 69-record Sahara layer | Governed subset; heritage exceptions separated | False |
| COMPLEMENTARY | Waddan — ودّان | No canonical record; Arabic route mention only | No detail route or destination media contract | None | None | Identity and provenance required | False |
| COMPLEMENTARY | Hun — هون | No canonical record; Arabic route/festival mention only | No detail route or destination media contract | None | None | Identity and provenance required | False |
| COMPLEMENTARY | Sokna — سوكنة | No canonical record; Arabic route/festival mention only | No detail route or destination media contract | None | No destination layer; one named spring remains in parent Sahara layer | City identity must remain separate from sub-feature | False |
| COMPLEMENTARY | Nafusa Mountains — جبل نفوسة | `nafusa`; independent aggregate region | EN/AR detail; gallery and responsive media | Coordinate review reports no match | None | Canonical repository identity; regional scope unresolved | False |
| COMPLEMENTARY | Awjila — أوجلة | `awjila`; independent oasis city | EN/AR detail; gallery and responsive media | Facility candidates only; review required | None | Canonical identity; permanent provenance/media review incomplete | False |
| COMPLEMENTARY | Girza — قِرزة الأثرية | Not found in audited repository sources | No route or media contract | None | None | Full authoritative identity package required | False |

## Verified GIS counts and non-duplication

- `backend/data/gis/green-mountain-tourism-curated.review.json` contains 180 records in `green-mountain-tourism-curated` for `green-mountain`.
- `backend/data/gis/libyan-sahara-tourism-curated.review.json` contains 69 records in `libyan-sahara-tourism-curated` for `desert`; exactly 34 use primary category `البحيرات الطبيعية والصحراوية`.
- The registry reports 214 scoped records: the 180-record Green Mountain layer plus the documented 34-record lakes subset. It does not add the entire 69-record Sahara parent layer or double-count the Sokna-named spring as destination coverage.
- Heritage candidates 832 and 913 remain outside the public natural-tourism layer.

## Controlled coverage vocabulary

- `FULL_GOVERNED_GIS_COVERAGE`: an authoritative review layer covers the unit; this is not approval.
- `PUBLIC_DESTINATION_WITHOUT_DETAILED_GIS`: a canonical public destination exists without a destination-specific curated layer.
- `NESTED_GIS_COLLECTION`: an explicitly selected category belongs to a parent layer.
- `HERITAGE_IDENTITY_REVIEW_REQUIRED`: public representation exists but identity semantics remain unresolved.
- `PARTIAL_REPOSITORY_COVERAGE`: repository mentions exist without a canonical destination package.
- `NOT_FOUND`: audited sources contain no identity record or visitor representation for the coverage unit.

Representation, priority, entity, coordinate, and identity vocabularies are enforced by the validator. Unknown values fail validation.

Identity-model vocabularies add `PROJECT_MODEL_RESOLVED`, `REPOSITORY_EVIDENCE_ONLY`, and `INSTITUTIONAL_REVIEW_REQUIRED`; runtime states `NOT_PROMOTED` and `REVIEW_REQUIRED`; relationships `WITHIN_REGION` and `CONTAINS_HERITAGE_CORE`; controlled destination dimensions; and promotional verification states `SOURCE_VERIFICATION_REQUIRED` and `VERIFIED_IN_REPOSITORY`.

## Development gaps and institutional actions

- **Tripoli and Benghazi:** approve representative geometry and define urban/historic GIS scope.
- **Acacus:** implement a multi-domain architecture separating or relating archaeology, rock art, natural landscapes, geology/geomorphology, routes, and visitor services; verify promotional wording before public use.
- **Cyrene (Shahat):** retain the resolved unified project identity within Green Mountain while completing archaeological-site scope, Shahat service context, coordinates, evidence, and future runtime review.
- **Ghadames:** define the broader destination boundary and Old City heritage-core containment without reusing the latter's coordinate or merging their publication requirements.
- **Leptis Magna and Sabratha:** review-only heritage GIS scope contracts now define anchor provenance, unresolved boundaries, future taxonomy, evidence gates, and separate institutionally sourced point inventories (51 and 39 records). The 90 points are non-public review evidence, not detailed or published layers, and do not change the registry-scoped GIS total; authoritative boundaries and verified feature promotion remain required.
- **Green Mountain:** complete institutional review and aggregate geometry decisions.
- **Lakes:** retain as a Sahara sublayer unless institutional architecture authorizes another model.
- **Waddan, Hun, and Sokna:** supply canonical bilingual identities, provenance, reviewed coordinates, media rights, and GIS scopes.
- **Nafusa Mountains:** define regional boundaries and constituent settlements.
- **Awjila:** replace facility-only coordinate evidence with an authoritative destination-level decision and complete permanent media/provenance review.
- **Girza:** supply the full authoritative identity and evidence package; no repository representation was found.

## Adding or promoting records

Future additions require a unique stable ID and coverage key, relative evidence paths, deterministic ordering, controlled vocabulary values, and direct GIS count verification. Absent evidence must remain `null`, `false`, empty, or explicitly unresolved. Promotion into a governed canonical record additionally requires institutionally resolved identity and relationships, reviewed bilingual names, authoritative coordinates where applicable, provenance, media rights, GIS scope, and separate publication-governance gates. Editing this registry cannot create a route, runtime record, or approval.

## Phased GIS expansion roadmap

### Phase A — Primary archaeological and heritage destinations

1. Leptis Magna
2. Sabratha
3. Cyrene archaeological-site scope with Shahat visitor-service context, using the resolved unified identity within Green Mountain
4. Ghadames destination boundary with the separately canonical Old City heritage core
5. Acacus multi-domain layers for archaeology, rock art, cultural heritage, natural landscape, geology/geomorphology, routes, and visitor services

### Phase B — Primary urban and regional destinations

1. Tripoli historic-city layer
2. Benghazi urban/cultural layer
3. Green Mountain institutional review completion
4. Natural/desert lakes retained as a governed Sahara sublayer

### Phase C — Complementary destinations

1. Waddan
2. Hun
3. Sokna
4. Nafusa Mountains
5. Awjila
6. Girza

## Validation

```text
python -m json.tool backend/data/destinations/national-destination-registry.review.json
python backend/scripts/destination_registry.py
python -m pytest -q backend/tests/unit/scripts/test_destination_registry.py
python backend/scripts/publication_governance.py
python backend/scripts/publication_generation.py validate-manifest
python backend/scripts/publication_generation.py verify
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
```

The registry remains descriptive and review-oriented. This phase creates no route, GIS layer, runtime destination, or publication approval and does not serve as a runtime destination source.
