#!/usr/bin/env python3
"""Validate the blocked Cyrene WORLD_HERITAGE anchor review deterministically."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = ROOT / "backend/data/gis/cyrene-world-heritage-anchor.review.json"
CANONICAL_REVIEW_PATH = ROOT / "backend/data/gis/canonical-destination-coordinate-review.json"
REGISTRY_PATH = ROOT / "backend/data/destinations/national-destination-registry.review.json"


class CyreneAnchorReviewError(ValueError):
    """Raised when the blocked anchor evidence or governance contract changes."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _haversine_m(a: dict[str, Any], b: dict[str, Any]) -> float:
    radius = 6_371_008.8
    lon1, lat1 = math.radians(a["longitude"]), math.radians(a["latitude"])
    lon2, lat2 = math.radians(b["longitude"]), math.radians(b["latitude"])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def validate_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    if artifact.get("layer_code") != "WORLD_HERITAGE":
        raise CyreneAnchorReviewError("layer must remain WORLD_HERITAGE")
    evidence = artifact.get("coordinate_evidence", [])
    if len(evidence) != 2 or any(item.get("crs") != "EPSG:4326" for item in evidence):
        raise CyreneAnchorReviewError("two WGS84 coordinate candidates must be preserved")
    for item in evidence:
        if not (-180 <= item["longitude"] <= 180 and -90 <= item["latitude"] <= 90):
            raise CyreneAnchorReviewError("coordinate outside WGS84 limits")
    distance = round(_haversine_m(evidence[0], evidence[1]), 3)
    if distance != artifact["coordinate_conflict"].get("distance_m") or distance < 1000:
        raise CyreneAnchorReviewError("material coordinate conflict changed")
    decision = artifact.get("geometry_decision", {})
    if decision != {
        "classification": "NO_SAFE_GEOMETRY",
        "canonical_site_anchor_ready": False,
        "world_heritage_ingestion_eligible": False,
        "ingestion_feature": None,
        "polygon_claimed_as_unesco_boundary": False,
    }:
        raise CyreneAnchorReviewError("geometry decision must remain fail-closed")
    governance = artifact.get("governance", {})
    required = {
        "review_status": "blocked",
        "authority_status": "unapproved",
        "is_published": False,
        "institutional_approval": False,
        "publication_approval": False,
        "runtime_mutation": False,
        "postgis_ingestion_performed": False,
    }
    if governance != required:
        raise CyreneAnchorReviewError("governance must remain unapproved and unpublished")

    canonical = _load(CANONICAL_REVIEW_PATH)
    candidates = [
        candidate
        for destination in canonical["destinations"]
        for candidate in destination["candidates"]
        if candidate["source_feature_id"] == artifact["institutional_property_evidence"]["source_feature_id"]
    ]
    if len(candidates) != 1:
        raise CyreneAnchorReviewError("institutional property source feature must resolve once")
    candidate = candidates[0]
    source = artifact["institutional_property_evidence"]
    for key in ("source_id", "source_file", "source_sha256", "source_feature_id", "source_reference", "source_name"):
        if source[key] != candidate[key]:
            raise CyreneAnchorReviewError(f"institutional property evidence changed: {key}")
    if [candidate["longitude"], candidate["latitude"]] != [evidence[0]["longitude"], evidence[0]["latitude"]]:
        raise CyreneAnchorReviewError("Placemark geometry changed")

    registry = _load(REGISTRY_PATH)
    record = next(item for item in registry["records"] if item["registry_record_id"] == "ndr-shahat-cyrene")
    destination = artifact["destination_identity"]
    if record["name_en"] != destination["project_name_en"] or record["name_ar"] != destination["project_name_ar"]:
        raise CyreneAnchorReviewError("project destination identity changed")
    if record["current_canonical_slug"] is not None or destination["current_canonical_slug"] is not None:
        raise CyreneAnchorReviewError("Cyrene must not claim a runtime canonical slug")
    return {"classification": "NO_SAFE_GEOMETRY", "coordinate_candidates": 2, "distance_m": distance}


def validate_serialization() -> None:
    artifact = _load(ARTIFACT_PATH)
    expected = (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if ARTIFACT_PATH.read_bytes() != expected:
        raise CyreneAnchorReviewError("artifact serialization is not deterministic UTF-8")


def main() -> int:
    try:
        result = validate_artifact(_load(ARTIFACT_PATH))
        validate_serialization()
    except (OSError, KeyError, StopIteration, json.JSONDecodeError, CyreneAnchorReviewError) as exc:
        print(f"Cyrene WORLD_HERITAGE anchor review failed: {exc}")
        return 1
    print("Cyrene WORLD_HERITAGE anchor review passed: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
