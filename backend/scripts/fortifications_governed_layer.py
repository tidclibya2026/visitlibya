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

SOURCE_PATH = GIS / "fortifications-source.review.geojson"
ARCHAEOLOGY_BLOCKED_PATH = GIS / "archaeological-sites-governed-blocked.review.json"
MASTER_PATH = GIS / "master-atlas-source-registry.v2.json"

IMPORT_PATH = GIS / "fortifications-governed-import.review.geojson"
BLOCKED_PATH = GIS / "fortifications-governed-blocked.review.json"

LAYER_CODE = "FORTIFICATIONS"
ARTIFACT_STATUS = "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"


class FortificationsGovernedLayerError(ValueError):
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
    value = value.replace("\u200e", "").replace("\u200f", "")
    value = value.replace("\u202a", "").replace("\u202b", "")
    value = value.replace("\u202c", "")
    value = re.sub(r"[\s_\-]+", " ", value)

    return value.strip()


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
    return (
        round(float(coords[0]), 7),
        round(float(coords[1]), 7),
    )


def archaeological_cross_layer_refs():
    if not ARCHAEOLOGY_BLOCKED_PATH.is_file():
        return []

    payload = load(ARCHAEOLOGY_BLOCKED_PATH)

    return [
        record
        for record in payload.get("records", [])
        if record.get("review_classification")
        == "CROSS_LAYER_REFERENCE_FORTIFICATIONS"
    ]


