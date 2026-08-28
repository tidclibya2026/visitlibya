#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
GIS = ROOT / "backend/data/gis"

SOURCE_PATH = GIS / "historical-sites-source.review.geojson"
MASTER_PATH = GIS / "master-atlas-source-registry.v2.json"

WORLD_HERITAGE_PATH = GIS / "world-heritage-governed-import.review.geojson"
FORTIFICATIONS_PATH = GIS / "fortifications-governed-import.review.geojson"
OLD_CITIES_PATH = GIS / "old-cities-governed-import.review.geojson"

IMPORT_PATH = GIS / "historical-sites-governed-import.review.geojson"
BLOCKED_PATH = GIS / "historical-sites-governed-blocked.review.json"

LAYER_CODE = "HISTORICAL_SITES"
ARTIFACT_STATUS = "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"


class HistoricalSitesGovernedLayerError(ValueError):
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


def semantic_sha256(path: Path):
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

    value = unicodedata.normalize("NFKC", str(value))

    for char in (
        "\u200e",
        "\u200f",
        "\u202a",
        "\u202b",
        "\u202c",
        "\ufeff",
    ):
        value = value.replace(char, "")

    value = value.strip().lower()
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

        if "name" in str(key).lower() or "اسم" in str(key):
            return str(value).strip()

    return None


def point_key(geometry):
    coords = geometry["coordinates"]
    return (
        round(float(coords[0]), 7),
        round(float(coords[1]), 7),
    )


def authority_coords(path):
    coords = set()

    if not path.is_file():
        return coords

    payload = load(path)

    for feature in payload.get("features", []):
        geom = feature.get("geometry") or {}
        if geom.get("type") == "Point":
            coords.add(point_key(geom))

    return coords


