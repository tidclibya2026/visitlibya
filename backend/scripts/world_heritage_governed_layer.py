#!/usr/bin/env python3
"""Build and validate the non-public WORLD_HERITAGE governed import artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COORDINATES_PATH = ROOT / "backend/data/dev/destination-coordinates.reviewed.json"
OUTPUT_PATH = ROOT / "backend/data/gis/world-heritage-governed-import.review.geojson"
SOURCE_FILE = "مواقع التراث العالمي الخمسة_LY.kml"
SOURCE_SHA256 = "07f88ae5fbcad07d7d653d3a4a8ca6c6f1c77772b4fe6adba6aabfc7f4def555"

SITES = {
    "leptis-magna": ("لبدة الكبرى", "Leptis Magna", "ndr-leptis-magna"),
    "sabratha": ("صبراتة", "Sabratha", "ndr-sabratha"),
    "acacus": ("تادرارت أكاكوس", "Tadrart Acacus", "ndr-acacus"),
    "old-city-ghadames": ("مدينة غدامس القديمة", "Old Town of Ghadames", "ndr-ghadames"),
}


class WorldHeritageLayerError(ValueError):
    """Raised when reviewed evidence cannot produce the governed import artifact."""


def build() -> dict:
    source = json.loads(COORDINATES_PATH.read_text(encoding="utf-8"))
    records = {record["slug"]: record for record in source["records"]}
    features = []
    for slug, (name_ar, name_en, registry_id) in SITES.items():
        record = records.get(slug)
        if not record or record.get("status") != "reviewed":
            raise WorldHeritageLayerError(f"Missing reviewed coordinate: {slug}")
        reference = record.get("source_reference", "")
        if not reference.startswith(f"{SOURCE_FILE}#Placemark-"):
            raise WorldHeritageLayerError(f"Unexpected source reference: {slug}")
        source_feature_id = reference.rsplit("#", 1)[1]
        features.append({
            "type": "Feature",
            "properties": {
                "feature_code": f"world-heritage-{slug}",
                "institutional_id": registry_id,
                "source_feature_id": source_feature_id,
                "name_ar": name_ar,
                "name_en": name_en,
                "category": "heritage",
                "source_identity": reference,
                "source_metadata": {
                    "artifact_status": "REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL",
                    "coordinate_review_status": "reviewed",
                    "destination_registry_id": registry_id,
                    "source_file": SOURCE_FILE,
                    "source_sha256": SOURCE_SHA256,
                },
            },
            "geometry": {
                "type": "Point",
                "coordinates": [record["longitude"], record["latitude"]],
            },
        })
    return {
        "type": "FeatureCollection",
        "name": "WORLD_HERITAGE governed review import",
        "artifact_status": "REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL",
        "layer_code": "WORLD_HERITAGE",
        "publication_approved": False,
        "source_database": "institutional-kml-review",
        "source_layer": "unesco-five-sites-ly",
        "excluded_sites": [{
            "site": "cyrene",
            "reason": "REVIEW_REQUIRED_AGGREGATE_NO_REVIEWED_CANONICAL_SITE_ANCHOR",
        }],
        "features": features,
    }


def canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def validate() -> dict:
    expected = canonical_bytes(build())
    if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_bytes() != expected:
        raise WorldHeritageLayerError("Governed import artifact is missing or stale")
    return json.loads(expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        OUTPUT_PATH.write_bytes(canonical_bytes(build()))
    artifact = validate()
    print("WORLD_HERITAGE GOVERNED IMPORT VALID")
    print("FEATURE COUNT:", len(artifact["features"]))
    print("PUBLICATION APPROVED:", artifact["publication_approved"])
    print("EXCLUDED SITES:", len(artifact["excluded_sites"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
