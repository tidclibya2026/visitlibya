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

## Sources inspected

The audit covered development and curated destination datasets, bilingual home and experience routes, detail galleries, responsive-image mappings, reviewed coordinate artifacts, both curated natural-tourism GIS reviews, heritage candidate review, the generated natural-tourism layer, and publication governance policy and ledger. Records cite stable relative repository paths without volatile line numbers.

## Fifteen-unit coverage matrix

| Tier | Coverage unit | Canonical slug / representation | Page and media | Coordinates | Destination GIS | Provenance / identity | Approval |
|---|---|---|---|---|---|---|---|
| PRIMARY | Tripoli — طرابلس | `tripoli`; independent city | EN/AR detail; gallery and responsive media | Review required; candidates are sub-features | None | Canonical repository identity; governed provenance incomplete | False |
| PRIMARY | Benghazi — بنغازي | `benghazi`; independent city | EN/AR detail; gallery and responsive media | Review required; candidates are sub-features | None | Canonical repository identity; governed provenance incomplete | False |
| PRIMARY | Acacus — أكاكوس | `acacus`; independent natural/rock-art destination | EN/AR detail; gallery | Reviewed pair | None | Reviewed coordinate provenance | False |
| PRIMARY | Shahat/Cyrene — شحات/قورينا | No independent slug; represented through `green-mountain` | EN/AR links use parent; responsive media | Identity-specific pair unresolved | No identity-specific layer | City/site/parent relationship unresolved | False |
| PRIMARY | Ghadames — غدامس | `ghadames`; separate related `old-city-ghadames` record | EN/AR detail; gallery and responsive media | Broader record has no reviewed pair; old-city pair not borrowed | None | Institutional GIS review exists; relationship contract unresolved | False |
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

## Development gaps and institutional actions

- **Tripoli and Benghazi:** approve representative geometry and define urban/historic GIS scope.
- **Acacus:** distinguish archaeological and natural GIS responsibilities.
- **Shahat/Cyrene:** decide whether the modern city and archaeological site are one entity, separate parent-child entities, or children of Green Mountain.
- **Ghadames:** define the relationship between `ghadames` and `old-city-ghadames`; do not reuse the latter's coordinate implicitly.
- **Leptis Magna and Sabratha:** establish site boundaries, feature provenance, and detailed layers.
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
3. Shahat/Cyrene, after identity resolution
4. Ghadames, after resolving the broader-city/old-city relationship
5. Acacus, with archaeological and natural scopes separated

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

The registry remains descriptive and review-oriented. It does not publish, approve, or serve as a runtime destination source.
