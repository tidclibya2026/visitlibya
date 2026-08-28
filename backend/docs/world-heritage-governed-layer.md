# WORLD_HERITAGE governed import

This phase adds a deterministic, non-public import artifact for the reusable governed GIS authority introduced by PR #112. It does not write to PostGIS, approve authority, publish a layer, change the Atlas frontend, or commit raw institutional GIS.

The artifact contains four reviewed destination/site anchors from `backend/data/dev/destination-coordinates.reviewed.json`: Leptis Magna, Sabratha, Tadrart Acacus, and the Old Town of Ghadames. Each point retains its institutional KML placemark reference and the accepted source SHA-256. The points are anchors only; they are not site boundaries, centroids, entrances, protection zones, or detailed heritage features.

Cyrene is deliberately excluded. The available placemark is classified in the canonical review as `REVIEW_REQUIRED_AGGREGATE` with `REGIONAL_CONTEXT`, and the national destination registry has no current canonical Cyrene destination or reviewed destination-level coordinate. It must not be promoted until identity and coordinate review produce a canonical site anchor.

All features remain `REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL`. If a separately authorized operator ingests the artifact through `ingest_governed_gis.py`, PR #112 forces the resulting records to `under_review`, `unapproved`, validated, and unpublished. This phase does not perform that database operation.

Validation:

```text
python backend/scripts/world_heritage_governed_layer.py
python -m pytest -q backend/tests/unit/scripts/test_world_heritage_governed_layer.py backend/tests/unit/gis/test_ingest_governed_gis.py
```
