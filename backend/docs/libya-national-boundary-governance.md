# Libya National Boundary Governance

## Status

**INSTITUTIONAL SOURCE RESOLVED — PUBLICATION PENDING**

Visit Libya now has a resolved institutional source for the Libya national boundary.

## Institutional Reference

- Institutional reference: المخطط العام للتنمية السياحية
- Project: مشروع أطلس ليبيا السياحي
- Source owner: مركز المعلومات والتوثيق السياحي
- Source database: `LibyaData.mdb`
- Feature Dataset: `الحدود`
- Feature Class: `الحدودالدولية`
- Source filter: `Countries_EN = Libya`

## Display Identity

- Arabic: `ليبيا`
- English: `Libya`

The historical Arabic source value is retained only as provenance metadata and is not used as the public display name.

## Geometry

- Geometry type: `Polygon`
- CRS: `GCS_WGS_1984`
- Feature count: `1`

## Geometry Validation

The derived boundary dataset was validated using ArcMap Check Geometry.

Result:

- Geometry errors: `0`
- Validation status: `VALID`

## Derived Dataset

The institutional source was not modified.

A derived publication candidate was created:

`atlas/derived/libya_national_boundary.shp`

Core component SHA-256 values are recorded in the governed boundary candidate record.

## Authority Decision

The previous unresolved-boundary finding has been superseded by discovery of the original institutional boundary within the Tourism Atlas source geodatabase.

The boundary is now considered:

- source resolved;
- institutionally attributable;
- geometry available;
- geometry validated;
- pending controlled publication.

## Publication Path

المخطط العام للتنمية السياحية
→ مشروع أطلس ليبيا السياحي
→ LibyaData.mdb
→ الحدود
→ الحدودالدولية
→ Countries_EN = Libya
→ geometry validation
→ governed derived boundary
→ PostGIS
→ public GeoJSON projection
→ Tourism Atlas

## Publication Gate

Final publication still requires:

1. PostGIS ingestion.
2. SRID normalization and validation.
3. PostGIS geometry validation.
4. Governed public API projection.
5. Frontend integration.
6. Release validation.

## Architectural Principle

The institutional source remains the provenance authority.

PostGIS will become the production spatial authority after governed ingestion.

GeoJSON remains a public transport/projection format and not the original source authority.
