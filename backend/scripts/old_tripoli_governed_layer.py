#!/usr/bin/env python3
"""Build and validate the non-public OLD_TRIPOLI governed review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION_PATH = ROOT / "backend/data/gis/old-tripoli-source-reconciliation.review.json"
IMPORT_PATH = ROOT / "backend/data/gis/old-tripoli-governed-import.review.geojson"
BLOCKED_PATH = ROOT / "backend/data/gis/old-tripoli-governed-blocked.review.json"
LAYER_CODE = "OLD_TRIPOLI"
ARTIFACT_STATUS = "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"
CATEGORIES = (
    "SAFE_POINT_CANDIDATE", "CONTEXTUAL_POINT", "CONTEXTUAL_LINE",
    "UNRESOLVED_ROUTE_SEMANTICS", "UNRESOLVED_POLYGON",
    "NON_AUTHORITATIVE_BOUNDARY", "DUPLICATE_OR_IDENTITY_REVIEW",
    "EXCLUDED_FROM_INGESTION",
)
SAFE_POINT_COLLECTIONS = frozenset({
    "RELIGIOUS_HERITAGE", "HISTORIC_BUILDINGS_AND_URBAN_HERITAGE",
    "ARCHAEOLOGICAL_AND_MONUMENTAL_HERITAGE", "TRADITIONAL_MARKETS_AND_CRAFTS",
    "MUSEUMS_AND_CULTURAL_FACILITIES",
})


class OldTripoliGovernedLayerError(ValueError):
    """Raised when evidence cannot safely produce the governed artifacts."""


def _canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def reconciliation_fingerprint(raw: bytes) -> str:
    """Hash reconciliation JSON semantics, independent of checkout line endings."""
    payload = json.loads(raw.decode("utf-8"))
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _all_records(source: dict) -> list[dict]:
    records = [item for collection in source["collections"].values() for item in collection]
    return sorted(records, key=lambda item: item["source_ordinal"])


def _identity_review_ordinals(source: dict) -> set[int]:
    ordinals: set[int] = set()
    for key in ("identity_conflicts", "same_name_different_geometry_groups", "near_point_review_pairs"):
        for group in source[key]:
            ordinals.update(group["source_ordinals"])
    for review in source["key_identity_review"]:
        for match in review["matches"]:
            if match["identity_match_status"] == "SOURCE_VARIANT_REQUIRES_IDENTITY_REVIEW":
                ordinals.add(match["source_ordinal"])
    return ordinals


def classify(source: dict, record: dict, identity_review: set[int]) -> str:
    ordinal = record["source_ordinal"]
    geometry_type = record["geometry_type"]
    if record in source["technical_quarantine"]:
        return "EXCLUDED_FROM_INGESTION"
    if ordinal in identity_review:
        return "DUPLICATE_OR_IDENTITY_REVIEW"
    if geometry_type == "LineString":
        return "UNRESOLVED_ROUTE_SEMANTICS" if record["raw_name"].strip() else "CONTEXTUAL_LINE"
    if geometry_type == "Polygon":
        overlap = {value for item in source["polygon_overlap_review_candidates"] for value in item["source_ordinals"]}
        return "NON_AUTHORITATIVE_BOUNDARY" if ordinal in overlap else "UNRESOLVED_POLYGON"
    if geometry_type == "Point" and record["proposed_review_collection"] in SAFE_POINT_COLLECTIONS:
        return "SAFE_POINT_CANDIDATE"
    if geometry_type == "Point":
        return "CONTEXTUAL_POINT"
    return "EXCLUDED_FROM_INGESTION"


def _geometry(record: dict) -> dict:
    part = record["geometry_parts"][0]
    return {"type": part["type"], "coordinates": part["coordinates"]}


def _ingest_geometry(record: dict) -> dict:
    """Normalize safe source points to the governed table's 2D WGS84 contract."""
    geometry = _geometry(record)
    coordinates = geometry["coordinates"]
    if len(coordinates) == 1 and isinstance(coordinates[0], list):
        coordinates = coordinates[0]
    return {"type": "Point", "coordinates": coordinates[:2]}


def _source_metadata(source: dict, record: dict, classification: str) -> dict[str, Any]:
    return {
        "artifact_status": ARTIFACT_STATUS,
        "review_classification": classification,
        "review_id": record["review_id"],
        "source_ordinal": record["source_ordinal"],
        "source_id": source["source_provenance"]["source_id"],
        "source_sha256": source["source_provenance"]["source_sha256"],
        "source_reference": f"{source['source_provenance']['portable_source_label']}#Placemark-{record['source_ordinal']}",
        "source_collection": record["proposed_review_collection"],
        "folder_path": record["folder_path"],
        "raw_name": record["raw_name"],
        "raw_description": record["raw_description"],
        "extended_data": record["extended_data"],
        "style_url": record["style_url"],
        "source_geometry": _geometry(record),
        "nested_destination": {
            "slug": "old-tripoli",
            "parent_slug": "tripoli",
            "relationship": "CONTAINS_HERITAGE_DESTINATION",
            "public_runtime_identity_created": False,
        },
    }


