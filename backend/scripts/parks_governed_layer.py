#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GIS = ROOT / "backend/data/gis"
SOURCE_PATH = GIS / "parks-source.review.geojson"
MASTER_PATH = GIS / "master-atlas-source-registry.v2.json"
IMPORT_PATH = GIS / "parks-governed-import.review.geojson"
BLOCKED_PATH = GIS / "parks-governed-blocked.review.json"
CROSS_PATH = GIS / "parks-cross-layer-review.json"
LAYER_CODE = "PARKS"
STATUS = "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"
EXPECTED_LAYERS = {"منتزهات": 59, "المنتزهات_الوطنية_1": 12}
CROSS_LAYERS = {
    "NATURAL_SITES": GIS / "natural-sites-governed-import.review.geojson",
    "WORLD_HERITAGE": GIS / "world-heritage-governed-import.review.geojson",
    "OLD_CITIES": GIS / "old-cities-governed-import.review.geojson",
    "HISTORICAL_SITES": GIS / "historical-sites-governed-import.review.geojson",
    "FORTIFICATIONS": GIS / "fortifications-governed-import.review.geojson",
}


class ParksGovernedLayerError(ValueError):
    pass


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(payload):
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True,
                       allow_nan=False) + "\n").encode("utf-8")


def semantic_sha256(path: Path):
    raw = json.dumps(load(path), ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_name(value):
    value = unicodedata.normalize("NFKC", str(value or ""))
    for char in ("\u200e", "\u200f", "\u202a", "\u202b", "\u202c", "\ufeff"):
        value = value.replace(char, "")
    return re.sub(r"[\s_\-]+", " ", value.strip().lower()).strip()


def extract_name(attrs):
    for key in ("name_ar", "Name_AR", "NAME_AR", "name", "Name", "NAME",
                "الاسم", "اسم"):
        if attrs.get(key) not in (None, ""):
            return str(attrs[key]).strip()
    for key, value in attrs.items():
        if value not in (None, "") and ("name" in str(key).lower() or "اسم" in str(key)):
            return str(value).strip()
    return None


def point_key(geometry):
    return tuple(round(float(v), 7) for v in geometry["coordinates"][:2])


def valid_wgs84(geometry):
    coords = geometry.get("coordinates") or []
    if len(coords) < 2:
        return False
    x, y = float(coords[0]), float(coords[1])
    return all(math.isfinite(v) for v in (x, y)) and -180 <= x <= 180 and -90 <= y <= 90


def validate_source(source, master):
    if source.get("layer_code") != LAYER_CODE:
        raise ParksGovernedLayerError("Source layer_code does not match PARKS")
    if source.get("source_feature_count") != 71 or source.get("extracted_feature_count") != 71:
        raise ParksGovernedLayerError("Expected source and extracted counts of 71")
    features = source.get("features") or []
    if len(features) != 71:
        raise ParksGovernedLayerError("Expected exactly 71 PARKS features")
    for flag in ("publication_approved", "canonical_identity_approved",
                 "authoritative_boundary_claimed"):
        if source.get(flag) is not False:
            raise ParksGovernedLayerError(f"Source {flag} must be false")
    counts = Counter()
    subtypes = set()
    for feature in features:
        geometry = feature.get("geometry") or {}
        props = feature.get("properties") or {}
        if geometry.get("type") != "Point":
            raise ParksGovernedLayerError("PARKS source geometries must remain Point")
        if props.get("target_layer") != LAYER_CODE:
            raise ParksGovernedLayerError("Feature target_layer does not match PARKS")
        if props.get("publication_approved") is not False:
            raise ParksGovernedLayerError("Feature publication_approved must be false")
        counts[props.get("source_layer")] += 1
        subtypes.add(props.get("source_subtype"))
    if dict(counts) != EXPECTED_LAYERS or subtypes != {"park", "national_park"}:
        raise ParksGovernedLayerError("PARKS source layers or subtypes mismatch")
    master_counts = {item["source_layer"]: item["feature_count"]
                     for item in master.get("layers", [])
                     if item.get("target_layer") == LAYER_CODE}
    if master_counts != EXPECTED_LAYERS:
        raise ParksGovernedLayerError("Master PARKS source inventory mismatch")


def cross_index():
    result = defaultdict(list)
    for layer_code, path in CROSS_LAYERS.items():
        for feature in load(path).get("features", []):
            geometry = feature.get("geometry") or {}
            if geometry.get("type") == "Point" and valid_wgs84(geometry):
                props = feature.get("properties") or {}
                result[point_key(geometry)].append({
                    "layer_code": layer_code,
                    "institutional_id": props.get("institutional_id"),
                    "feature_code": props.get("feature_code"),
                    "name_ar": props.get("name_ar"),
                })
    return result


def build():
    source, master = load(SOURCE_PATH), load(MASTER_PATH)
    validate_source(source, master)
    features = source["features"]
    prepared = []
    name_coords, identity_counts, coord_layers = defaultdict(set), Counter(), defaultdict(set)
    for feature in features:
        props = feature["properties"]
        name = extract_name(props.get("source_attributes") or {})
        normalized = normalize_name(name)
        coordinate = point_key(feature["geometry"])
        layer = props["source_layer"]
        if normalized:
            name_coords[normalized].add(coordinate)
            identity_counts[(normalized, coordinate)] += 1
        coord_layers[coordinate].add(layer)
        prepared.append((feature, name, normalized, coordinate))

    evidence = {"source": semantic_sha256(SOURCE_PATH),
                "master_registry": semantic_sha256(MASTER_PATH)}
    evidence.update({code.lower(): semantic_sha256(path)
                     for code, path in CROSS_LAYERS.items()})
    cross = cross_index()
    governed, blocked, cross_records = [], [], []
    generic_names = {"منتزه", "حديقة", "park", "national park"}

    for feature, name, normalized, coordinate in prepared:
        props = feature["properties"]
        geometry = feature["geometry"]
        source_id = str(props["source_feature_id"])
        source_layer = props["source_layer"]
        subtype = props["source_subtype"]
        matches = cross.get(coordinate, []) if valid_wgs84(geometry) else []
        classification = "SAFE_PARK_POINT"
        if not valid_wgs84(geometry):
            classification = "SOURCE_GEOMETRY_CRS_REVIEW"
        elif not normalized:
            classification = "SOURCE_IDENTITY_REVIEW"
        elif normalized in generic_names:
            classification = "GENERIC_NAME_IDENTITY_REVIEW"
        elif identity_counts[(normalized, coordinate)] > 1:
            classification = "EXACT_DUPLICATE_IDENTITY_REVIEW"
        elif len(coord_layers[coordinate]) > 1:
            classification = "SAME_COORDINATE_PARK_SOURCES_REVIEW"
        elif len(name_coords[normalized]) > 1:
            classification = "SAME_NAME_DIFFERENT_COORDINATES_REVIEW"
        elif matches:
            classification = "CROSS_LAYER_REFERENCE"

        metadata = {
            "artifact_status": STATUS, "review_classification": classification,
            "source_database": props.get("source_database"),
            "source_layer": source_layer, "source_subtype": subtype,
            "source_feature_id": source_id,
            "source_composite_id": props.get("source_composite_id"),
            "source_attributes": props.get("source_attributes") or {},
            "source_semantic_sha256": evidence["source"],
            "master_registry_semantic_sha256": evidence["master_registry"],
            "evidence_semantic_sha256": evidence,
            "publication_approved": False, "canonical_identity_approved": False,
            "authoritative_boundary_claimed": False,
            "cross_layer_authority_created": False,
        }
        institutional_id = f"atlas-park-{subtype}-{source_id}"
        record = {
            "institutional_id": institutional_id, "source_feature_id": source_id,
            "source_layer": source_layer, "park_subtype": subtype,
            "name_ar": name, "review_classification": classification,
            "geometry_type": "Point", "geometry": geometry,
            "source_metadata": metadata,
        }
        if matches:
            cross_records.append({
                "park_institutional_id": institutional_id,
                "park_source_layer": source_layer, "park_source_feature_id": source_id,
                "park_name_ar": name, "coordinate": list(coordinate),
                "relationship": "CROSS_LAYER_REFERENCE",
                "matches": matches, "publication_approved": False,
                "authoritative_boundary_claimed": False,
            })
        if classification == "SAFE_PARK_POINT":
            governed.append({
                "type": "Feature",
                "properties": {
                    "feature_code": f"park-{subtype}-{source_id}",
                    "institutional_id": institutional_id,
                    "source_feature_id": source_id, "name_ar": name,
                    "name_en": None, "category": "park", "park_subtype": subtype,
                    "review_classification": classification,
                    "source_identity": f"Libya ATLAS Project.gdb#{source_layer}-{source_id}",
                    "source_metadata": metadata,
                },
                "geometry": geometry,
            })
        else:
            record["blocked_reason"] = classification
            blocked.append(record)

    counts = Counter(["SAFE_PARK_POINT"] * len(governed))
    counts.update(item["review_classification"] for item in blocked)
    common = {
        "artifact_status": STATUS, "layer_code": LAYER_CODE,
        "publication_approved": False, "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "source_database": "Libya ATLAS Project.gdb", "source_feature_count": 71,
        "master_registry_version": "v2", "category_counts": dict(sorted(counts.items())),
        "evidence_semantic_sha256": evidence,
    }
    imported = {"type": "FeatureCollection", "name": "PARKS governed review import",
                **common, "features": governed}
    blocked_payload = {"schema_version": 1, "inventory_id": "parks-governed-blocked-v1",
                       **common, "safe_ingestible_feature_count": len(governed),
                       "blocked_feature_count": len(blocked), "records": blocked}
    cross_payload = {
        "schema_version": 1, "inventory_id": "parks-cross-layer-review-v1",
        "artifact_status": STATUS, "layer_code": LAYER_CODE,
        "publication_approved": False, "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "cross_layer_reference_count": len(cross_records),
        "coordinate_review_excluded_count": sum(
            item["review_classification"] == "SOURCE_GEOMETRY_CRS_REVIEW"
            for item in blocked
        ),
        "coordinate_review_excluded_records": [
            {
                "park_institutional_id": item["institutional_id"],
                "park_source_layer": item["source_layer"],
                "park_source_feature_id": item["source_feature_id"],
                "coordinate": item["geometry"]["coordinates"],
                "reason": "SOURCE_GEOMETRY_CRS_REVIEW",
            }
            for item in blocked
            if item["review_classification"] == "SOURCE_GEOMETRY_CRS_REVIEW"
        ],
        "comparison_layers": list(CROSS_LAYERS),
        "evidence_semantic_sha256": evidence, "records": cross_records,
    }
    return imported, blocked_payload, cross_payload


def validate():
    expected = build()
    for path, payload in zip((IMPORT_PATH, BLOCKED_PATH, CROSS_PATH), expected):
        if not path.is_file() or path.read_bytes() != canonical_bytes(payload):
            raise ParksGovernedLayerError(f"Artifact missing or stale: {path.name}")
    imported, blocked, cross = expected
    if len(imported["features"]) + len(blocked["records"]) != 71:
        raise ParksGovernedLayerError("PARKS accounting failed")
    codes = [f["properties"]["feature_code"] for f in imported["features"]]
    if len(codes) != len(set(codes)):
        raise ParksGovernedLayerError("Duplicate governed feature_code")
    return imported, blocked, cross


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        for path, payload in zip((IMPORT_PATH, BLOCKED_PATH, CROSS_PATH), build()):
            path.write_bytes(canonical_bytes(payload))
    imported, blocked, cross = validate()
    print("PARKS GOVERNED REVIEW ARTIFACTS VALID")
    print("SOURCE COUNT:", imported["source_feature_count"])
    print("SAFE INGESTIBLE:", len(imported["features"]))
    print("BLOCKED:", len(blocked["records"]))
    print("CROSS-LAYER REFERENCES:", cross["cross_layer_reference_count"])
    print("CATEGORY COUNTS:", json.dumps(imported["category_counts"], ensure_ascii=False,
                                         sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
