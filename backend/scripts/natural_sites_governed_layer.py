#!/usr/bin/env python3
"""Build and validate the non-public NATURAL_SITES governed review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
GIS = ROOT / "backend/data/gis"
NATIONAL_PATH = GIS / "national-natural-resources-source-reconciliation.review.json"
PHASE1_PATH = GIS / "phase1-natural-editorial-candidates.review.json"
HIGH_PRIORITY_PATH = GIS / "high-priority-natural-candidates.institutional-review.json"
GREEN_CURATED_PATH = GIS / "green-mountain-tourism-curated.review.json"
GREEN_REVIEW_PATH = GIS / "green-mountain-expanded.review.json"
SAHARA_CURATED_PATH = GIS / "libyan-sahara-tourism-curated.review.json"
SAHARA_REVIEW_PATH = GIS / "libyan-sahara-tourism-candidates.review.json"
CROSS_LAYER_PATH = GIS / "natural-layer-cross-layer-review.json"
REGISTRY_PATH = ROOT / "backend/data/destinations/national-destination-registry.review.json"
SOURCE_MANIFEST_PATH = GIS / "source-manifest.json"
INSTITUTIONAL_SOURCES_PATH = GIS / "institutional-sources.json"
DEV_DESTINATIONS_PATH = ROOT / "backend/data/dev/destinations.json"
DEV_COORDINATES_PATH = ROOT / "backend/data/dev/destination-coordinates.reviewed.json"
IMPORT_PATH = GIS / "natural-sites-governed-import.review.geojson"
BLOCKED_PATH = GIS / "natural-sites-governed-blocked.review.json"

LAYER_CODE = "NATURAL_SITES"
ARTIFACT_STATUS = "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"
CATEGORIES = (
    "SAFE_POINT_CANDIDATE",
    "SAFE_NAMED_GEOMETRY_CANDIDATE",
    "CONTEXTUAL_FEATURE",
    "REGIONAL_CONTEXT_ONLY",
    "DUPLICATE_OR_IDENTITY_REVIEW",
    "BOUNDARY_SEMANTICS_UNRESOLVED",
    "SOURCE_REVIEW_REQUIRED",
    "EXCLUDED_FROM_INGESTION",
)
NON_NATURAL_COLLECTIONS = frozenset({
    "ARCHAEOLOGICAL_OR_HERITAGE_REVIEW", "HISTORICAL_OR_MEMORIAL_REVIEW",
    "SETTLEMENT_OR_URBAN_REVIEW", "VISITOR_SERVICE_OR_FACILITY_REVIEW",
    "AGRICULTURAL_OR_PRODUCTIVE_SITE_REVIEW", "INFRASTRUCTURE_OR_TRANSPORT_REVIEW",
    "MIXED_NATURAL_CULTURAL_REVIEW", "UNRESOLVED_NON_NATURAL_CONTEXT",
})


class NaturalSitesGovernedLayerError(ValueError):
    """Raised when evidence cannot safely produce the governed artifacts."""


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _semantic_sha256(path: Path) -> str:
    payload = _load(path)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _records(national: dict) -> list[dict]:
    records = [record for collection in national["collections"].values() for record in collection]
    return sorted(records, key=lambda record: record["source_ordinal"])


def _ordinals(payload: dict) -> set[int]:
    return {int(record["source_feature_id"]) for record in payload.get("records", [])}


def _nested_cross_records(cross: dict) -> list[dict]:
    records: list[dict] = []
    value = cross.get("records", {})
    groups = value.values() if isinstance(value, dict) else (
        nested for item in value if isinstance(item, dict) for nested in item.values()
    )
    for nested in groups:
        if isinstance(nested, list):
            records.extend(nested)
    return records


def _identity_review_ordinals(national: dict) -> set[int]:
    review = national["duplicate_and_conflict_review"]
    ordinals: set[int] = set()
    for key in (
        "normalized_name_exact_coordinate_groups",
        "different_name_identical_coordinate_groups",
        "same_name_different_coordinate_groups",
    ):
        for group in review[key]:
            ordinals.update(group["source_ordinals"])
    for groups in review["near_coordinate_candidates"].values():
        for group in groups:
            ordinals.update(group["source_ordinals"])
    return ordinals


def _phase1_eligible_ordinals(phase1: dict) -> set[int]:
    return {
        item["source_ordinal"]
        for queue in phase1["candidate_queues"].values()
        for item in queue
    }


def classify(
    record: dict,
    *,
    identity_review: set[int],
    curated: set[int],
    phase1_eligible: set[int],
    regional_review: set[int],
    contextual: set[int],
    excluded: set[int],
) -> str:
    ordinal = record["source_ordinal"]
    collection = record["proposed_review_collection"]
    if ordinal in excluded or collection == "CATEGORY_SCOPE_MISMATCH_REVIEW":
        return "EXCLUDED_FROM_INGESTION"
    if ordinal in identity_review:
        return "DUPLICATE_OR_IDENTITY_REVIEW"
    if collection == "PROTECTED_AREAS_AND_PARKS_REVIEW":
        return "BOUNDARY_SEMANTICS_UNRESOLVED"
    if ordinal in contextual or collection in NON_NATURAL_COLLECTIONS:
        return "CONTEXTUAL_FEATURE"
    if ordinal in curated:
        return "SAFE_NAMED_GEOMETRY_CANDIDATE"
    if ordinal in phase1_eligible:
        return "SAFE_POINT_CANDIDATE"
    if ordinal in regional_review:
        return "REGIONAL_CONTEXT_ONLY"
    return "SOURCE_REVIEW_REQUIRED"


def _source_metadata(record: dict, classification: str, evidence: dict[str, str]) -> dict[str, Any]:
    return {
        "artifact_status": ARTIFACT_STATUS,
        "review_classification": classification,
        "source_ordinal": record["source_ordinal"],
        "governed_review_id": record["review_id"],
        "source_reference": f"national_natural_resources_atlas_with_media_2026#Feature-{record['source_ordinal']}",
        "source_id": "natural-atlas-media",
        "source_semantic_sha256": evidence["national_reconciliation"],
        "raw_id": record["raw_id"],
        "raw_name": record["raw_name"],
        "normalized_review_name": record["proposed_normalized_name"],
        "raw_primary_category": record["raw_primary_category"],
        "raw_all_categories": record["raw_all_categories"],
        "raw_description": record["raw_description"],
        "raw_origin": record["raw_origin"],
        "raw_source": record["raw_source"],
        "raw_status": record["raw_status"],
        "review_collection": record["proposed_review_collection"],
        "resolution_bucket": record["resolution_bucket"],
        "overlap_partition": record["overlap_partition"],
        "existing_governed_overlaps": record["existing_governed_overlaps"],
        "quality_flags": record["quality_flags"],
        "source_geometry_metadata_mismatch": record["source_geometry_metadata_mismatch"],
        "preserved_properties": record["preserved_properties"],
        "source_geometry": record["geometry"],
    }


def build() -> tuple[dict, dict]:
    national, phase1 = _load(NATIONAL_PATH), _load(PHASE1_PATH)
    green_curated, green_review = _load(GREEN_CURATED_PATH), _load(GREEN_REVIEW_PATH)
    sahara_curated, sahara_review = _load(SAHARA_CURATED_PATH), _load(SAHARA_REVIEW_PATH)
    cross, registry = _load(CROSS_LAYER_PATH), _load(REGISTRY_PATH)
    evidence = {
        "national_reconciliation": _semantic_sha256(NATIONAL_PATH),
        "phase1_editorial_review": _semantic_sha256(PHASE1_PATH),
        "high_priority_institutional_review": _semantic_sha256(HIGH_PRIORITY_PATH),
        "green_mountain_curated": _semantic_sha256(GREEN_CURATED_PATH),
        "green_mountain_review": _semantic_sha256(GREEN_REVIEW_PATH),
        "libyan_sahara_curated": _semantic_sha256(SAHARA_CURATED_PATH),
        "libyan_sahara_review": _semantic_sha256(SAHARA_REVIEW_PATH),
        "cross_layer_review": _semantic_sha256(CROSS_LAYER_PATH),
        "destination_registry": _semantic_sha256(REGISTRY_PATH),
        "source_manifest": _semantic_sha256(SOURCE_MANIFEST_PATH),
        "institutional_sources": _semantic_sha256(INSTITUTIONAL_SOURCES_PATH),
        "development_destinations": _semantic_sha256(DEV_DESTINATIONS_PATH),
        "reviewed_destination_coordinates": _semantic_sha256(DEV_COORDINATES_PATH),
    }
    curated = _ordinals(green_curated) | _ordinals(sahara_curated)
    regional_review = _ordinals(green_review) | _ordinals(sahara_review)
    cross_records = _nested_cross_records(cross)
    contextual = {int(item["source_feature_id"]) for item in cross_records if item["curation_status"] == "CROSS_LAYER_REVIEW"}
    excluded = {int(item["source_feature_id"]) for item in cross_records if item["curation_status"] == "EXCLUDED_FROM_NATURAL_LAYER"}
    identity_review = _identity_review_ordinals(national)
    phase1_eligible = _phase1_eligible_ordinals(phase1)
    records = _records(national)
    classified = [(record, classify(record, identity_review=identity_review, curated=curated,
        phase1_eligible=phase1_eligible, regional_review=regional_review,
        contextual=contextual, excluded=excluded)) for record in records]

    features, blocked = [], []
    safe = {"SAFE_POINT_CANDIDATE", "SAFE_NAMED_GEOMETRY_CANDIDATE"}
    for record, category in classified:
        metadata = _source_metadata(record, category, evidence)
        if category in safe:
            features.append({
                "type": "Feature",
                "properties": {
                    "feature_code": f"natural-site-{record['review_id']}",
                    "institutional_id": record["review_id"],
                    "source_feature_id": str(record["source_ordinal"]),
                    "name_ar": record["raw_name"].strip() or None,
                    "name_en": None,
                    "category": "natural_tourism",
                    "review_classification": category,
                    "source_identity": metadata["source_reference"],
                    "source_metadata": metadata,
                },
                "geometry": record["geometry"],
            })
        else:
            blocked.append({
                "institutional_id": record["review_id"],
                "source_ordinal": record["source_ordinal"],
                "name_ar": record["raw_name"],
                "review_classification": category,
                "blocked_reason": category,
                "geometry_type": record["geometry"]["type"],
                "geometry": record["geometry"],
                "source_metadata": metadata,
            })
    counts = Counter(category for _, category in classified)
    geometry_counts = {
        status: dict(Counter(record["geometry"]["type"] for record, category in classified if (category in safe) == (status == "ingestible")))
        for status in ("ingestible", "blocked")
    }
    registry_identities = [
        {"registry_record_id": item["registry_record_id"], "slug": item["current_canonical_slug"],
         "entity_type": item["entity_type"], "role": "REGIONAL_CONTEXT_ONLY",
         "point_or_boundary_inferred": False}
        for item in registry["records"] if item["current_canonical_slug"] in {"green-mountain", "desert"}
    ]
    common = {
        "artifact_status": ARTIFACT_STATUS,
        "layer_code": LAYER_CODE,
        "publication_approved": False,
        "authoritative_protected_area_boundary_claimed": False,
        "authoritative_park_or_reserve_boundary_claimed": False,
        "lake_wadi_or_hydrological_extent_claimed": False,
        "tourism_zone_trail_or_route_claimed": False,
        "evidence_count": len(records),
        "category_counts": {category: counts[category] for category in CATEGORIES},
        "geometry_counts_by_status": geometry_counts,
        "evidence_semantic_sha256": evidence,
        "canonical_regional_identities": registry_identities,
    }
    imported = {"type": "FeatureCollection", "name": "NATURAL_SITES governed review import",
        **common, "source_database": "institutional-natural-atlas-review",
        "source_layer": "national-natural-resources", "features": features}
    blocked_artifact = {"schema_version": 1, "inventory_id": "natural-sites-governed-blocked-v1",
        **common, "safe_ingestible_feature_count": len(features),
        "blocked_feature_count": len(blocked), "records": blocked}
    return imported, blocked_artifact


def validate() -> tuple[dict, dict]:
    expected_import, expected_blocked = build()
    for path, expected in ((IMPORT_PATH, expected_import), (BLOCKED_PATH, expected_blocked)):
        if not path.is_file() or path.read_bytes() != _canonical_bytes(expected):
            raise NaturalSitesGovernedLayerError(f"Governed artifact is missing or stale: {path.name}")
    if expected_import["evidence_count"] != 945:
        raise NaturalSitesGovernedLayerError("Evidence accounting is not exactly 945")
    if len(expected_import["features"]) + len(expected_blocked["records"]) != 945:
        raise NaturalSitesGovernedLayerError("Every source ordinal must resolve exactly once")
    if sum(expected_import["category_counts"].values()) != 945:
        raise NaturalSitesGovernedLayerError("Classification accounting does not close")
    safe_categories = {"SAFE_POINT_CANDIDATE", "SAFE_NAMED_GEOMETRY_CANDIDATE"}
    for feature in expected_import["features"]:
        geometry = shape(feature["geometry"])
        if geometry.geom_type != "Point" or geometry.is_empty or not geometry.is_valid:
            raise NaturalSitesGovernedLayerError("Unsafe ingestible geometry")
        x, y = geometry.x, geometry.y
        if not all(math.isfinite(v) for v in (x, y)) or not (-180 <= x <= 180 and -90 <= y <= 90):
            raise NaturalSitesGovernedLayerError("Coordinate outside WGS84 limits")
        if feature["properties"]["review_classification"] not in safe_categories:
            raise NaturalSitesGovernedLayerError("Blocked classification entered import")
    return expected_import, expected_blocked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        imported, blocked = build()
        IMPORT_PATH.write_bytes(_canonical_bytes(imported))
        BLOCKED_PATH.write_bytes(_canonical_bytes(blocked))
    imported, blocked = validate()
    print("NATURAL_SITES GOVERNED REVIEW ARTIFACTS VALID")
    print("EVIDENCE COUNT:", imported["evidence_count"])
    print("SAFE INGESTIBLE:", len(imported["features"]))
    print("BLOCKED:", len(blocked["records"]))
    print("CATEGORY COUNTS:", json.dumps(imported["category_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
