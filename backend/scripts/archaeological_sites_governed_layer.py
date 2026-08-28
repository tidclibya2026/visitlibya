#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
GIS = ROOT / "backend/data/gis"

SOURCE_PATH = GIS / "archaeological-sites-source.review.geojson"
MASTER_PATH = GIS / "master-atlas-source-registry.v2.json"
AUTHORITY_PATH = GIS / "master-atlas-authority-map.v2.json"
WORLD_HERITAGE_PATH = GIS / "world-heritage-governed-import.review.geojson"

IMPORT_PATH = GIS / "archaeological-sites-governed-import.review.geojson"
BLOCKED_PATH = GIS / "archaeological-sites-governed-blocked.review.json"

LAYER_CODE = "ARCHAEOLOGICAL_SITES"
ARTIFACT_STATUS = "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"


class ArchaeologicalSitesGovernedLayerError(ValueError):
    pass


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(payload):
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def semantic_sha256(path: Path) -> str:
    payload = load(path)
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_name(value):
    if not value:
        return ""
    value = str(value).strip().lower()
    value = re.sub(r"[\s_\-]+", " ", value)
    return value


def extract_name(attrs):
    preferred = (
        "name_ar",
        "Name_AR",
        "NAME_AR",
        "name",
        "Name",
        "NAME",
        "الاسم",
        "اسم",
    )
    for key in preferred:
        value = attrs.get(key)
        if value not in (None, ""):
            return str(value).strip()

    for key, value in attrs.items():
        if value in (None, ""):
            continue
        lowered = str(key).lower()
        if "name" in lowered or "اسم" in str(key):
            return str(value).strip()

    return None


def point_key(geometry):
    coords = geometry["coordinates"]
    return (round(float(coords[0]), 7), round(float(coords[1]), 7))


def world_heritage_evidence():
    if not WORLD_HERITAGE_PATH.is_file():
        return set(), set()

    payload = load(WORLD_HERITAGE_PATH)
    names = set()
    coords = set()

    for feature in payload.get("features", []):
        props = feature.get("properties", {})

        for key in ("name_ar", "name_en"):
            name = normalize_name(props.get(key))
            if name:
                names.add(name)

        geom = feature.get("geometry") or {}
        if geom.get("type") == "Point":
            coords.add(point_key(geom))

    return names, coords


