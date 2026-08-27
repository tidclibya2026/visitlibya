# Libya National Boundary Governance

## Status

**BLOCKED FOR PUBLICATION**

Visit Libya currently does not possess a resolved authoritative national boundary dataset that satisfies the project's GIS governance requirements.

## Audit Finding

The institutional GIS audit contains a taxonomy entry:

- Arabic source category: `حدود ليبيا`
- Feature count: `1`
- Visit Libya category: `null`
- Mapping status: `REVIEW_REQUIRED`

This taxonomy entry does not provide sufficient provenance to establish a national boundary authority.

## Sources Reviewed

Thirteen institutional GIS source summaries were reviewed.

Only three currently audited sources contain Polygon geometry:

1. Old Tripoli
2. Acacus
3. Five Libya UNESCO World Heritage Sites

None represents the national boundary of Libya.

Their bounding boxes and thematic scopes demonstrate that they are local, regional, or heritage datasets.

## Authority Decision

No existing audited Polygon or MultiPolygon shall be interpreted as the national boundary.

The absence of a national-scale source is an explicit governance finding, not a reason to fabricate or infer geometry.

## Publication Gate

A Libya national boundary may become publishable only when all of the following are available:

1. Identifiable authoritative source.
2. Traceable provenance.
3. Original source dataset.
4. Immutable version or SHA-256 checksum.
5. Polygon or MultiPolygon geometry.
6. Declared CRS.
7. Valid geometry.
8. Verified national geographic extent.
9. Institutional review.
10. Explicit publication approval.

## Prohibited Substitutions

The following must not be used as substitutes:

- destination extent;
- UNESCO polygons;
- natural-resource polygons;
- regional tourism polygons;
- municipal extent;
- manually drawn SVG borders;
- undocumented GeoJSON downloaded from an unknown source.

## Relationship to the Tourism Atlas

The Tourism Atlas may display governed destination points without an authoritative national boundary.

Until a national boundary satisfies this governance contract, the frontend must not claim that a displayed outline represents the official or authoritative Libya national boundary.

## Future Authority Path

Authoritative source
→ provenance registration
→ checksum
→ CRS normalization
→ geometry validation
→ national extent validation
→ institutional review
→ approval
→ publication projection
→ Tourism Atlas

## Architectural Principle

GeoJSON is a transport or publication projection.

It does not become authoritative merely because it contains a Polygon.

Authority originates from the governed source and approval process.
