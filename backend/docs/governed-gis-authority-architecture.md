# Governed GIS Authority Architecture

## Authority flow

Institutional Source
→ protected review/import artifact
→ identity and geometry validation
→ institutional review
→ institutional approval
→ PostGIS authority
→ publication gate
→ repository and service
→ GeoJSON API projection
→ Tourism Atlas / Visit Libya

PostGIS is the runtime spatial authority. Raw institutional databases and exports
remain protected evidence. GeoJSON, KML, JSON, shapefiles, and similar files are
imports, review artifacts, development artifacts, or API projections; they are not
the public system of record.

## Additive authority model

`governed_gis_features` supports point, multipoint, line, multiline, polygon, and
multipolygon geometry at SRID 4326. The specialized `destinations` and
`national_boundaries` authorities remain intact. In particular, the Libya national
boundary is not migrated into the generic table.

Each generic feature has stable layer and institutional identities, bilingual
content, source provenance, a PostGIS geometry, and independent review, authority,
validation, and publication state. A database row is not automatically a public
record.

## Governance gates

The lifecycle is:

`draft` → `under_review` → `reviewed`

Geometry validation, authority approval, and publication are separate decisions.
Public repository methods require all of the following:

- authority status `approved`;
- validation status `valid`;
- `is_validated = true`;
- `is_published = true`;
- non-null authoritative PostGIS geometry.

Valid geometry alone never grants institutional approval or public visibility.
The ingestion foundation has no publication option and defaults every new or
updated record to unapproved and unpublished.

## Layer registry

`app.gis.layer_registry` defines layer codes, bilingual names, categories, allowed
geometry types, authority level, publication policy, frontend metadata visibility,
and safe default publication state. Layer-specific ingestion is rejected unless the
layer exists and its geometry type is allowed.

Initial registry entries reserve architecture for Libya's national boundary, World
Heritage, Old Tripoli, natural sites, archaeological sites, historical sites, and
rock art. Registry entries do not ingest, approve, validate, or publish real data.

## Public API and frontend contract

The public contract is rooted at `/api/v1/gis/layers`:

- `GET /gis/layers`
- `GET /gis/layers/{layer_code}`
- `GET /gis/layers/{layer_code}/features`
- `GET /gis/layers/{layer_code}/features/{feature_code}`
- `GET /gis/layers/{layer_code}/geojson`
- `GET /gis/layers/{layer_code}/bbox`

Public schemas intentionally omit internal source paths, source hashes, and source
metadata. Feature and collection geometry is projected from PostGIS with
`ST_AsGeoJSON`; bbox filtering is performed with PostGIS `ST_Intersects`.

The existing Atlas remains compatible with destination spatial endpoints. Future
layer integrations should call the governed layer GeoJSON/bbox endpoints through
`assets/js/app/api/gis-api.js` rather than importing committed raw GIS JSON. This
foundation does not switch or publish existing frontend datasets.