def build():
    source = load(SOURCE_PATH)
    master = load(MASTER_PATH)

    if source.get("layer_code") != LAYER_CODE:
        raise HistoricalSitesGovernedLayerError(
            "Source layer_code does not match HISTORICAL_SITES"
        )

    features = source.get("features") or []

    if len(features) != 136:
        raise HistoricalSitesGovernedLayerError(
            "Expected exactly 136 historical source features"
        )

    expected_layers = {
        "كنائس",
        "مزارع_قديمة",
        "مسارح",
        "القصور",
        "الاضرحة",
    }

    master_layers = {
        item.get("source_layer")
        for item in master.get("layers", [])
        if item.get("target_layer") == LAYER_CODE
    }

    if expected_layers != master_layers:
        raise HistoricalSitesGovernedLayerError(
            "Master HISTORICAL_SITES source set mismatch"
        )

    wh_coords = authority_coords(WORLD_HERITAGE_PATH)
    fort_coords = authority_coords(FORTIFICATIONS_PATH)
    old_city_coords = authority_coords(OLD_CITIES_PATH)

    prepared = []
    name_counts = Counter()
    coord_counts = Counter()
    identity_geometry_counts = Counter()

    for feature in features:
        props = feature.get("properties") or {}
        attrs = props.get("source_attributes") or {}
        geom = feature.get("geometry")

        if not geom:
            raise HistoricalSitesGovernedLayerError(
                "Missing source geometry"
            )

        shp = shape(geom)

        if shp.geom_type != "Point" or shp.is_empty or not shp.is_valid:
            raise HistoricalSitesGovernedLayerError(
                "Historical source must contain valid Points"
            )

        x, y = shp.x, shp.y

        if not all(math.isfinite(v) for v in (x, y)):
            raise HistoricalSitesGovernedLayerError(
                "Non-finite historical coordinate"
            )

        if not (-180 <= x <= 180 and -90 <= y <= 90):
            raise HistoricalSitesGovernedLayerError(
                "Coordinate outside WGS84 limits"
            )

        name = extract_name(attrs)
        normalized = normalize_name(name)
        coordinate = point_key(geom)
        subtype = props.get("source_subtype")

        if normalized:
            name_counts[(subtype, normalized)] += 1
            identity_geometry_counts[
                (subtype, normalized, coordinate)
            ] += 1

        coord_counts[coordinate] += 1

        prepared.append({
            "source": feature,
            "name": name,
            "normalized": normalized,
            "coordinate": coordinate,
            "subtype": subtype,
        })

    governed = []
    blocked = []

    evidence = {
        "source": semantic_sha256(SOURCE_PATH),
        "master_registry": semantic_sha256(MASTER_PATH),
        "world_heritage": (
            semantic_sha256(WORLD_HERITAGE_PATH)
            if WORLD_HERITAGE_PATH.is_file()
            else None
        ),
        "fortifications": (
            semantic_sha256(FORTIFICATIONS_PATH)
            if FORTIFICATIONS_PATH.is_file()
            else None
        ),
        "old_cities": (
            semantic_sha256(OLD_CITIES_PATH)
            if OLD_CITIES_PATH.is_file()
            else None
        ),
    }

    generic_historic_farm_names = {
        "مزرعة محصنة",
        "مزارع محصنة",
    }

    seen_duplicate_identity_geometry = set()

    for item in prepared:
        feature = item["source"]
        props = feature.get("properties") or {}

        oid = str(props.get("source_feature_id"))
        source_layer = props.get("source_layer")
        subtype = item["subtype"]
        name = item["name"]
        normalized = item["normalized"]
        coordinate = item["coordinate"]

        classification = "SAFE_HISTORICAL_SITE_POINT"

        if not normalized:
            classification = "SOURCE_IDENTITY_REVIEW"

        elif (
            subtype == "historic_farm"
            and normalized in generic_historic_farm_names
        ):
            classification = "SOURCE_IDENTITY_REVIEW"

        elif identity_geometry_counts[
            (subtype, normalized, coordinate)
        ] > 1:
            key = (subtype, normalized, coordinate)

            if key in seen_duplicate_identity_geometry:
                classification = "DUPLICATE_GEOMETRY_IDENTITY_REVIEW"
            else:
                classification = "IDENTITY_RECONCILIATION_REVIEW"
                seen_duplicate_identity_geometry.add(key)

        elif coordinate in fort_coords:
            classification = "CROSS_LAYER_REFERENCE_FORTIFICATIONS"

        elif coordinate in old_city_coords:
            classification = "CROSS_LAYER_REFERENCE_OLD_CITIES"

        elif coordinate in wh_coords:
            classification = "CROSS_LAYER_REFERENCE_WORLD_HERITAGE"

        metadata = {
            "artifact_status": ARTIFACT_STATUS,
            "review_classification": classification,
            "source_database": "Libya ATLAS Project.gdb",
            "source_layer": source_layer,
            "source_subtype": subtype,
            "source_feature_id": oid,
            "source_semantic_sha256": evidence["source"],
            "master_registry_semantic_sha256": evidence["master_registry"],
            "world_heritage_semantic_sha256": evidence["world_heritage"],
            "fortifications_semantic_sha256": evidence["fortifications"],
            "old_cities_semantic_sha256": evidence["old_cities"],
            "source_attributes": props.get("source_attributes") or {},
            "authoritative_boundary_claimed": False,
            "cross_layer_authority_created": False,
        }

        if classification == "SAFE_HISTORICAL_SITE_POINT":
            governed.append({
                "type": "Feature",
                "properties": {
                    "feature_code":
                        "historical-%s-%s" % (subtype, oid),
                    "institutional_id":
                        "atlas-historical-%s-%s" % (subtype, oid),
                    "source_feature_id": oid,
                    "name_ar": name,
                    "name_en": None,
                    "category": "history",
                    "historical_subtype": subtype,
                    "review_classification": classification,
                    "source_identity":
                        "Libya ATLAS Project.gdb#%s-%s"
                        % (source_layer, oid),
                    "source_metadata": metadata,
                },
                "geometry": feature["geometry"],
            })
        else:
            blocked.append({
                "institutional_id":
                    "atlas-historical-%s-%s" % (subtype, oid),
                "source_feature_id": oid,
                "source_layer": source_layer,
                "historical_subtype": subtype,
                "name_ar": name,
                "review_classification": classification,
                "blocked_reason": classification,
                "geometry_type": feature["geometry"]["type"],
                "geometry": feature["geometry"],
                "source_metadata": metadata,
            })

    counts = Counter(
        ["SAFE_HISTORICAL_SITE_POINT"] * len(governed)
        + [
            record["review_classification"]
            for record in blocked
        ]
    )

    common = {
        "artifact_status": ARTIFACT_STATUS,
        "layer_code": LAYER_CODE,
        "publication_approved": False,
        "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "source_database": "Libya ATLAS Project.gdb",
        "source_feature_count": 136,
        "master_registry_version": "v2",
        "category_counts": dict(sorted(counts.items())),
        "evidence_semantic_sha256": evidence,
    }

    imported = {
        "type": "FeatureCollection",
        "name": "HISTORICAL_SITES governed review import",
        **common,
        "features": governed,
    }

    blocked_payload = {
        "schema_version": 1,
        "inventory_id":
            "historical-sites-governed-blocked-v1",
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
            raise HistoricalSitesGovernedLayerError(
                "Artifact missing: %s" % path.name
            )

        if path.read_bytes() != canonical_bytes(expected):
            raise HistoricalSitesGovernedLayerError(
                "Artifact stale: %s" % path.name
            )

    if (
        len(imported["features"])
        + len(blocked["records"])
        != 136
    ):
        raise HistoricalSitesGovernedLayerError(
            "Historical accounting failed"
        )

    codes = [
        feature["properties"]["feature_code"]
        for feature in imported["features"]
    ]

    if len(codes) != len(set(codes)):
        raise HistoricalSitesGovernedLayerError(
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

    print("HISTORICAL_SITES GOVERNED REVIEW ARTIFACTS VALID")
    print("SOURCE COUNT:", imported["source_feature_count"])
    print("SAFE INGESTIBLE:", len(imported["features"]))
    print("BLOCKED:", len(blocked["records"]))
    print(
        "CATEGORY COUNTS:",
        json.dumps(
            imported["category_counts"],
            ensure_ascii=False,
            sort_keys=True,
        ),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