def build() -> tuple[dict, dict]:
    source = json.loads(RECONCILIATION_PATH.read_text(encoding="utf-8"))
    records = _all_records(source)
    identity_review = _identity_review_ordinals(source)
    classified = [(record, classify(source, record, identity_review)) for record in records]
    features = []
    blocked = []
    for record, category in classified:
        metadata = _source_metadata(source, record, category)
        if category == "SAFE_POINT_CANDIDATE":
            features.append({
                "type": "Feature",
                "properties": {
                    "feature_code": f"old-tripoli-{record['review_id']}",
                    "institutional_id": record["review_id"],
                    "source_feature_id": f"Placemark-{record['source_ordinal']}",
                    "name_ar": record["raw_name"].strip() or None,
                    "name_en": None,
                    "category": "heritage",
                    "review_classification": category,
                    "source_identity": metadata["source_reference"],
                    "source_metadata": metadata,
                },
                "geometry": _ingest_geometry(record),
            })
        else:
            blocked.append({
                "review_id": record["review_id"],
                "source_ordinal": record["source_ordinal"],
                "review_classification": category,
                "blocked_reason": category,
                "geometry_type": record["geometry_type"],
                "geometry": _geometry(record),
                "source_metadata": metadata,
            })
    counts = Counter(category for _, category in classified)
    geometry_counts = {
        status: dict(Counter(record["geometry_type"] for record, category in classified if (category == "SAFE_POINT_CANDIDATE") == (status == "ingestible")))
        for status in ("ingestible", "blocked")
    }
    common = {
        "artifact_status": ARTIFACT_STATUS,
        "layer_code": LAYER_CODE,
        "publication_approved": False,
        "authoritative_boundary_claimed": False,
        "historic_or_visitor_route_claimed": False,
        "source_reconciliation_id": source["reconciliation_id"],
        "source_reconciliation_sha256": reconciliation_fingerprint(
            RECONCILIATION_PATH.read_bytes()
        ),
        "evidence_count": len(records),
        "category_counts": {name: counts[name] for name in CATEGORIES},
        "geometry_counts_by_status": geometry_counts,
    }
    import_artifact = {
        "type": "FeatureCollection", "name": "OLD_TRIPOLI governed review import",
        **common, "source_database": "institutional-kml-review",
        "source_layer": "tripoli-old-city", "features": features,
    }
    blocked_artifact = {
        "schema_version": 1, "inventory_id": "old-tripoli-governed-blocked-v1",
        **common, "safe_ingestible_feature_count": len(features),
        "blocked_feature_count": len(blocked), "records": blocked,
    }
    return import_artifact, blocked_artifact


def validate() -> tuple[dict, dict]:
    expected_import, expected_blocked = build()
    for path, expected in ((IMPORT_PATH, expected_import), (BLOCKED_PATH, expected_blocked)):
        if not path.is_file() or path.read_bytes() != _canonical_bytes(expected):
            raise OldTripoliGovernedLayerError(f"Governed artifact is missing or stale: {path.name}")
    if expected_import["evidence_count"] != 430:
        raise OldTripoliGovernedLayerError("Evidence accounting is not exactly 430")
    if len(expected_import["features"]) + len(expected_blocked["records"]) != 430:
        raise OldTripoliGovernedLayerError("Governed accounting does not resolve every record")
    for feature in expected_import["features"]:
        geometry = shape(feature["geometry"])
        if geometry.geom_type != "Point" or geometry.is_empty or not geometry.is_valid:
            raise OldTripoliGovernedLayerError("Unsafe ingestible geometry")
        x, y = geometry.x, geometry.y
        if not (-180 <= x <= 180 and -90 <= y <= 90):
            raise OldTripoliGovernedLayerError("Coordinate outside WGS84 limits")
    return expected_import, expected_blocked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        import_artifact, blocked_artifact = build()
        IMPORT_PATH.write_bytes(_canonical_bytes(import_artifact))
        BLOCKED_PATH.write_bytes(_canonical_bytes(blocked_artifact))
    import_artifact, blocked_artifact = validate()
    print("OLD_TRIPOLI GOVERNED REVIEW ARTIFACTS VALID")
    print("EVIDENCE COUNT:", import_artifact["evidence_count"])
    print("SAFE INGESTIBLE:", len(import_artifact["features"]))
    print("BLOCKED:", len(blocked_artifact["records"]))
    print("CATEGORY COUNTS:", json.dumps(import_artifact["category_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
