# Institutional GIS source registry

## Purpose and boundaries

This development tool audits center-supplied KML and GeoJSON, normalizes source-derived metadata, and generates destination mapping candidates for human review. It does not fetch URLs, access PostgreSQL, change Visit Libya destinations, populate reviewed coordinates, import media, or modify either Atlas application.

The workflow is:

```text
institutional source → source registry → normalized features → exact-equality candidates
→ human review → reviewed mapping → reviewed coordinate intake → later importer dry-run
```

Candidate output is not approval. No name similarity, substring, or confidence score can promote a candidate.

## Source manifest

`data/gis/source-manifest.json` maps stable registry-only source IDs to expected filenames and logical roles. It contains no machine paths. Source IDs and generated feature fingerprints are audit identifiers, not national tourism-site identifiers.

Supply files through an explicit directory. On Windows, for example:

```text
python -m scripts.audit_institutional_gis --source-dir "C:\visitlibya-gis-sources"
```

The path is illustrative; the tool does not assume it exists. Manifest filenames are resolved beneath the supplied directory, and traversal outside that directory is rejected.

## Safe parsing

Inputs are limited to 25 MiB each and must be UTF-8. KML is rejected before XML parsing if it contains a DTD or entity declaration. No parser performs network resolution. Supported KML content is Placemark name, description, ExtendedData, Point coordinates, and geometry-type auditing. LineString, Polygon, and MultiGeometry are recorded but never converted to destination coordinates. Supplementary JSON governance arrays are audited for record IDs and schema keys but never normalized as geographic features.

KML coordinate order is `longitude,latitude[,altitude]`. GeoJSON must be a FeatureCollection; Point order is `[longitude, latitude]`. Normalized Visit Libya fields are emitted as `latitude` and `longitude`. Both values must be finite and within geographic ranges.

Source files are opened read-only and are never cleaned or rewritten. Missing and malformed sources remain explicit audit states.

## Preview and reports

Preview performs no writes:

```text
python -m scripts.audit_institutional_gis --source-dir "C:\visitlibya-gis-sources"
```

Explicit report generation writes only atomic JSON artifacts under `data/gis`:

```text
python -m scripts.audit_institutional_gis --source-dir "C:\visitlibya-gis-sources" --write-reports
```

Generated artifacts include the factual source registry, data-quality audit, taxonomy crosswalk, and candidate report. Each parsed source records SHA-256, count, geometry types, bounds, metadata coverage, duplicates, and quality findings.

## Mapping states and human review

- `EXACT_ID`: an explicit source property equals the canonical Visit Libya slug. It still requires governance review before coordinate intake.
- `EXACT_APPROVED_MAPPING`: reserved for a separately approved mapping record; the generator does not create it.
- `REVIEW_REQUIRED`: exact normalized name equality only.
- `REVIEW_REQUIRED_AGGREGATE`: exact equality involving a broad destination where one Point may not represent the area.
- `AMBIGUOUS`: multiple exact-name candidates exist.
- `NO_MATCH`: no exact discovery candidate.
- `CONFLICT`: reserved for incompatible approved identity or coordinate evidence.

`data/gis/destination-source-mapping.reviewed.json` remains empty until a human approves exact source-feature-to-destination relationships. Candidate records must never be copied automatically into `data/dev/destination-coordinates.reviewed.json`.

### Canonical destination semantic review

`data/gis/canonical-destination-coordinate-review.json` is a reproducible, human-review-only analysis of every destination in `data/dev/destinations.json`. It searches normalized source names, descriptions, source context, categories, localities, regions, and approved discovery aliases. Similarity values rank discovery results only and can never approve identity.

The review uses `APPROVAL_READY`, `REVIEW_REQUIRED`, `REVIEW_REQUIRED_AGGREGATE`, `AMBIGUOUS`, `NO_MATCH`, and `CONFLICT`. `APPROVAL_READY` means that the institutional feature appears to represent the same tourism destination closely enough for a human decision; it is not approval and does not write coordinates. Multiple plausible points remain separate, and broad destinations never receive an inferred centroid or an arbitrary sub-feature point.

Every candidate also records one semantic scope: `DESTINATION_LEVEL_FEATURE`, `INSTITUTIONAL_ANCHOR`, `SUB_FEATURE`, or `REGIONAL_CONTEXT`. Broad destinations may be `APPROVAL_READY` when an institutional source explicitly provides a destination-level feature or representative anchor. Regional metadata and sub-features establish source coverage but do not by themselves authorize a representative coordinate.

World Heritage Placemark authority is literal. Names, descriptions, coordinates, hierarchy, references, and source hashes from `مواقع التراث العالمي الخمسة_LY.kml` remain source-derived and are not renamed, split, merged, or replaced with broader inferred entities. A top-level heritage summary Placemark such as `مدينة غدامس القديمة` retains that exact institutional semantic identity; similarly named secondary records remain visible but cannot override it.

Preview the canonical review without writing files:

```text
python -m scripts.audit_institutional_gis --source-dir "C:\visitlibya-gis-sources"
```

Writing the review artifact is explicit and still does not access a database or the reviewed coordinate intake:

```text
python -m scripts.audit_institutional_gis --source-dir "C:\visitlibya-gis-sources" --write-reports
```

## Atlas relationships

The Libya Tourist Atlas and Natural Resources/Landscape Atlas remain independent institutional geographic products. This registry preserves lineage to supplied files without copying their applications or creating a competing GIS interface. Natural Atlas base/media deduplication is allowed only when identical native feature IDs prove identity; otherwise the relationship is reported unresolved.

Media references are audited only. They remain unsuitable for Visit Libya database import until creator, rights, approval, and stable delivery provenance are reviewed under the existing media policy.

## Taxonomy and future publication

The generated crosswalk labels exact category-code equality as `EXACT`; all other source classifications require review. Natural resources should enter a future visitor catalogue only through tourism-value selection, editorial validation, coordinate review, and media approval. Lakes, springs, protected areas, oases, wetlands, and distinctive landscapes may be candidates. Wells, dams, tanks, and every wadi must not become visitor destinations automatically.

## Future national site identifier

A future `tourism_site_code` should be assigned by the responsible institutional data owner, immutable, language-neutral, and unique to a reviewed tourism site or area. It should link—but not replace—Visit Libya slugs, source-native IDs, and Atlas placemark IDs. Registry fingerprints must never be promoted into that namespace.
