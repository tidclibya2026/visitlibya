# Primary heritage GIS foundation

## Purpose and non-public scope

This phase creates deterministic, evidence-backed GIS **scope contracts** for Leptis Magna — لبدة الكبرى and Sabratha — صبراتة. The contracts define what future heritage GIS may contain, which evidence is required, and which approval gates remain open. They are review-only metadata: they are not GeoJSON feature layers, are not backend or frontend runtime inputs, grant no institutional approval or publication eligibility, and create no public map.

The implementation changes no database, API, route, curated destination runtime record, natural-tourism layer, publication ledger, or protected generated artifact.

## Site anchors are not boundaries

A site anchor is one reviewed point linked to a canonical destination identity. It can locate the destination at review level, but it does not describe the site's extent. A boundary is authoritative polygonal geometry with its own legal, management, survey, provenance, and institutional review requirements. A point must never be relabeled as an entrance, representative display point, boundary centroid, facility, site polygon, protection zone, or buffer zone without evidence establishing that role.

## Scope contracts are not published GIS layers

The two JSON files describe controlled categories, evidence gates, gaps, and governance status. Their empty `candidate_features` arrays are deliberate. A detailed GIS layer would contain verified feature instances and geometries; a published layer would additionally pass institutional and publication governance. Therefore the registry records `gis_scope_contract_present: true` while retaining `gis_layer_present: false`, zero feature records, and `PUBLIC_DESTINATION_WITHOUT_DETAILED_GIS` coverage. Scope contracts add nothing to the existing registry-scoped GIS total of 214.

## Evidence sources inspected

- `backend/data/destinations/national-destination-registry.review.json`
- `backend/data/gis/canonical-destination-coordinate-review.json`
- `backend/data/gis/heritage-candidates.review.json`
- Existing reviewed and curated GIS datasets under `backend/data/gis/`, including institutional audit and source metadata
- `backend/data/dev/destination-coordinates.reviewed.json`
- `backend/data/dev/destinations.json`
- `assets/js/data/curated-destinations.js`, trip-map sources, destination galleries, and responsive media metadata
- English and Arabic home, experience, and heritage pages
- Atlas-derived repository review data and the scripts that generated candidate review evidence
- Publication policy, generation manifest, legacy baseline, and the empty approval ledger

Repository-wide searches covered `leptis-magna`, `Leptis Magna`, `لبدة`, `لبدة الكبرى`, `sabratha`, `Sabratha`, and `صبراتة`. External sources were not browsed or scraped.

## Current evidence matrices

### Leptis Magna

| Dimension | Finding | Authority in this phase |
|---|---|---|
| Canonical identity | `leptis-magna`; لبدة الكبرى / Leptis Magna; `ndr-leptis-magna`; archaeological heritage site; PRIMARY | Repository identity confirmed; not institutional publication approval |
| Site anchor | Longitude `14.2883012`, latitude `32.6389502` | Reviewed canonical destination/site anchor only |
| Exact provenance | `backend/data/dev/destination-coordinates.reviewed.json`, `slug:leptis-magna`, `مواقع التراث العالمي الخمسة_LY.kml#Placemark-1`; canonical review feature `fp-0ce1a2534b980be1145494f4` | Coordinate evidence preserved exactly |
| Heritage reference | English and Arabic heritage pages identify Leptis Magna / لبدة الكبرى in the World Heritage presentation | Identity and visitor context only |
| Municipality/geographic label | Development data says `Al Khums · Northwest Coast`; candidate source material contains related locality descriptions | Not a site boundary or proof of feature membership |
| Media | `imges/Leptis Magna3.jpeg`, `imges/Leptis Magna1.jpg`, `imges/Leptis Magna.jpeg` | Identity and visitor presentation only |
| Detailed candidates | Canonical review reports 21 discovered candidates, including the destination-level anchor and name-matched sub-features/facilities | None promoted; feature identity and membership review incomplete |
| Boundary | No authoritative polygon found | `AUTHORITATIVE_BOUNDARY_REQUIRED` |

### Sabratha

| Dimension | Finding | Authority in this phase |
|---|---|---|
| Canonical identity | `sabratha`; صبراتة / Sabratha; `ndr-sabratha`; archaeological heritage site; PRIMARY | Repository identity confirmed; not institutional publication approval |
| Site anchor | Longitude `12.484983`, latitude `32.805035` | Reviewed canonical destination/site anchor only |
| Exact provenance | `backend/data/dev/destination-coordinates.reviewed.json`, `slug:sabratha`, `مواقع التراث العالمي الخمسة_LY.kml#Placemark-2`; canonical review feature `fp-e602be9583f488fb120439db` | Coordinate evidence preserved exactly |
| Heritage reference | English and Arabic heritage pages identify Sabratha / صبراتة in the World Heritage presentation | Identity and visitor context only |
| Municipality/geographic label | Development data says `Sabratha · Northwest Coast`; candidate source context includes صبراتة and الساحل الغربي | Not a site boundary or proof of feature membership |
| Media | `imges/Sabratha.jpg`, `imges/Sabratha.jpeg` | Identity and visitor presentation only |
| Detailed candidates | Canonical review reports 63 discovered candidates, including the destination-level anchor and name-matched sub-features/facilities | None promoted; feature identity and membership review incomplete |
| Boundary | No authoritative polygon found | `AUTHORITATIVE_BOUNDARY_REQUIRED` |

