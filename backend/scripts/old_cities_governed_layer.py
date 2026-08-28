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

SOURCE_PATH = GIS / "old-cities-source.review.geojson"
MASTER_PATH = GIS / "master-atlas-source-registry.v2.json"

WORLD_HERITAGE_PATH = (
    GIS / "world-heritage-governed-import.review.geojson"
)

OLD_TRIPOLI_PATH = (
    GIS / "old-tripoli-governed-import.review.geojson"
)

IMPORT_PATH = (
    GIS / "old-cities-governed-import.review.geojson"
)

BLOCKED_PATH = (
    GIS / "old-cities-governed-blocked.review.json"
)

LAYER_CODE = "OLD_CITIES"

ARTIFACT_STATUS = (
    "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"
)


class OldCitiesGovernedLayerError(ValueError):
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

    value = unicodedata.normalize(
        "NFKC",
        str(value),
    )

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

    value = re.sub(
        r"[\s_\-]+",
        " ",
        value,
    )

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

        if (
            "name" in str(key).lower()
            or "اسم" in str(key)
        ):
            return str(value).strip()

    return None


def point_key(geometry):
    coords = geometry["coordinates"]

    return (
        round(float(coords[0]), 7),
        round(float(coords[1]), 7),
    )


def authority_names(path):
    names = set()

    if not path.is_file():
        return names

    payload = load(path)

    for feature in payload.get("features", []):
        props = feature.get("properties") or {}

        for key in (
            "name_ar",
            "name_en",
        ):
            value = normalize_name(
                props.get(key)
            )

            if value:
                names.add(value)

    return names


def build():
    source = load(SOURCE_PATH)
    master = load(MASTER_PATH)

    if source.get("layer_code") != LAYER_CODE:
        raise OldCitiesGovernedLayerError(
            "Source layer_code mismatch"
        )

    features = source.get("features") or []

    if len(features) != 27:
        raise OldCitiesGovernedLayerError(
            "Expected exactly 27 OLD_CITIES source features"
        )

    master_matches = [
        item
        for item in master.get("layers", [])
        if item.get("source_layer") == "مدن_قديمة"
        and item.get("target_layer") == LAYER_CODE
    ]

    if len(master_matches) != 1:
        raise OldCitiesGovernedLayerError(
            "Master registry OLD_CITIES mapping is not unique"
        )

    wh_names = authority_names(
        WORLD_HERITAGE_PATH
    )

    old_tripoli_names = authority_names(
        OLD_TRIPOLI_PATH
    )

    prepared = []
    name_counts = Counter()
    coord_counts = Counter()

    for feature in features:
        props = feature.get("properties") or {}
        attrs = props.get(
            "source_attributes"
        ) or {}

        geom = feature.get("geometry")

        if not geom:
            raise OldCitiesGovernedLayerError(
                "Missing geometry"
            )

        shp = shape(geom)

        if (
            shp.geom_type != "Point"
            or shp.is_empty
            or not shp.is_valid
        ):
            raise OldCitiesGovernedLayerError(
                "OLD_CITIES source must contain valid Points"
            )

        x, y = shp.x, shp.y

        if not all(
            math.isfinite(v)
            for v in (x, y)
        ):
            raise OldCitiesGovernedLayerError(
                "Non-finite coordinate"
            )

        name = extract_name(attrs)
        normalized = normalize_name(name)

        coord = point_key(geom)

        if normalized:
            name_counts[normalized] += 1

        coord_counts[coord] += 1

        prepared.append(
            {
                "source": feature,
                "name": name,
                "normalized": normalized,
                "coordinate": coord,
            }
        )

    governed = []
    blocked = []

    evidence = {
        "source":
            semantic_sha256(SOURCE_PATH),

        "master_registry":
            semantic_sha256(MASTER_PATH),

        "world_heritage":
            (
                semantic_sha256(
                    WORLD_HERITAGE_PATH
                )
                if WORLD_HERITAGE_PATH.is_file()
                else None
            ),

        "old_tripoli":
            (
                semantic_sha256(
                    OLD_TRIPOLI_PATH
                )
                if OLD_TRIPOLI_PATH.is_file()
                else None
            ),
    }

    generic_names = {
        "مدينة قديمة",
        "المدينة القديمة",
        "بلدة قديمة",
        "البلدة القديمة",
    }

    wrong_layer_names = {
        "مدينة ملاهي",
        "ملاهي",
    }

    for item in prepared:
        feature = item["source"]

        props = feature.get(
            "properties"
        ) or {}

        oid = str(
            props.get(
                "source_feature_id"
            )
        )

        name = item["name"]
        normalized = item["normalized"]
        coordinate = item["coordinate"]

        classification = (
            "SAFE_OLD_CITY_POINT"
        )

        if not normalized:
            classification = (
                "SOURCE_IDENTITY_REVIEW"
            )

        elif normalized in wrong_layer_names:
            classification = (
                "WRONG_LAYER_SEMANTICS"
            )

        elif normalized in generic_names:
            classification = (
                "SOURCE_IDENTITY_REVIEW"
            )

        elif (
            "غدامس" in normalized
            or normalized in wh_names
        ):
            classification = (
                "CROSS_LAYER_REFERENCE_WORLD_HERITAGE"
            )

        elif (
            "طرابلس" in normalized
            or normalized in old_tripoli_names
        ):
            classification = (
                "CROSS_LAYER_REFERENCE_OLD_TRIPOLI"
            )

        elif name_counts[normalized] > 1:
            classification = (
                "IDENTITY_RECONCILIATION_REVIEW"
            )

        elif coord_counts[coordinate] > 1:
            classification = (
                "DUPLICATE_GEOMETRY_REVIEW"
            )

        metadata = {
            "artifact_status":
                ARTIFACT_STATUS,

            "review_classification":
                classification,

            "source_database":
                "Libya ATLAS Project.gdb",

            "source_layer":
                "مدن_قديمة",

            "source_feature_id":
                oid,

            "source_semantic_sha256":
                evidence["source"],

            "master_registry_semantic_sha256":
                evidence["master_registry"],

            "world_heritage_semantic_sha256":
                evidence["world_heritage"],

            "old_tripoli_semantic_sha256":
                evidence["old_tripoli"],

            "source_attributes":
                props.get(
                    "source_attributes"
                ) or {},

            "authoritative_boundary_claimed":
                False,

            "world_heritage_authority_created":
                False,

            "old_tripoli_authority_created":
                False,
        }

        if (
            classification
            == "SAFE_OLD_CITY_POINT"
        ):
            governed.append(
                {
                    "type": "Feature",

                    "properties": {
                        "feature_code":
                            "old-city-atlas-%s"
                            % oid,

                        "institutional_id":
                            "atlas-old-city-%s"
                            % oid,

                        "source_feature_id":
                            oid,

                        "name_ar":
                            name,

                        "name_en":
                            None,

                        "category":
                            "old_city",

                        "review_classification":
                            classification,

                        "source_identity":
                            (
                                "Libya ATLAS Project.gdb"
                                "#مدن_قديمة-%s"
                                % oid
                            ),

                        "source_metadata":
                            metadata,
                    },

                    "geometry":
                        feature["geometry"],
                }
            )

        else:
            blocked.append(
                {
                    "institutional_id":
                        "atlas-old-city-%s"
                        % oid,

                    "source_feature_id":
                        oid,

                    "name_ar":
                        name,

                    "review_classification":
                        classification,

                    "blocked_reason":
                        classification,

                    "geometry_type":
                        feature[
                            "geometry"
                        ]["type"],

                    "geometry":
                        feature["geometry"],

                    "source_metadata":
                        metadata,
                }
            )

    counts = Counter(
        ["SAFE_OLD_CITY_POINT"]
        * len(governed)
        + [
            record[
                "review_classification"
            ]
            for record in blocked
        ]
    )

    common = {
        "artifact_status":
            ARTIFACT_STATUS,

        "layer_code":
            LAYER_CODE,

        "publication_approved":
            False,

        "canonical_identity_approved":
            False,

        "authoritative_boundary_claimed":
            False,

        "source_database":
            "Libya ATLAS Project.gdb",

        "source_layer":
            "مدن_قديمة",

        "source_feature_count":
            27,

        "master_registry_version":
            "v2",

        "category_counts":
            dict(
                sorted(
                    counts.items()
                )
            ),

        "evidence_semantic_sha256":
            evidence,
    }

    imported = {
        "type":
            "FeatureCollection",

        "name":
            "OLD_CITIES governed review import",

        **common,

        "features":
            governed,
    }

    blocked_payload = {
        "schema_version":
            1,

        "inventory_id":
            "old-cities-governed-blocked-v1",

        **common,

        "safe_ingestible_feature_count":
            len(governed),

        "blocked_feature_count":
            len(blocked),

        "records":
            blocked,
    }

    return imported, blocked_payload


