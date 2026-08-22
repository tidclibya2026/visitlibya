#!/usr/bin/env python3
"""Build and validate the review-only Ghadames source reconciliation."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = ROOT / "backend/data/gis/ghadames-source-reconciliation.review.json"
REGISTRY_PATH = ROOT / "backend/data/destinations/national-destination-registry.review.json"
INPUT_HASHES = {
    "ghadames-raw-inventory.json": "626069c4669575f5c123330f2caa8ff808af914f4e4437a0a10e105b98c4019e",
    "ghadames-source-comparison.json": "8aabcb31e2ead8d6ab24d1b1c59583d12ba5a7dc844fc0339455c65b5629812a",
    "ghadames-inspection-hashes.json": "057cf9ab97fd707812c86d0b297b85ff75b09d72b338090f4583fe63e777b6e2",
}
COLLECTIONS = (
    "buildings_context", "natural_context", "places_context", "access_roads",
    "landuse_context", "heritage_core_candidates", "visitor_services", "other_tourism_context",
)
LAYER_COLLECTION = {
    "buildings": "buildings_context", "natural": "natural_context", "places": "places_context",
    "roads": "access_roads", "select_landuse": "landuse_context",
}
HERITAGE_INTERSECTION_NAMES = {
    "مدينة غدامس القديمة", "ساحة الجامع العتيق", "الجامع العتيق", "ساحة جرسان", "مقهى توجدة",
}
VISITOR_SERVICE_NAMES = {
    "فندق عين الفرس‎", "فندق دار غدامس", "مكتب بريد واتصالات", "فندق القافلة", "فندق جوهرة الواحة‎‎‎",
    "بيوت الشباب", "سوق الصناعات التقليدية", "مصرف", "مطعم ومقهى أوال", "مستشفى غدامس العام", "حديقة ",
    "الساحة الرياضية", "مكتب السياحة غدامس", "فندق بن يدر‎‎", "سوق اللحوم", "سوق الخضروات", "سوق الثلاثاء",
    "الحديقة العامة", "مركز الشرطة", "مطعم بيروجينا", "مطعم بيروجينا 2", "فندق نجوم غدامس‎", "فندق باب الفتح",
    "محطة التزود بالوقود والمشتقات البترولية", "استراحة قصر الديوان", "استراحة ونزريك", "مخيم سياحي", "مصرف شمال أفريقيا",
}
FALSE_FIELDS = ("publication_approved", "canonical_approval", "public_visibility_enabled")
PROTECTED_PATHS = (
    "assets/js/data/natural-tourism-layers.js", "assets/js/data/curated-destinations.js",
    "backend/data/dev/destinations.json", "backend/data/governance",
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
)


class GhadamesReconciliationError(ValueError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _review_id(prefix: str, source_id: str, layer: str, ordered_attributes: list[dict], geometry: dict) -> str:
    digest = _sha256(_canonical({"source_id": source_id, "layer": layer, "ordered_attributes": ordered_attributes, "geometry": geometry}))[:24]
    return f"ghadames-{prefix}-{digest}"


def _valid_geometry(geometry_type: str, geometry: Any) -> bool:
    if not isinstance(geometry, dict):
        return False
    def finite_pair(pair: Any) -> bool:
        return isinstance(pair, list) and len(pair) >= 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in pair[:2])
    if geometry_type == "Point":
        return all(isinstance(geometry.get(key), (int, float)) and not isinstance(geometry.get(key), bool) and math.isfinite(geometry[key]) for key in ("x", "y"))
    key = "paths" if geometry_type == "Polyline" else "rings" if geometry_type == "Polygon" else None
    return bool(key and isinstance(geometry.get(key), list) and geometry[key] and all(isinstance(part, list) and len(part) >= 2 and all(finite_pair(pair) for pair in part) for part in geometry[key]))


def _governed_record(source_id: str, layer: dict, source_row: dict, collection: str) -> dict:
    attribute_field_names = [field["name"] for field in layer["fields"] if field["type"] not in {"OID", "Geometry", "Blob", "Raster"}]
    ordered_attributes = [{"field": name, "value": source_row["attributes"].get(name)} for name in attribute_field_names]
    geometry = source_row["geometry"]
    return {
        "review_id": _review_id("record", source_id, layer["relative_path"], ordered_attributes, geometry),
        "review_collection": collection,
        "source_reference": {"source_id": source_id, "database_basename": "gadamas.gdb", "relative_layer": layer["relative_path"], "source_row_ordinal": source_row["source_row_ordinal"]},
        "source_attribute_schema_order": attribute_field_names,
        "source_attributes_ordered": ordered_attributes,
        "source_attributes": source_row["attributes"],
        "source_geometry": geometry,
        "geometry_type": layer["geometry_type"],
        "wkid": 4326,
        "source_content_origin": "OSM_DERIVED_WHERE_OSM_ID_PRESENT_IN_INSTITUTIONALLY_HELD_GEODATABASE",
        "institutional_authorship_of_osm_content_claimed": False,
        "destination_membership_status": "UNRESOLVED_REVIEW_ROUTING_ONLY",
        "archaeological_classification_status": "UNRESOLVED",
        "publication_approved": False,
        "canonical_approval": False,
        "public_visibility_enabled": False,
        "institutional_review_status": "UNRESOLVED",
    }


def _point_collection(name: Any) -> str:
    if name in HERITAGE_INTERSECTION_NAMES:
        return "heritage_core_candidates"
    if name in VISITOR_SERVICE_NAMES:
        return "visitor_services"
    return "other_tourism_context"


def build_artifact(input_directory: Path) -> dict:
    raw_bytes = {}
    for basename, expected_hash in INPUT_HASHES.items():
        content = (input_directory / basename).read_bytes()
        if _sha256(content) != expected_hash:
            raise GhadamesReconciliationError(f"inspection hash mismatch: {basename}")
        raw_bytes[basename] = content
    raw = json.loads(raw_bytes["ghadames-raw-inventory.json"])
    comparison = json.loads(raw_bytes["ghadames-source-comparison.json"])
    hashes = json.loads(raw_bytes["ghadames-inspection-hashes.json"])
    sources = {item["source_id"]: item for item in raw["sources"]}
    primary = sources["gadamas_flash16"]
    collections = {name: [] for name in COLLECTIONS}
    layer_registry = []
    for layer in primary["feature_classes"]:
        collection = LAYER_COLLECTION.get(layer["relative_path"])
        if layer["relative_path"] == "select_point":
            collection = None
        layer_registry.append({
            "relative_layer": layer["relative_path"], "geometry_type": layer["geometry_type"], "record_count": layer["record_count"],
            "wkid": layer["spatial_reference"]["wkid"], "spatial_reference_name": layer["spatial_reference"]["name"],
            "extent": layer["extent"], "has_z": layer["has_z"], "has_m": layer["has_m"], "ordered_field_schema": layer["fields"],
        })
        for source_row in layer["records"]:
            target = _point_collection(source_row["attributes"].get("Name")) if layer["relative_path"] == "select_point" else collection
            collections[target].append(_governed_record("gadamas_flash16", layer, source_row, target))
    quarantined = []
    boundary_registry = {item["source_id"]: item for item in raw["boundaries"]}
    for boundary_id in ("old_city", "zone", "third_zone"):
        boundary = boundary_registry[boundary_id]
        layer = boundary["layer"]
        source_row = layer["records"][0]
        attribute_fields = [field["name"] for field in layer["fields"] if field["type"] not in {"OID", "Geometry", "Blob", "Raster"}]
        ordered = [{"field": name, "value": source_row["attributes"].get(name)} for name in attribute_fields]
        record = {
            "review_id": _review_id("boundary", boundary_id, layer["relative_path"], ordered, source_row["geometry"]),
            "source_reference": {"source_id": boundary_id, "artifact_basename": layer["relative_path"]},
            "source_attribute_schema_order": attribute_fields, "source_attributes_ordered": ordered,
            "source_attributes": source_row["attributes"], "source_geometry": source_row["geometry"],
            "geometry_type": "Polygon", "wkid": 4326,
            "semantic_status": "UNRESOLVED_SOURCE_POLYGON_EVIDENCE",
            "plausible_identity_evidence": "OLD_CITY_GHADAMES" if boundary_id == "old_city" else None,
            "canonical_boundary_approval": False, "unesco_boundary_approval": False, "unesco_buffer_zone_approval": False,
            "publication_approved": False, "canonical_approval": False, "public_visibility_enabled": False,
            "institutional_review_status": "UNRESOLVED",
        }
        quarantined.append({"quarantine_reason": "UNRESOLVED_BOUNDARY_SEMANTICS", "record": record})
    all_clean = [item for name in COLLECTIONS for item in collections[name]]
    spatial_ids = [item["review_id"] for item in collections["heritage_core_candidates"]]
    component_hashes = hashes["source_shapefile_components"]
    return {
        "schema_version": 1,
        "reconciliation_id": "ghadames-source-reconciliation-v1",
        "status": "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE",
        "registry_record_id": "ndr-ghadames",
        "identity_architecture": {
            "broader_destination_slug": "ghadames", "heritage_core_slug": "old-city-ghadames",
            "relationship": "CONTAINS_HERITAGE_CORE", "identities_merged": False,
            "old_city_coordinate_inherited_by_broader_destination": False,
            "old_city_boundary_inherited_by_broader_destination": False,
            "records_duplicated_for_containment": False,
            "separate_evidence_and_publication_requirements": True,
        },
        "inspection_provenance": {
            "institutional_source_label": "INSTITUTIONALLY_HELD_ARCGIS_SOURCE_INSPECTION",
            "extraction_date": "2026-08-22", "absolute_source_paths_recorded": False,
            "input_hashes": [{"basename": name, "sha256": digest} for name, digest in INPUT_HASHES.items()],
            "source_shapefile_component_hashes": component_hashes,
        },
        "source_copy_assessment": {
            "assessed_source_ids": ["gadamas_flash16", "gadamas_flash16_cloud", "gadamas_flash8_cloud"],
            "database_basename": "gadamas.gdb", "primary_source_id": "gadamas_flash16",
            "physical_equality": "ALL_THREE_BYTE_IDENTICAL", "logical_equality": "ALL_THREE_LOGICALLY_IDENTICAL",
            "primary_record_count": 770, "excluded_duplicate_copy_count": 2,
            "excluded_redundant_record_copy_count": 1540, "unique_records_lost": 0,
            "conflicting_schema_count": 0, "conflicting_geometry_count": 0, "unique_complementary_record_count": 0,
            "physical_directory_sha256": comparison["source_summaries"][0]["physical_directory_sha256"],
        },
        "layer_registry": layer_registry,
        "collections": collections,
        "spatial_review_evidence": {
            "relationship": "POINT_GEOMETRICALLY_INTERSECTS_UNRESOLVED_OLD_CITY_SOURCE_POLYGON",
            "member_review_ids": spatial_ids,
            "source_names": sorted(HERITAGE_INTERSECTION_NAMES),
            "grants_canonical_membership": False, "grants_archaeological_classification": False,
            "grants_unesco_membership": False, "grants_boundary_authority": False, "grants_publication_eligibility": False,
        },
        "quarantined_records": quarantined,
        "false_positive_protection": {
            "excluded_name": "فندق الغدامسية", "known_other_destination": "tripoli",
            "present_in_reconciliation": False, "name_similarity_establishes_membership": False,
        },
        "summary": {
            "database_source_copy_record_count": 2310, "excluded_duplicate_copy_record_count": 1540,
            "unique_primary_database_record_count": 770, "boundary_evidence_record_count": 3,
            "represented_evidence_record_count": 773,
            "clean_counts_by_collection": {name: len(collections[name]) for name in COLLECTIONS},
            "clean_record_count": len(all_clean), "quarantined_record_count": len(quarantined),
            "quarantine_reason_counts": {"UNRESOLVED_BOUNDARY_SEMANTICS": 3},
            "publication_or_registry_gis_count_added": 0,
        },
        "governance": {
            "review_only": True, "runtime_source": False, "authoritative_boundary_present": False,
            "publication_approved": False, "canonical_approval": False, "public_visibility_enabled": False,
            "institutional_review_status": "UNRESOLVED", "approval_event_reference": None,
        },
    }


def validate_artifact(artifact: dict, root: Path = ROOT, check_git: bool = True) -> dict:
    errors = []
    def check(condition: bool, message: str) -> None:
        if not condition: errors.append(message)
    check(artifact.get("schema_version") == 1, "schema version mismatch")
    check(artifact.get("status") == "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE", "artifact is not review-only")
    check(artifact.get("registry_record_id") == "ndr-ghadames", "registry linkage mismatch")
    provenance = artifact.get("inspection_provenance", {})
    check({item.get("basename"): item.get("sha256") for item in provenance.get("input_hashes", [])} == INPUT_HASHES, "inspection hashes mismatch")
    check(provenance.get("absolute_source_paths_recorded") is False, "absolute source path policy mismatch")
    source = artifact.get("source_copy_assessment", {})
    check(source.get("primary_record_count") == 770 and source.get("excluded_redundant_record_copy_count") == 1540, "source-copy accounting mismatch")
    check(source.get("excluded_duplicate_copy_count") == 2 and source.get("unique_records_lost") == 0, "duplicate-copy decision mismatch")
    check(source.get("physical_equality") == "ALL_THREE_BYTE_IDENTICAL" and source.get("logical_equality") == "ALL_THREE_LOGICALLY_IDENTICAL", "source equality mismatch")
    expected_layers = {"buildings": 81, "natural": 15, "places": 4, "roads": 599, "select_landuse": 20, "select_point": 51}
    layers = artifact.get("layer_registry", [])
    check({item.get("relative_layer"): item.get("record_count") for item in layers} == expected_layers, "layer counts mismatch")
    check(all(item.get("wkid") == 4326 and isinstance(item.get("has_z"), bool) and isinstance(item.get("has_m"), bool) for item in layers), "layer spatial metadata mismatch")
    check(next((item for item in layers if item.get("relative_layer") == "select_point"), {}).get("has_z") is True and next((item for item in layers if item.get("relative_layer") == "select_point"), {}).get("has_m") is True, "select_point Z/M state mismatch")
    collections = artifact.get("collections", {})
    check(list(collections) == list(COLLECTIONS), "collection order mismatch")
    clean = [record for name in COLLECTIONS for record in collections.get(name, [])]
    quarantine_items = artifact.get("quarantined_records", [])
    quarantine = [item.get("record", {}) for item in quarantine_items]
    check(len(clean) == 770 and len(quarantine) == 3, "represented count mismatch")
    clean_ids = [item.get("review_id") for item in clean]
    quarantine_ids = [item.get("review_id") for item in quarantine]
    check(len(clean_ids) == len(set(clean_ids)) and len(quarantine_ids) == len(set(quarantine_ids)), "duplicate review ID")
    check(set(clean_ids).isdisjoint(quarantine_ids), "clean and quarantine overlap")
    for record in clean:
        expected = _review_id("record", record.get("source_reference", {}).get("source_id"), record.get("source_reference", {}).get("relative_layer"), record.get("source_attributes_ordered"), record.get("source_geometry"))
        check(record.get("review_id") == expected, "deterministic clean review ID mismatch")
        check(record.get("source_attribute_schema_order") == [item.get("field") for item in record.get("source_attributes_ordered", [])], "ordered attributes mismatch")
        check(_valid_geometry(record.get("geometry_type"), record.get("source_geometry")) and record.get("wkid") == 4326, "invalid clean geometry")
        for field in FALSE_FIELDS: check(record.get(field) is False, f"record grants {field}")
        check(record.get("institutional_review_status") == "UNRESOLVED", "record review resolved without authority")
    check(len({(item.get("source_reference", {}).get("relative_layer"), item.get("source_reference", {}).get("source_row_ordinal")) for item in clean}) == 770, "source records are missing or duplicated")
    for item in quarantine_items:
        record = item.get("record", {})
        expected = _review_id("boundary", record.get("source_reference", {}).get("source_id"), record.get("source_reference", {}).get("artifact_basename"), record.get("source_attributes_ordered"), record.get("source_geometry"))
        check(item.get("quarantine_reason") == "UNRESOLVED_BOUNDARY_SEMANTICS" and record.get("review_id") == expected, "boundary quarantine mismatch")
        check(_valid_geometry("Polygon", record.get("source_geometry")) and record.get("wkid") == 4326, "invalid boundary evidence")
        for field in (*FALSE_FIELDS, "canonical_boundary_approval", "unesco_boundary_approval", "unesco_buffer_zone_approval"):
            check(record.get(field) is False, f"boundary grants {field}")
        check(record.get("semantic_status") == "UNRESOLVED_SOURCE_POLYGON_EVIDENCE" and record.get("institutional_review_status") == "UNRESOLVED", "boundary semantics overclaimed")
    identity = artifact.get("identity_architecture", {})
    check(identity == {"broader_destination_slug": "ghadames", "heritage_core_slug": "old-city-ghadames", "relationship": "CONTAINS_HERITAGE_CORE", "identities_merged": False, "old_city_coordinate_inherited_by_broader_destination": False, "old_city_boundary_inherited_by_broader_destination": False, "records_duplicated_for_containment": False, "separate_evidence_and_publication_requirements": True}, "identity architecture mismatch")
    spatial = artifact.get("spatial_review_evidence", {})
    check(set(spatial.get("source_names", [])) == HERITAGE_INTERSECTION_NAMES and len(spatial.get("member_review_ids", [])) == 5, "spatial intersection evidence mismatch")
    check(set(spatial.get("member_review_ids", [])) == set(item.get("review_id") for item in collections.get("heritage_core_candidates", [])), "spatial member linkage mismatch")
    check(all(spatial.get(field) is False for field in ("grants_canonical_membership", "grants_archaeological_classification", "grants_unesco_membership", "grants_boundary_authority", "grants_publication_eligibility")), "spatial evidence grants authority")
    serialized = json.dumps(artifact, ensure_ascii=False)
    check("فندق الغدامسية" not in serialized.replace(json.dumps(artifact.get("false_positive_protection", {}), ensure_ascii=False), ""), "Tripoli false-positive record entered reconciliation")
    check(artifact.get("false_positive_protection", {}).get("known_other_destination") == "tripoli" and artifact.get("false_positive_protection", {}).get("present_in_reconciliation") is False, "false-positive protection mismatch")
    summary = artifact.get("summary", {})
    computed = {name: len(collections.get(name, [])) for name in COLLECTIONS}
    check(summary.get("clean_counts_by_collection") == computed and sum(computed.values()) == 770, "collection totals mismatch")
    check(summary.get("represented_evidence_record_count") == 773 and summary.get("quarantined_record_count") == 3, "summary accounting mismatch")
    check(summary.get("publication_or_registry_gis_count_added") == 0, "review evidence inflates publication GIS count")
    governance = artifact.get("governance", {})
    for field in FALSE_FIELDS: check(governance.get(field) is False, f"artifact grants {field}")
    check(governance.get("runtime_source") is False and governance.get("authoritative_boundary_present") is False, "artifact claims runtime or boundary authority")
    registry = json.loads((root / REGISTRY_PATH.relative_to(ROOT)).read_text(encoding="utf-8"))
    check(sum(item.get("gis_record_count", 0) for item in registry.get("records", [])) == 214, "registry GIS count changed")
    ghadames = next((item for item in registry.get("records", []) if item.get("registry_record_id") == "ndr-ghadames"), {})
    check(ghadames.get("gis_source_reconciliation_present") is True and ghadames.get("gis_source_reconciliation_path") == "backend/data/gis/ghadames-source-reconciliation.review.json", "registry reconciliation reference mismatch")
    check(ghadames.get("gis_layer_present") is False and ghadames.get("gis_record_count") == 0 and ghadames.get("coordinates_present") is False, "registry promotes Ghadames review evidence")
    if check_git:
        result = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", *PROTECTED_PATHS], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        check(not result.stdout.strip(), f"protected artifacts changed: {result.stdout.strip()}")
    if errors: raise GhadamesReconciliationError("\n".join(errors))
    return {"clean_records": 770, "quarantined_records": 3, "represented_evidence": 773, "duplicate_copies_excluded": 1540}


def validate_serialization(path: Path = ARTIFACT_PATH) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r\n" in raw:
        raise GhadamesReconciliationError("artifact must be UTF-8 without BOM, LF, and exactly one final newline")
    if b"C:\\\\" in raw or b"visitlibya-local-backups" in raw:
        raise GhadamesReconciliationError("artifact contains an absolute local path")


def main() -> int:
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "build":
            artifact = build_artifact(Path(sys.argv[2]))
            ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        elif len(sys.argv) != 1:
            raise GhadamesReconciliationError("usage: ghadames_source_reconciliation.py [build INSPECTION_DIRECTORY]")
        validate_serialization()
        result = validate_artifact(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError, GhadamesReconciliationError) as exc:
        print(f"Ghadames source reconciliation failed:\n{exc}", file=sys.stderr)
        return 1
    print("Ghadames source reconciliation passed: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