The reviewed anchor pairs agree across the reviewed-coordinate file, canonical review best candidate, and development destination record. Candidate descriptions may contain rounded or other coordinates, but they do not replace the exact reviewed pairs. Facilities, hotels, hostels, photographs, captions, and similarly named records are not promoted to site anchors or detailed features.

## Candidate-feature decision

Both contracts use an empty `candidate_features` array. The repository contains destination-name matches and possible monuments, structures, museums, facilities, and related records, but this audit found no feature instance that had completed all required gates: stable source identity, exact destination membership, feature-level canonical identity, controlled heritage classification, authoritative geometry and capture method, rights/provenance, human review, and institutional review. The Atlas heritage candidates 832 and 913 concern other places and remain outside both contracts and the public natural layer.

Future candidate records must preserve source IDs, names, coordinates, source paths, and provenance exactly; include a documented selection reason; remain review-required; and keep `publication_approved: false`. Name similarity alone is insufficient.

## Institutional point inventories added 2026-08-22

Two ArcGIS JSON exports from `points_world_heritage.gdb` are preserved inside the existing scope contracts as non-public review inventories. Only portable provenance is recorded: database and layer identifiers, export basename, SHA-256, record count, geometry type, WKID, field names, and extraction date. Local backup paths are not recorded.

| Destination | Layer / export | SHA-256 | Points | Review classification counts |
|---|---|---|---:|---|
| Leptis Magna | `leptis_points_review` / `leptis_points_review.esri.json` | `51be7a822a221e3ff4170c2f0104a83a9a99fc3b3ea916ca3a57a7723fd6f281` | 51 | 39 archaeological/heritage; 11 visitor service/facility; 1 landscape/natural; 0 unresolved |
| Sabratha | `sabratha_points_review` / `sabratha_points_review.esri.json` | `ffb3612844670770fafedf559860827a37b2ee556ee28794c94a6d62652de5d3` | 39 | 33 archaeological/heritage; 2 visitor service/facility; 0 landscape/natural; 4 unresolved |

The classification is name-evidence routing for review only. It does not establish canonical archaeological classification, destination membership, ownership, public visibility, or publication eligibility. Every record preserves every original attribute value and original point coordinate. Content-derived review IDs bind the source database and layer, all preserved source attributes, and coordinates, so mutable ArcGIS OIDs are never the sole identity. Original order and close or repeated points are retained.

The inventories remain distinct from the existing reviewed destination anchors. They are point inventories, not boundaries, boundary centroids, entrances, routes, or published feature layers. They add 90 non-public review points but add zero records to the registry's 214 published-scope GIS count.

### Leptis Magna quality findings

- 51 records, 49 unique nonblank Arabic names, and 49 unique coordinates.
- `popupinfo` is blank in 49 records, `en_name` in 33, and `photo` in 42.
- `متحف الفسيفساء` occurs twice with exactly the same name and coordinate; both records are preserved and flagged.
- `معبد جوبيتير دوليكينوس` and `معبد جوبيتير` share an exact coordinate but have different source identities; both are preserved and flagged.
- The mutable `objectid` value zero occurs twice and is flagged; it is not used as the sole review identity.
- Close pairs remain separate for human review and are never automatically deduplicated.
- The `en_name` value for `قوس الإمبراطور تراجان` contains attachment JSON and is preserved and flagged rather than interpreted as an English name.
- Nine nonblank `photo` values contain attachment JSON: four parse successfully and five are truncated. All are source references only.
- The `قوس سبتيموس سفيروس` photo value references a filename naming `قوس الإمبراطور تراجان`; this is flagged as a media identity conflict.
- Attachment paths establish neither ownership nor usage rights.

### Sabratha quality findings

- 39 records, 39 unique coordinates, and 36 unique nonblank names.
- All 39 description values are blank.
- All 39 geometry coordinates match source `X`/`Y` within `0.000001` degrees.
- Repeated `معبد سيرابيس`, `حوض المعمودية`, and `معبد ايزيس وإيزوريس` names have different coordinates and remain separate review records.
- The `معبد سيرابيس` group and nearby `Serapaeum (Sabratha` record are flagged for identity/normalization review.
- The incomplete source value `Serapaeum (Sabratha` is preserved exactly. `Serapaeum (Sabratha)` is stored only as a proposed normalized value.
- `حمامات أوفانيوس` and `حمامات ريجيو السابع` are approximately 0.79 metres apart but remain distinct records with a proximity review flag.

