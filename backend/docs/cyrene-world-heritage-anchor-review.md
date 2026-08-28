# Cyrene WORLD_HERITAGE anchor review

## Decision

The institutional identity `موقع شحات (قورينة) الأثري` / `Archaeological Site of Cyrene` is explicit World Heritage property evidence. Modern Shahat is its municipality/locality, the Green Mountain is regional context, and the project registry identity `Cyrene (Shahat)` is a separate unpublished destination model. These identities are related but are not merged.

No canonical site anchor is ready. The institutional KML Placemark geometry is 21.8532586, 32.8125333 (WGS84), while coordinate fields embedded in the same Placemark description are 21.8580, 32.8250 (WGS84). They are 1,455.322 metres apart. Without an institutional decision selecting one representation, the evidence is `COORDINATE_REVIEW_REQUIRED` and the overall geometry decision is `NO_SAFE_GEOMETRY`.

The `points_world_heritage.gdb` records are archaeological sub-features or locality context and are `REGIONAL_CONTEXT_ONLY` for canonical-anchor purposes. The `Cyrene_shahhat.gdb` polygons do not state UNESCO property or buffer-zone semantics and are `BOUNDARY_SEMANTICS_UNRESOLVED`. The `Qurina_Cy.gdb` archaeological evidence also retains its previously documented CRS metadata/geometry conflict.

Accordingly, no ingestion-compatible GeoJSON feature is emitted, no dry-run is performed, and Cyrene remains excluded from governed `WORLD_HERITAGE` ingestion. The deterministic blocked artifact preserves the evidence and keeps `authority_status` unapproved and `is_published` false.

## Required resolution

An institutional reviewer must identify the canonical representative site point (or provide a separately reviewed property-level point), explain which conflicting coordinate representation is authoritative, and independently document any UNESCO property/buffer boundary semantics before ingestion preparation can proceed.

## Validation

```text
python backend/scripts/cyrene_world_heritage_anchor_review.py
python -m pytest -q backend/tests/unit/scripts/test_cyrene_world_heritage_anchor_review.py
```