def build():
    source = load(SOURCE_PATH)
    master = load(MASTER_PATH)
    authority = load(AUTHORITY_PATH)

    if source.get("layer_code") != LAYER_CODE:
        raise ArchaeologicalSitesGovernedLayerError(
            "Source layer_code does not match ARCHAEOLOGICAL_SITES"
        )

    features = source.get("features", [])

    if len(features) != 11:
        raise ArchaeologicalSitesGovernedLayerError(
            "Expected exactly 11 net-new archaeological source features"
        )

    master_layers = master.get("layers", [])
    matches = [
        item
        for item in master_layers
        if item.get("source_layer") == "اثري"
        and item.get("target_layer") == LAYER_CODE
    ]

    if len(matches) != 1:
        raise ArchaeologicalSitesGovernedLayerError(
            "Master registry must contain exactly one 'اثري' layer mapping"
        )

    world_names, world_coords = world_heritage_evidence()

    name_counts = Counter()
    coord_counts = Counter()

    prepared = []

    for feature in features:
        props = feature.get("properties", {})
        attrs = props.get("source_attributes") or {}
        geom = feature.get("geometry")

        if not geom:
            raise ArchaeologicalSitesGovernedLayerError("Missing source geometry")

        shp = shape(geom)

        if shp.geom_type != "Point" or shp.is_empty or not shp.is_valid:
            raise ArchaeologicalSitesGovernedLayerError(
                "Only valid Point geometry is allowed"
            )

        x, y = shp.x, shp.y

        if not all(math.isfinite(v) for v in (x, y)):
            raise ArchaeologicalSitesGovernedLayerError(
                "Non-finite archaeological coordinate"
            )

        if not (-180 <= x <= 180 and -90 <= y <= 90):
            raise ArchaeologicalSitesGovernedLayerError(
                "Coordinate outside WGS84 limits"
            )

        name = extract_name(attrs)
        normalized = normalize_name(name)
        coordinate = point_key(geom)

        if normalized:
            name_counts[normalized] += 1

        coord_counts[coordinate] += 1

        prepared.append(
            {
                "source": feature,
                "name": name,
                "normalized_name": normalized,
                "coordinate": coordinate,
            }
        )

    governed = []
    blocked = []

    evidence = {
        "source_extract": semantic_sha256(SOURCE_PATH),
        "master_registry": semantic_sha256(MASTER_PATH),
        "authority_map": semantic_sha256(AUTHORITY_PATH),
        "world_heritage": (
            semantic_sha256(WORLD_HERITAGE_PATH)
            if WORLD_HERITAGE_PATH.is_file()
            else None
        ),
    }

    for item in prepared:
        source_feature = item["source"]
        source_props = source_feature["properties"]
        oid = str(source_props["source_feature_id"])
        name = item["name"]
        normalized = item["normalized_name"]
        coordinate = item["coordinate"]

        classification = "SAFE_ARCHAEOLOGICAL_POINT"

        generic_identity_names = {
            "اثري",
            "أثري",
            "موقع اثري",
            "موقع أثري",
            "اطلال",
            "أطلال",
        }

        fortification_names = {
            "قلعة",
            "حصن",
            "قصر محصن",
        }

        if normalized and normalized in world_names:
            classification = "WORLD_HERITAGE_OVERLAP_CONTEXT"

        elif coordinate in world_coords:
            classification = "WORLD_HERITAGE_OVERLAP_CONTEXT"

        elif normalized in fortification_names:
            classification = "CROSS_LAYER_REFERENCE_FORTIFICATIONS"

        elif coord_counts[coordinate] > 1:
            classification = "DUPLICATE_GEOMETRY_REVIEW"

        elif normalized in generic_identity_names:
            classification = "SOURCE_IDENTITY_REVIEW"

        elif not normalized:
            classification = "SOURCE_IDENTITY_REVIEW"

        common_metadata = {
            "artifact_status": ARTIFACT_STATUS,
            "review_classification": classification,
            "source_database": "Libya ATLAS Project.gdb",
            "source_layer": "اثري",
            "source_feature_id": oid,
            "source_semantic_sha256": evidence["source_extract"],
            "master_registry_semantic_sha256": evidence["master_registry"],
            "authority_map_semantic_sha256": evidence["authority_map"],
            "world_heritage_semantic_sha256": evidence["world_heritage"],
            "source_attributes": source_props.get("source_attributes") or {},
            "cross_layer_authority_created": False,
            "world_heritage_authority_created": False,
            "archaeological_boundary_claimed": False,
        }

        if classification == "SAFE_ARCHAEOLOGICAL_POINT":
            governed.append(
                {
                    "type": "Feature",
                    "properties": {
                        "feature_code": "archaeological-site-atlas-%s" % oid,
                        "institutional_id": "atlas-archaeological-%s" % oid,
                        "source_feature_id": oid,
                        "name_ar": name,
                        "name_en": None,
                        "category": "archaeology",
                        "review_classification": classification,
                        "source_identity": "Libya ATLAS Project.gdb#اثري-%s" % oid,
                        "source_metadata": common_metadata,
                    },
                    "geometry": source_feature["geometry"],
                }
            )
        else:
            blocked.append(
                {
                    "institutional_id": "atlas-archaeological-%s" % oid,
                    "source_feature_id": oid,
                    "name_ar": name,
                    "review_classification": classification,
                    "blocked_reason": classification,
                    "geometry_type": source_feature["geometry"]["type"],
                    "geometry": source_feature["geometry"],
                    "source_metadata": common_metadata,
                }
            )

    counts = Counter(
        ["SAFE_ARCHAEOLOGICAL_POINT"] * len(governed)
        + [item["review_classification"] for item in blocked]
    )

    common = {
        "artifact_status": ARTIFACT_STATUS,
        "layer_code": LAYER_CODE,
        "publication_approved": False,
        "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "world_heritage_authority_duplicated": False,
        "source_database": "Libya ATLAS Project.gdb",
        "source_layer": "اثري",
        "master_registry_version": "v2",
        "source_feature_count": 11,
        "category_counts": dict(sorted(counts.items())),
        "evidence_semantic_sha256": evidence,
    }

    imported = {
        "type": "FeatureCollection",
        "name": "ARCHAEOLOGICAL_SITES governed review import",
        **common,
        "features": governed,
    }

    blocked_payload = {
        "schema_version": 1,
        "inventory_id": "archaeological-sites-governed-blocked-v1",
        **common,
        "safe_ingestible_feature_count": len(governed),
        "blocked_feature_count": len(blocked),
        "records": blocked,
    }

    return imported, blocked_payload


def validate():
    imported, blocked = build()

    for path, expected in (
        (IMPORT_PATH, imported),
        (BLOCKED_PATH, blocked),
    ):
        if not path.is_file():
            raise ArchaeologicalSitesGovernedLayerError(
                "Governed artifact missing: %s" % path.name
            )

        if path.read_bytes() != canonical_bytes(expected):
            raise ArchaeologicalSitesGovernedLayerError(
                "Governed artifact stale: %s" % path.name
            )

    if len(imported["features"]) + len(blocked["records"]) != 11:
        raise ArchaeologicalSitesGovernedLayerError(
            "Every archaeological source record must resolve exactly once"
        )

    feature_codes = [
        feature["properties"]["feature_code"]
        for feature in imported["features"]
    ]

    if len(feature_codes) != len(set(feature_codes)):
        raise ArchaeologicalSitesGovernedLayerError(
            "Duplicate governed feature_code"
        )

    for feature in imported["features"]:
        if feature["properties"]["review_classification"] != "SAFE_ARCHAEOLOGICAL_POINT":
            raise ArchaeologicalSitesGovernedLayerError(
                "Blocked classification entered governed import"
            )

    return imported, blocked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.write:
        imported, blocked = build()
        IMPORT_PATH.write_bytes(canonical_bytes(imported))
        BLOCKED_PATH.write_bytes(canonical_bytes(blocked))

    imported, blocked = validate()

    print("ARCHAEOLOGICAL_SITES GOVERNED REVIEW ARTIFACTS VALID")
    print("SOURCE COUNT:", imported["source_feature_count"])
    print("SAFE INGESTIBLE:", len(imported["features"]))
    print("BLOCKED:", len(blocked["records"]))
    print(
        "CATEGORY COUNTS:",
        json.dumps(imported["category_counts"], sort_keys=True),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