def validate():
    imported, blocked = build()

    for path, expected in (
        (IMPORT_PATH, imported),
        (BLOCKED_PATH, blocked),
    ):
        if not path.is_file():
            raise OldCitiesGovernedLayerError(
                "Artifact missing: %s"
                % path.name
            )

        if (
            path.read_bytes()
            != canonical_bytes(
                expected
            )
        ):
            raise OldCitiesGovernedLayerError(
                "Artifact stale: %s"
                % path.name
            )

    total = (
        len(imported["features"])
        + len(blocked["records"])
    )

    if total != 27:
        raise OldCitiesGovernedLayerError(
            "OLD_CITIES accounting failed"
        )

    codes = [
        feature[
            "properties"
        ]["feature_code"]
        for feature
        in imported["features"]
    ]

    if len(codes) != len(set(codes)):
        raise OldCitiesGovernedLayerError(
            "Duplicate governed feature_code"
        )

    return imported, blocked


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write",
        action="store_true",
    )

    args = parser.parse_args()

    if args.write:
        imported, blocked = build()

        IMPORT_PATH.write_bytes(
            canonical_bytes(
                imported
            )
        )

        BLOCKED_PATH.write_bytes(
            canonical_bytes(
                blocked
            )
        )

    imported, blocked = validate()

    print(
        "OLD_CITIES GOVERNED REVIEW ARTIFACTS VALID"
    )

    print(
        "SOURCE COUNT:",
        imported[
            "source_feature_count"
        ],
    )

    print(
        "SAFE INGESTIBLE:",
        len(
            imported["features"]
        ),
    )

    print(
        "BLOCKED:",
        len(
            blocked["records"]
        ),
    )

    print(
        "CATEGORY COUNTS:",
        json.dumps(
            imported[
                "category_counts"
            ],
            ensure_ascii=False,
            sort_keys=True,
        ),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
