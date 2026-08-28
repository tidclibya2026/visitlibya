# NATURAL_SITES governed review layer

## Status and scope

This layer is a deterministic, non-public governed review import for `NATURAL_SITES`. It uses only committed project and institutional evidence. It grants no publication approval, canonical approval, protected-area authority, or public visibility.

The ordinal-complete evidence base is the 945-point national natural-resources reconciliation. The destination registry, Phase 1 natural review, high-priority review packet, Green Mountain curated/review layers, Libyan Sahara curated/review layers, cross-layer review, institutional source manifest, and institutional source inventory are corroborating classification and provenance evidence. They are not counted again as new physical features.

## Deterministic decisions

- `SAFE_NAMED_GEOMETRY_CANDIDATE`: a source Point present in an existing Green Mountain or Libyan Sahara curated review layer, unless identity-conflicted.
- `SAFE_POINT_CANDIDATE`: a clean Phase 1 eligible source Point with no inspected curated overlap and no identity conflict.
- `REGIONAL_CONTEXT_ONLY`: evidence appearing only in a regional candidate/review layer; regional membership does not create a destination boundary.
- `CONTEXTUAL_FEATURE`: mixed, cultural, service, infrastructure, or cross-layer evidence retained for context but not natural-site ingestion.
- `DUPLICATE_OR_IDENTITY_REVIEW`: every member of exact-coordinate, same-name/different-coordinate, different-name/identical-coordinate, or near-coordinate review groups.
- `BOUNDARY_SEMANTICS_UNRESOLVED`: protected-area/park review labels represented only by source points. No boundary, reserve limit, or park limit is inferred.
- `SOURCE_REVIEW_REQUIRED`: remaining clean natural-resource evidence whose subtype or tourism-site identity is not sufficiently resolved for ingestion.
- `EXCLUDED_FROM_INGESTION`: mandatory natural-display mismatches and explicit natural-layer exclusions.

All ingestible geometry is unchanged source WGS84 Point geometry. The artifacts do not infer protected-area boundaries, park or reserve boundaries, tourism development zones, routes or trails, or lake, wadi, wetland, and hydrological extents.

The registry identities `green-mountain` and `desert` are preserved as canonical regional context only. They supply no point or boundary geometry. Feature identity remains the governed national review ID plus source ordinal and portable institutional source reference; names and proximity never cause consolidation.

## Review-state contract

Controlled ingestion sets every row to `review_status=under_review`, `authority_status=unapproved`, `validation_status=valid`, `is_validated=true`, and `is_published=false`. The public repository filters therefore return no NATURAL_SITES feature until a separate governed approval and publication action occurs.

## Regeneration and validation

```powershell
python backend/scripts/natural_sites_governed_layer.py --write
python backend/scripts/natural_sites_governed_layer.py
python -m pytest -q backend/tests/unit/scripts/test_natural_sites_governed_layer.py backend/tests/unit/gis backend/tests/integration/api/test_governed_gis.py
$env:PYTHONPATH='backend'; python backend/scripts/ingest_governed_gis.py --geojson backend/data/gis/natural-sites-governed-import.review.geojson --layer-code NATURAL_SITES --source-layer national-natural-resources --source-database institutional-natural-atlas-review --dry-run
```

The generator fingerprints every committed evidence artifact semantically, so line-ending changes do not alter provenance. Validation fails if either generated artifact is missing or stale, accounting does not close at 945, unsafe classifications enter the import, or geometry is empty, invalid, non-Point, non-finite, or outside WGS84 limits.