An unusable standalone Sabratha shapefile candidate was rejected and was not imported. No record, geometry, or provenance claim in these contracts derives from that corrupt candidate.

## Controlled layer taxonomy

The contracts define the following future categories without creating feature instances:

1. `ARCHAEOLOGICAL_MONUMENT`
2. `ARCHAEOLOGICAL_STRUCTURE`
3. `MOSAIC_OR_ARTIFACT_CONTEXT`
4. `SITE_ENTRANCE`
5. `VISITOR_CENTER`
6. `MUSEUM`
7. `INTERPRETATION_POINT`
8. `ACCESS_ROUTE`
9. `VISITOR_SERVICE`
10. `PROTECTION_OR_BUFFER_ZONE`
11. `DOCUMENTED_VIEWPOINT`
12. `OTHER_REVIEW_REQUIRED`

Each category declares allowable GeoJSON geometry types, required evidence, current authoritative-feature availability, and mandatory human and institutional review. Taxonomy availability does not classify any real-world feature.

## Boundary gaps and required institutional inputs

No authoritative site, protection-zone, or buffer-zone polygon was found for either destination. The project governance owner identified in publication policy—the Tourism Information and Documentation Center—must coordinate authoritative supplying evidence without this phase inventing a new authority. Required inputs are:

- an authoritative site and applicable protection/buffer geometry with source instrument, version, date, coordinate reference information, and rights;
- stable bilingual feature identities and source IDs;
- surveyed geometries with capture methods and accuracy;
- explicit destination-membership and heritage-classification review;
- visitor-service operational evidence where relevant;
- separate identity, coordinate, destination-membership, media-rights, and publication decisions under the established separation of duties.

## Future fieldwork data-collection template

No fake field records are created. A future empty template or governed collection form should contain:

| Field | Requirement |
|---|---|
| `field_record_id` | Stable unique identifier |
| `destination_slug` | Controlled canonical destination linkage |
| `feature_name_ar`, `feature_name_en` | Source-backed bilingual identity |
| `feature_category` | Controlled taxonomy value |
| `geometry_type` | Allowed GeoJSON type |
| `longitude`, `latitude` | Numeric values when the geometry is a point; never inferred |
| `coordinate_method` | Survey/GNSS/digitization method stated explicitly |
| `horizontal_accuracy_m` | Measured or documented accuracy |
| `capture_date` | ISO date |
| `field_team` | Accountable capture team |
| `source_institution` | Supplying institution as documented by the evidence |
| `evidence_reference` | Stable source record or instrument reference |
| `media_reference` | Existing governed media linkage, if applicable |
| `rights_status` | Geometry and media reuse status |
| `review_status` | Controlled review lifecycle state |
| `canonical_identity_status` | Separate identity decision state |
| `publication_approved` | Must remain false until an effective ledger decision |

Line and polygon records additionally need ordered vertices, CRS, topology checks, capture method, accuracy, and boundary authority. Entrances, centroids, routes, facilities, and viewpoints require role-specific evidence and may not inherit the site anchor.

## QA and review workflow

1. Intake preserves the original source and immutable source identity.
2. Technical validation checks JSON/GeoJSON, UTF-8 serialization, geometry type, finite numbers, Libya bounds, stable ordering, duplicate IDs, and provenance.
3. Identity review confirms bilingual names separately from geometry.
4. Spatial review confirms geometry method, accuracy, destination membership, and topology.
5. Heritage subject review confirms classification independently of visibility or media.
6. Rights review covers source geometry and media independently.
7. Institutional decisions are recorded through the established append-only governance process; validation cannot create approval.
8. Deterministic generation and protected-output verification precede any authorized runtime integration.

## Promotion gates

Promotion must pass these gates independently and in order:

1. Review scope accepted.
2. Feature identities and geometries verified.
3. Authoritative site and applicable protection/buffer boundary supplied and reviewed.
4. Complete source provenance and rights recorded.
5. Required institutional identity, coordinate, membership, media-rights, and publication decisions effective.
6. Deterministic generation manifest and protected-output verification updated through a separately authorized phase.
7. Public map integration implemented and tested through a separately authorized frontend/runtime phase.

This foundation stops at review scope. It creates no public layer and grants none of the later gates.

## Validation

```text
python -m json.tool backend/data/gis/leptis-magna-heritage-scope.review.json
python -m json.tool backend/data/gis/sabratha-heritage-scope.review.json
python backend/scripts/primary_heritage_gis_review.py
python -m pytest -q backend/tests/unit/scripts/test_primary_heritage_gis_review.py
python backend/scripts/destination_registry.py
python -m pytest -q backend/tests/unit/scripts/test_destination_registry.py
python backend/scripts/publication_governance.py
python backend/scripts/publication_generation.py validate-manifest
python backend/scripts/publication_generation.py verify
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
```