def build():
    source = load(SOURCE_PATH)
    master = load(MASTER_PATH)

    if source.get("layer_code") != LAYER_CODE:
        raise FortificationsGovernedLayerError(
            "Source layer_code does not match FORTIFICATIONS"
        )

    features = source.get("features", [])

    if len(features) != 12:
        raise FortificationsGovernedLayerError(
            "Expected exactly 12 fortification source features"
        )

    master_matches = [
        item
        for item in master.get("layers", [])
        if item.get("source_layer") == "القلاع_والحصون"
        and item.get("target_layer") == LAYER_CODE
    ]

    if len(master_matches) != 1:
        raise FortificationsGovernedLayerError(
            "Master registry must contain exactly one fortifications mapping"
        )

    prepared = []
    name_counts = Counter()
    coord_counts = Counter()

    for feature in features:
        props = feature.get("properties", {})
        attrs = props.get("source_attributes") or {}
        geom = feature.get("geometry")

        if not geom:
            raise FortificationsGovernedLayerError(
                "Missing source geometry"
            )

        shp = shape(geom)

        if shp.geom_type != "Point":
            raise FortificationsGovernedLayerError(
                "Only Point source geometry is supported"
            )

        if shp.is_empty or not shp.is_valid:
            raise FortificationsGovernedLayerError(
                "Invalid fortification geometry"
            )

        x, y = shp.x, shp.y

        if not all(math.isfinite(v) for v in (x, y)):
            raise FortificationsGovernedLayerError(
                "Non-finite fortification coordinate"
            )

        if not (-180 <= x <= 180 and -90 <= y <= 90):
            raise FortificationsGovernedLayerError(
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

    cross_refs = archaeological_cross_layer_refs()

    cross_ref_coords = {
        point_key(record["geometry"])
        for record in cross_refs
        if record.get("geometry", {}).get("type") == "Point"
    }

    governed = []
    blocked = []

    evidence = {
        "source": semantic_sha256(SOURCE_PATH),
        "master_registry": semantic_sha256(MASTER_PATH),
        "archaeology_cross_layer": (
            semantic_sha256(ARCHAEOLOGY_BLOCKED_PATH)
            if ARCHAEOLOGY_BLOCKED_PATH.is_file()
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

        classification = "SAFE_FORTIFICATION_POINT"

        if not normalized:
            classification = "SOURCE_IDENTITY_REVIEW"

        elif name_counts[normalized] > 1:
            classification = "DUPLICATE_NAME_REVIEW"

        elif coord_counts[coordinate] > 1:
            classification = "DUPLICATE_GEOMETRY_REVIEW"

        metadata = {
            "artifact_status": ARTIFACT_STATUS,
            "review_classification": classification,
            "source_database": "Libya ATLAS Project.gdb",
            "source_layer": "القلاع_والحصون",
            "source_feature_id": oid,
            "source_semantic_sha256": evidence["source"],
            "master_registry_semantic_sha256": evidence["master_registry"],
            "archaeology_cross_layer_semantic_sha256":
                evidence["archaeology_cross_layer"],
            "source_attributes":
                source_props.get("source_attributes") or {},
            "cross_layer_reference_match":
                coordinate in cross_ref_coords,
            "authoritative_boundary_claimed": False,
        }

        if classification == "SAFE_FORTIFICATION_POINT":
            governed.append(
                {
                    "type": "Feature",
                    "properties": {
                        "feature_code":
                            "fortification-atlas-%s" % oid,
                        "institutional_id":
                            "atlas-fortification-%s" % oid,
                        "source_feature_id": oid,
                        "name_ar": name,
                        "name_en": None,
                        "category": "fortification",
                        "review_classification":
                            classification,
                        "source_identity":
                            "Libya ATLAS Project.gdb#القلاع_والحصون-%s"
                            % oid,
                        "source_metadata": metadata,
                    },
                    "geometry": source_feature["geometry"],
                }
            )

        else:
            blocked.append(
                {
                    "institutional_id":
                        "atlas-fortification-%s" % oid,
                    "source_feature_id": oid,
                    "name_ar": name,
                    "review_classification":
                        classification,
                    "blocked_reason":
                        classification,
                    "geometry_type":
                        source_feature["geometry"]["type"],
                    "geometry":
                        source_feature["geometry"],
                    "source_metadata":
                        metadata,
                }
            )

    unresolved_cross_refs = []

    governed_coords = {
        point_key(feature["geometry"])
        for feature in governed
    }

    for record in cross_refs:
        geom = record.get("geometry") or {}

        if geom.get("type") != "Point":
            continue

        coord = point_key(geom)

        if coord not in governed_coords:
            unresolved_cross_refs.append(
                {
                    "source_layer":
                        "ARCHAEOLOGICAL_SITES",
                    "source_feature_id":
                        record.get("source_feature_id"),
                    "name_ar":
                        record.get("name_ar"),
                    "review_classification":
                        "UNRESOLVED_CROSS_LAYER_REFERENCE",
                    "geometry":
                        geom,
                }
            )

    counts = Counter(
        ["SAFE_FORTIFICATION_POINT"] * len(governed)
        + [
            item["review_classification"]
            for item in blocked
        ]
    )

    common = {
        "artifact_status": ARTIFACT_STATUS,
        "layer_code": LAYER_CODE,
        "publication_approved": False,
        "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "source_database": "Libya ATLAS Project.gdb",
        "source_layer": "القلاع_والحصون",
        "source_feature_count": 12,
        "master_registry_version": "v2",
        "category_counts":
            dict(sorted(counts.items())),
        "evidence_semantic_sha256":
            evidence,
    }

    imported = {
        "type": "FeatureCollection",
        "name": "FORTIFICATIONS governed review import",
        **common,
        "features": governed,
    }

    blocked_payload = {
        "schema_version": 1,
        "inventory_id":
            "fortifications-governed-blocked-v1",
        **common,
        "safe_ingestible_feature_count":
            len(governed),
        "blocked_feature_count":
            len(blocked),
        "unresolved_cross_layer_reference_count":
            len(unresolved_cross_refs),
        "records":
            blocked,
        "unresolved_cross_layer_references":
            unresolved_cross_refs,
    }

    return imported, blocked_payload


def validate():
    imported, blocked = build()

    for path, expected in (
        (IMPORT_PATH, imported),
        (BLOCKED_PATH, blocked),
    ):
        if not path.is_file():
            raise FortificationsGovernedLayerError(
                "Governed artifact missing: %s"
                % path.name
            )

        if path.read_bytes() != canonical_bytes(expected):
            raise FortificationsGovernedLayerError(
                "Governed artifact stale: %s"
                % path.name
            )

    if (
        len(imported["features"])
        + len(blocked["records"])
        != 12
    ):
        raise FortificationsGovernedLayerError(
            "Every fortification source record must resolve exactly once"
        )

    codes = [
        feature["properties"]["feature_code"]
        for feature in imported["features"]
    ]

    if len(codes) != len(set(codes)):
        raise FortificationsGovernedLayerError(
            "Duplicate governed feature_code"
        )

    return imported, blocked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.write:
        imported, blocked = build()

        IMPORT_PATH.write_bytes(
            canonical_bytes(imported)
        )

        BLOCKED_PATH.write_bytes(
            canonical_bytes(blocked)
        )

    imported, blocked = validate()

    print(
        "FORTIFICATIONS GOVERNED REVIEW ARTIFACTS VALID"
    )
    print(
        "SOURCE COUNT:",
        imported["source_feature_count"],
    )
    print(
        "SAFE INGESTIBLE:",
        len(imported["features"]),
    )
    print(
        "BLOCKED:",
        len(blocked["records"]),
    )
    print(
        "UNRESOLVED CROSS-LAYER REFERENCES:",
        len(
            blocked[
                "unresolved_cross_layer_references"
            ]
        ),
    )
    print(
        "CATEGORY COUNTS:",
        json.dumps(
            imported["category_counts"],
            sort_keys=True,
        ),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
