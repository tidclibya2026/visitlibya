#!/usr/bin/env python3
"""Build and validate the review-only Cyrene/Shahat source reconciliation."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = ROOT / "backend/data/gis/cyrene-source-reconciliation.review.json"
REGISTRY_PATH = ROOT / "backend/data/destinations/national-destination-registry.review.json"
MANIFEST_BASENAME = "cyrene-source-export-manifest.json"
MANIFEST_SHA256 = "7dcb32021236dfde82040f463433ce5b0cd695dee941988bd5cd94d0e74fb361"
COLLECTIONS = (
    "heritage_points",
    "heritage_polygons",
    "natural_context_points",
    "visitor_services_points",
    "access_roads",
    "buildings_context",
)
GOVERNANCE_FALSE_FIELDS = ("publication_approved", "canonical_approval", "public_visibility_enabled")
EXACT_DUPLICATES = (
    ("roads", "cyrene_shahhat__003.esri.json", "qurina_cy__004.esri.json", 1376),
    ("buildings", "cyrene_shahhat__005.esri.json", "qurina_cy__006.esri.json", 38),
    ("schools", "cyrene_shahhat__007.esri.json", "qurina_cy__008.esri.json", 11),
    ("mosques", "cyrene_shahhat__009.esri.json", "qurina_cy__009.esri.json", 11),
    ("lodges", "cyrene_shahhat__018.esri.json", "qurina_cy__013.esri.json", 2),
)
LAYER_COLLECTION = {
    "cyrene_shahhat__001.esri.json": "buildings_context",
    "cyrene_shahhat__002.esri.json": "buildings_context",
    "cyrene_shahhat__003.esri.json": "access_roads",
    "cyrene_shahhat__004.esri.json": "natural_context_points",
    "cyrene_shahhat__005.esri.json": "buildings_context",
    "cyrene_shahhat__006.esri.json": "visitor_services_points",
    "cyrene_shahhat__007.esri.json": "visitor_services_points",
    "cyrene_shahhat__008.esri.json": "visitor_services_points",
    "cyrene_shahhat__009.esri.json": "visitor_services_points",
    "cyrene_shahhat__010.esri.json": "visitor_services_points",
    "cyrene_shahhat__011.esri.json": "visitor_services_points",
    "cyrene_shahhat__012.esri.json": "visitor_services_points",
    "cyrene_shahhat__013.esri.json": "heritage_points",
    "cyrene_shahhat__014.esri.json": "heritage_polygons",
    "cyrene_shahhat__015.esri.json": "visitor_services_points",
    "cyrene_shahhat__016.esri.json": "visitor_services_points",
    "cyrene_shahhat__017.esri.json": "heritage_points",
    "cyrene_shahhat__018.esri.json": "visitor_services_points",
    "qurina_cy__001.esri.json": "heritage_points",
    "qurina_cy__002.esri.json": "visitor_services_points",
    "qurina_cy__003.esri.json": "visitor_services_points",
    "qurina_cy__005.esri.json": "visitor_services_points",
    "qurina_cy__007.esri.json": "visitor_services_points",
    "qurina_cy__010.esri.json": "visitor_services_points",
    "qurina_cy__011.esri.json": "visitor_services_points",
    "qurina_cy__012.esri.json": "visitor_services_points",
    "points_world_heritage__001.esri.json": "visitor_services_points",
}
PROTECTED_PATHS = (
    "assets/js/data/natural-tourism-layers.js",
    "assets/js/data/curated-destinations.js",
    "backend/data/dev/destinations.json",
    "backend/data/governance",
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
)


class CyreneReconciliationError(ValueError):
    """Raised when source evidence or the reconciliation contract is invalid."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _valid_geometry(geometry_type: str, geometry: Any) -> bool:
    if not isinstance(geometry, dict):
        return False
    if geometry_type == "esriGeometryPoint":
        return _finite(geometry.get("x")) and _finite(geometry.get("y"))
    coordinate_key = "paths" if geometry_type == "esriGeometryPolyline" else "rings"
    groups = geometry.get(coordinate_key)
    return isinstance(groups, list) and bool(groups) and all(
        isinstance(group, list) and bool(group) and all(
            isinstance(pair, list) and len(pair) >= 2 and _finite(pair[0]) and _finite(pair[1]) for pair in group
        ) for group in groups
    )


def _source_ref(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": entry["source_id"],
        "source_database": entry["source_database"],
        "relative_layer": entry["relative_layer"],
        "export_file": entry["export_file"],
        "sha256": entry["sha256"],
    }


def _name(attributes: dict[str, Any]) -> Any:
    for key in ("Name", "name", "ar_name"):
        if key in attributes:
            return attributes[key]
    return None


def _record_id(collection: str, refs: list[dict[str, Any]], attributes: dict[str, Any], geometry: Any, derived: Any) -> str:
    identity = {
        "collection": collection,
        "source_identity": [{"source_id": ref["source_id"], "relative_layer": ref["relative_layer"]} for ref in refs],
        "source_attributes": attributes,
        "source_geometry": geometry,
        "derived_review_geometry": derived,
    }
    return "cyrene-review-" + _sha256(_canonical(identity))[:24]


def _governed_record(collection: str, refs: list[dict[str, Any]], feature: dict[str, Any], flags: list[str] | None = None, derived: Any = None) -> dict[str, Any]:
    attributes = feature.get("attributes", {})
    geometry = feature.get("geometry")
    return {
        "review_id": _record_id(collection, refs, attributes, geometry, derived),
        "review_collection": collection,
        "source_references": refs,
        "source_attributes": attributes,
        "source_geometry": geometry,
        "source_name": _name(attributes),
        "proposed_normalized_name": None,
        "proposed_identity_evidence": None,
        "derived_review_geometry": derived,
        "quality_flags": sorted(set(flags or [])),
        "destination_membership_status": "UNRESOLVED",
        "archaeological_interpretation_status": "UNRESOLVED",
        "authoritative_boundary": False,
        "media_rights_verified": False,
        "publication_approved": False,
        "canonical_approval": False,
        "public_visibility_enabled": False,
        "institutional_review_status": "UNRESOLVED",
        "resolution_status": "UNRESOLVED",
    }


def _distance_m(a: dict[str, Any], b: dict[str, Any]) -> float:
    lat1, lat2 = a["y"], b["y"]
    lat = math.radians((lat1 + lat2) / 2)
    dx = (a["x"] - b["x"]) * 111320 * math.cos(lat)
    dy = (a["y"] - b["y"]) * 110540
    return math.hypot(dx, dy)


def _nearest_groups(kind: str, left: list[dict[str, Any]], right: list[dict[str, Any]], maximum_m: float) -> list[dict[str, Any]]:
    candidates: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    for a in left:
        for b in right:
            distance = _distance_m(a["source_geometry"], b["source_geometry"])
            if distance <= maximum_m:
                candidates.append((distance, a, b))
    used_left: set[str] = set()
    used_right: set[str] = set()
    groups: list[dict[str, Any]] = []
    for distance, a, b in sorted(candidates, key=lambda item: (item[0], item[1]["review_id"], item[2]["review_id"])):
        if a["review_id"] in used_left or b["review_id"] in used_right:
            continue
        used_left.add(a["review_id"])
        used_right.add(b["review_id"])
        groups.append({
            "group_id": f"identity-candidate-{kind}-{len(groups) + 1:02d}",
            "candidate_type": kind,
            "member_review_ids": [a["review_id"], b["review_id"]],
            "distance_m": round(distance, 3),
            "decision": "REVIEW_REQUIRED_NO_CONSOLIDATION",
            "basis": "Spatial proximity suggests possible correspondence but is not identity proof.",
        })
    return groups


def load_source_bundle(source_dir: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, bytes]]:
    manifest_path = source_dir / MANIFEST_BASENAME
    manifest_raw = manifest_path.read_bytes()
    if _sha256(manifest_raw) != MANIFEST_SHA256:
        raise CyreneReconciliationError("manifest hash mismatch")
    manifest = json.loads(manifest_raw.decode("utf-8-sig"))
    if manifest.get("errors") != [] or manifest.get("inspection_only") is not True or manifest.get("mutation_performed_on_sources") is not False:
        raise CyreneReconciliationError("manifest must contain zero errors and remain inspection-only")
    exports = manifest.get("exports", [])
    if len(exports) != 32:
        raise CyreneReconciliationError("manifest must contain exactly 32 exports")
    documents: dict[str, dict[str, Any]] = {}
    raw_files: dict[str, bytes] = {}
    for entry in exports:
        name = entry["export_file"]
        raw = (source_dir / name).read_bytes()
        if _sha256(raw) != entry["sha256"]:
            raise CyreneReconciliationError(f"source hash mismatch: {name}")
        document = json.loads(raw.decode("utf-8-sig"))
        if len(document.get("features", [])) != entry["record_count"]:
            raise CyreneReconciliationError(f"source record count mismatch: {name}")
        if document.get("geometryType") != f"esriGeometry{entry['shape_type']}":
            raise CyreneReconciliationError(f"source geometry type mismatch: {name}")
        documents[name] = document
        raw_files[name] = raw
    return manifest, documents, raw_files


def build_artifact(source_dir: Path) -> dict[str, Any]:
    manifest, documents, raw_files = load_source_bundle(source_dir)
    entries = {entry["export_file"]: entry for entry in manifest["exports"]}
    duplicate_secondary = {secondary for _, _, secondary, _ in EXACT_DUPLICATES}
    duplicate_primary = {primary: secondary for _, primary, secondary, _ in EXACT_DUPLICATES}
    exact_decisions: list[dict[str, Any]] = []
    for logical, primary, secondary, count in EXACT_DUPLICATES:
        if raw_files[primary] != raw_files[secondary] or entries[primary]["sha256"] != entries[secondary]["sha256"]:
            raise CyreneReconciliationError(f"exact duplicate verification failed: {logical}")
        exact_decisions.append({
            "logical_layer": logical,
            "record_count": count,
            "sha256": entries[primary]["sha256"],
            "consolidation_decision": "EXACT_BYTE_IDENTICAL_SINGLE_REPRESENTATION",
            "records_removed_from_clean_count": count,
            "source_references": [_source_ref(entries[primary]), _source_ref(entries[secondary])],
        })

    collections: dict[str, list[dict[str, Any]]] = {name: [] for name in COLLECTIONS}
    quarantine: list[dict[str, Any]] = []
    geometry_conflicts: list[dict[str, Any]] = []
    records_by_export: dict[str, list[dict[str, Any]]] = {}

    for entry in manifest["exports"]:
        export_file = entry["export_file"]
        if export_file in duplicate_secondary:
            continue
        document = documents[export_file]
        collection = LAYER_COLLECTION[export_file]
        refs = [_source_ref(entry)]
        if export_file in duplicate_primary:
            refs.append(_source_ref(entries[duplicate_primary[export_file]]))
        records_by_export[export_file] = []
        for feature in document["features"]:
            flags: list[str] = []
            derived = None
            proposed_identity_evidence = None
            resolution_status = "UNRESOLVED"
            valid = _valid_geometry(document["geometryType"], feature.get("geometry"))
            name = str(_name(feature.get("attributes", {})) or "").strip()
            if export_file == "qurina_cy__001.esri.json":
                attributes = feature.get("attributes", {})
                if not (_finite(attributes.get("x")) and _finite(attributes.get("y"))):
                    valid = False
                else:
                    derived = {"method": "SOURCE_ATTRIBUTE_XY", "longitude": attributes["x"], "latitude": attributes["y"], "wkid": 4326}
                    flags.append("CRS_METADATA_GEOMETRY_CONFLICT")
                    geometry_conflicts.append({
                        "conflict_id": f"crs-conflict-qurina-archaeology-{len(geometry_conflicts) + 1:02d}",
                        "source_reference": _source_ref(entry),
                        "source_name": name,
                        "source_crs": entry["spatial_reference"],
                        "exported_json_spatial_reference": document.get("spatialReference"),
                        "preserved_source_geometry": feature.get("geometry"),
                        "derived_review_geometry": derived,
                        "quality_flag": "CRS_METADATA_GEOMETRY_CONFLICT",
                        "resolution_status": "UNRESOLVED",
                    })
            if export_file == "cyrene_shahhat__017.esri.json" and name in {"متحف المنحوتاث", "نبع ابوللو", "الحمامات الاغريقية"}:
                flags.append("SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT")
                world_entry = entries["points_world_heritage__001.esri.json"]
                world_match = next(
                    candidate for candidate in documents["points_world_heritage__001.esri.json"]["features"]
                    if candidate.get("geometry") == feature.get("geometry")
                )
                proposed_identity_evidence = {
                    "source_reference": _source_ref(world_entry),
                    "source_name": _name(world_match.get("attributes", {})),
                    "source_geometry": world_match.get("geometry"),
                    "canonical_approval": False,
                    "publication_approved": False,
                }
                resolution_status = "UNRESOLVED_NO_AUTOMATIC_REPAIR"
                geometry_conflicts.append({
                    "conflict_id": f"attribute-geometry-misalignment-{len(geometry_conflicts) + 1:02d}",
                    "source_reference": _source_ref(entry),
                    "source_name": name,
                    "preserved_source_geometry": feature.get("geometry"),
                    "quality_flag": "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT",
                    "proposed_identity_evidence": proposed_identity_evidence,
                    "resolution_status": "UNRESOLVED_NO_AUTOMATIC_REPAIR",
                })
            if export_file == "cyrene_shahhat__017.esri.json" and name in {"غابة شحات", "شلال شحات"}:
                collection = "natural_context_points"
            elif export_file == "cyrene_shahhat__017.esri.json" and name == "متحف شحات":
                collection = "visitor_services_points"
            elif export_file == "points_world_heritage__001.esri.json":
                no = feature.get("attributes", {}).get("no")
                collection = "heritage_points" if isinstance(no, int) and no <= 9 else "visitor_services_points"
                if no == 10:
                    collection = "natural_context_points"
            record = _governed_record(collection, refs, feature, flags, derived)
            record["proposed_identity_evidence"] = proposed_identity_evidence
            record["resolution_status"] = resolution_status
            if not valid:
                record["quality_flags"] = sorted(set(record["quality_flags"] + ["INVALID_GEOMETRY_QUARANTINED"]))
                quarantine.append({"quarantine_reason": "INVALID_GEOMETRY", "record": record})
                records_by_export[export_file].append(record)
                continue
            if "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT" in record["quality_flags"]:
                quarantine.append({"quarantine_reason": "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT", "record": record})
                records_by_export[export_file].append(record)
                continue
            if export_file == "points_world_heritage__001.esri.json" and name == "كافي الشلال شحات":
                record["quality_flags"] = sorted(set(record["quality_flags"] + ["SPATIAL_OUTLIER"]))
                quarantine.append({"quarantine_reason": "SPATIAL_OUTLIER", "record": record})
                records_by_export[export_file].append(record)
                continue
            collections[collection].append(record)
            records_by_export[export_file].append(record)

    all_clean = [item for name in COLLECTIONS for item in collections[name]]
    by_source = lambda source_id: [item for item in all_clean if item["source_references"][0]["source_id"] == source_id]
    source_records = {source: by_source(source) for source in ("cyrene_shahhat", "qurina_cy", "points_world_heritage")}
    fuel_left = [item for item in source_records["cyrene_shahhat"] if item["source_references"][0]["export_file"] == "cyrene_shahhat__006.esri.json"]
    fuel_right = [item for item in source_records["qurina_cy"] if item["source_references"][0]["export_file"] == "qurina_cy__007.esri.json"]
    bank_left = [item for item in source_records["cyrene_shahhat"] if item["source_references"][0]["export_file"] == "cyrene_shahhat__010.esri.json"]
    bank_right = [item for item in source_records["qurina_cy"] if item["source_references"][0]["export_file"] == "qurina_cy__010.esri.json"]
    identity_groups = _nearest_groups("FUEL_NEAR_PAIR", fuel_left, fuel_right, 25.0)
    identity_groups += _nearest_groups("BANK_NEAR_PAIR", bank_left, bank_right, 25.0)
    paired_bank_ids = {record_id for group in identity_groups if group["candidate_type"] == "BANK_NEAR_PAIR" for record_id in group["member_review_ids"]}
    unique_banks = [item["review_id"] for item in bank_right if item["review_id"] not in paired_bank_ids]
    identity_groups.append({
        "group_id": "identity-candidate-bank-unique-qurina",
        "candidate_type": "BANK_UNPAIRED_SOURCE_RECORD",
        "member_review_ids": unique_banks,
        "distance_m": None,
        "decision": "PRESERVE_AS_UNIQUE_REVIEW_RECORD",
        "basis": "No near corresponding bank was found in the primary source; identity remains unresolved.",
    })
    for kind, files in (
        ("RESTAURANT_UNION_REVIEW", {"cyrene_shahhat__012.esri.json", "qurina_cy__011.esri.json"}),
        ("CAFE_DISTINCT_REVIEW", {"cyrene_shahhat__015.esri.json", "qurina_cy__012.esri.json"}),
        ("HERITAGE_CROSS_SOURCE_REVIEW", {"cyrene_shahhat__013.esri.json", "cyrene_shahhat__017.esri.json", "qurina_cy__001.esri.json", "points_world_heritage__001.esri.json"}),
    ):
        members = [item["review_id"] for item in all_clean if item["source_references"][0]["export_file"] in files]
        identity_groups.append({
            "group_id": f"identity-candidate-{kind.lower().replace('_', '-')}",
            "candidate_type": kind,
            "member_review_ids": members,
            "distance_m": None,
            "decision": "PRESERVE_UNION_NO_AUTOMATIC_CONSOLIDATION",
            "basis": "Names and proximity are candidate-review evidence only; source records remain distinct.",
        })

    clean_by_id = {item["review_id"]: item for item in all_clean}
    heritage_group = next(item for item in identity_groups if item["candidate_type"] == "HERITAGE_CROSS_SOURCE_REVIEW")
    heritage_group["membership_policy"] = "CLEAN_RECORDS_ONLY_QUARANTINED_EVIDENCE_REFERENCED_THROUGH_CONFLICTS"
    heritage_group["included_collections"] = sorted({clean_by_id[review_id]["review_collection"] for review_id in heritage_group["member_review_ids"]})
    heritage_group["member_cross_tab"] = [
        {
            "review_id": review_id,
            "source_id": clean_by_id[review_id]["source_references"][0]["source_id"],
            "relative_layer": clean_by_id[review_id]["source_references"][0]["relative_layer"],
            "review_collection": clean_by_id[review_id]["review_collection"],
            "state": "CLEAN",
            "quality_flags": clean_by_id[review_id]["quality_flags"],
        }
        for review_id in heritage_group["member_review_ids"]
    ]

    source_registry = []
    for entry in manifest["exports"]:
        document = documents[entry["export_file"]]
        source_registry.append({
            "source_id": entry["source_id"],
            "source_database": entry["source_database"],
            "relative_layer": entry["relative_layer"],
            "export_file": entry["export_file"],
            "sha256": entry["sha256"],
            "record_count": entry["record_count"],
            "geometry_type": document["geometryType"],
            "source_crs": entry["spatial_reference"],
            "exported_json_spatial_reference": document.get("spatialReference"),
            "extraction_date": "2026-08-22",
            "verification_status": "HASH_COUNT_AND_SCHEMA_VERIFIED",
        })

    raw_by_source = {
        source: sum(entry["record_count"] for entry in manifest["exports"] if entry["source_id"] == source)
        for source in ("cyrene_shahhat", "qurina_cy", "points_world_heritage")
    }
    raw_total = sum(raw_by_source.values())
    removed = sum(item[3] for item in EXACT_DUPLICATES)
    represented = all_clean + [item["record"] for item in quarantine]
    state_by_id = {item["review_id"]: "CLEAN" for item in all_clean}
    state_by_id.update({item["record"]["review_id"]: "QUARANTINED" for item in quarantine})
    source_layer_counts: dict[tuple[str, str, str, str], int] = {}
    collection_state_counts: dict[tuple[str, str], int] = {}
    quality_flag_counts: dict[str, int] = {}
    quarantine_reason_counts: dict[str, int] = {}
    for record in represented:
        state = state_by_id[record["review_id"]]
        collection_state_counts[(record["review_collection"], state)] = collection_state_counts.get((record["review_collection"], state), 0) + 1
        for source_reference in record["source_references"]:
            key = (source_reference["source_id"], source_reference["relative_layer"], record["review_collection"], state)
            source_layer_counts[key] = source_layer_counts.get(key, 0) + 1
        for flag in record["quality_flags"]:
            quality_flag_counts[flag] = quality_flag_counts.get(flag, 0) + 1
    for item in quarantine:
        reason = item["quarantine_reason"]
        quarantine_reason_counts[reason] = quarantine_reason_counts.get(reason, 0) + 1
    reporting_audit = {
        "source_layer_collection_state_cross_tab": [
            {"source_id": key[0], "relative_layer": key[1], "review_collection": key[2], "state": key[3], "record_count": count}
            for key, count in sorted(source_layer_counts.items())
        ],
        "thematic_collection_state_cross_tab": [
            {"review_collection": key[0], "state": key[1], "record_count": count}
            for key, count in sorted(collection_state_counts.items())
        ],
        "record_count_by_state": {"CLEAN": len(all_clean), "QUARANTINED": len(quarantine)},
        "heritage_review_group_membership_by_state": {"CLEAN": len(heritage_group["member_review_ids"]), "QUARANTINED": 0},
        "quality_flag_counts": {key: quality_flag_counts[key] for key in sorted(quality_flag_counts)},
        "quarantine_reason_counts": {key: quarantine_reason_counts[key] for key in sorted(quarantine_reason_counts)},
        "source_reference_count": sum(source_layer_counts.values()),
        "represented_record_count": len(represented),
    }
    artifact = {
        "schema_version": 1,
        "reconciliation_id": "cyrene-shahat-source-reconciliation-v1",
        "canonical_destination_slug": "cyrene",
        "registry_record_id": "ndr-shahat-cyrene",
        "name_ar": "قورينا – شحات",
        "name_en": "Cyrene (Shahat)",
        "status": "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE",
        "manifest_provenance": {"basename": MANIFEST_BASENAME, "sha256": MANIFEST_SHA256, "export_count": 32, "export_error_count": 0, "extraction_date": "2026-08-22", "absolute_source_path_recorded": False},
        "source_evaluation": [
            {"source_id": "cyrene_shahhat", "role": "PRIMARY_THEMATIC_SOURCE", "feature_class_count": 18, "raw_record_count": 1537, "decision": "RETAIN_WITH_RECORD_LEVEL_REVIEW"},
            {"source_id": "qurina_cy", "role": "COMPLEMENTARY_SOURCE", "feature_class_count": 13, "raw_record_count": 1519, "decision": "RETAIN_UNIQUE_RECORDS_AND_EXACTLY_CONSOLIDATE_PROVEN_DUPLICATES"},
            {"source_id": "points_world_heritage", "role": "REFERENCE_IDENTITY_SOURCE", "feature_class_count": 1, "raw_record_count": 27, "decision": "RETAIN_AS_REVIEW_EVIDENCE_NOT_PUBLICATION_APPROVAL"},
            {"source_id": "cyrene1", "role": "EXCLUDED_SOURCE", "feature_class_count": 0, "raw_record_count": 0, "decision": "EMPTY_SOURCE_DATABASE"},
        ],
        "source_registry": source_registry,
        "exact_duplicate_consolidations": exact_decisions,
        "collections": collections,
        "identity_candidate_groups": identity_groups,
        "geometry_conflicts": geometry_conflicts,
        "quarantined_records": quarantine,
        "summary": {
            "raw_records_by_source": raw_by_source,
            "raw_record_count": raw_total,
            "exact_duplicate_second_copies_removed": removed,
            "represented_record_count": raw_total - removed,
            "clean_inventory_record_count": len(all_clean),
            "quarantined_record_count": len(quarantine),
            "clean_counts_by_collection": {name: len(collections[name]) for name in COLLECTIONS},
            "identity_candidate_group_count": len(identity_groups),
            "geometry_conflict_count": len(geometry_conflicts),
            "publication_or_registry_gis_count_added": 0,
            "reporting_audit": reporting_audit,
        },
        "governance": {
            "publication_approved": False,
            "canonical_approval": False,
            "public_visibility_enabled": False,
            "institutional_review_status": "UNRESOLVED",
            "runtime_source": False,
            "authoritative_boundary_present": False,
            "official_destination_membership_granted": False,
            "authoritative_archaeological_interpretation_granted": False,
            "verified_media_rights_granted": False,
            "approval_event_reference": None,
        },
        "unresolved_decisions": [
            "Resolve quarantined invalid geometries without inventing coordinates.",
            "Resolve three source attribute/geometry misalignments using institutional identity review.",
            "Resolve the qurina_cy archaeological CRS metadata/geometry conflict while preserving original UTM geometry.",
            "Review fuel, bank, restaurant, cafe, and cross-source heritage identity candidates without proximity-only deduplication.",
            "Review the world-heritage cafe spatial outlier and destination membership.",
            "Complete institutional identity, archaeological interpretation, media-rights, boundary, and publication decisions independently.",
        ],
    }
    return artifact


def validate_artifact(artifact: dict[str, Any], root: Path = ROOT, check_git: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)
    check(artifact.get("schema_version") == 1, "unsupported schema")
    check(artifact.get("canonical_destination_slug") == "cyrene", "canonical slug mismatch")
    check(artifact.get("registry_record_id") == "ndr-shahat-cyrene", "registry linkage mismatch")
    check(artifact.get("status") == "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE", "artifact must remain review-only")
    manifest = artifact.get("manifest_provenance", {})
    check(manifest == {"basename": MANIFEST_BASENAME, "sha256": MANIFEST_SHA256, "export_count": 32, "export_error_count": 0, "extraction_date": "2026-08-22", "absolute_source_path_recorded": False}, "manifest provenance mismatch")
    source_registry = artifact.get("source_registry", [])
    check(len(source_registry) == 32, "source registry must contain 32 exports")
    check(sum(item.get("record_count", 0) for item in source_registry) == 3083, "source registry raw count mismatch")
    check(all(item.get("verification_status") == "HASH_COUNT_AND_SCHEMA_VERIFIED" for item in source_registry), "source verification status mismatch")
    registry_by_export = {item.get("export_file"): item for item in source_registry}
    decisions = artifact.get("exact_duplicate_consolidations", [])
    check(len(decisions) == 5 and sum(item.get("record_count", 0) for item in decisions) == 1438, "exact duplicate consolidation mismatch")
    check(all(len(item.get("source_references", [])) == 2 for item in decisions), "duplicate provenance references missing")
    collections = artifact.get("collections", {})
    check(list(collections) == list(COLLECTIONS), "thematic collection order mismatch")
    clean = [item for name in COLLECTIONS for item in collections.get(name, [])]
    quarantine = artifact.get("quarantined_records", [])
    all_records = clean + [item.get("record", {}) for item in quarantine]
    ids = [item.get("review_id") for item in all_records]
    check(len(ids) == len(set(ids)), "review IDs must be unique")
    check(len(clean) == 1634 and len(quarantine) == 11, "clean or quarantine count mismatch")
    clean_ids = {item.get("review_id") for item in clean}
    quarantine_ids = {item.get("record", {}).get("review_id") for item in quarantine}
    check(clean_ids.isdisjoint(quarantine_ids), "clean and quarantine records overlap")
    check(len(clean_ids | quarantine_ids) == 1645, "represented record accounting mismatch")
    check(sum(item.get("quarantine_reason") == "INVALID_GEOMETRY" for item in quarantine) == 7, "invalid geometry quarantine count mismatch")
    check(sum(item.get("quarantine_reason") == "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT" for item in quarantine) == 3, "misalignment quarantine count mismatch")
    check(sum(item.get("quarantine_reason") == "SPATIAL_OUTLIER" for item in quarantine) == 1, "spatial outlier quarantine mismatch")
    for record in all_records:
        check(record.get("review_collection") in COLLECTIONS, "record review collection is invalid")
        check(record.get("review_id") == _record_id(record.get("review_collection"), record.get("source_references", []), record.get("source_attributes", {}), record.get("source_geometry"), record.get("derived_review_geometry")), "deterministic review ID mismatch")
        for field in GOVERNANCE_FALSE_FIELDS:
            check(record.get(field) is False, f"record grants {field}")
        check(record.get("institutional_review_status") == "UNRESOLVED", "record institutional review must remain unresolved")
        check(record.get("authoritative_boundary") is False and record.get("media_rights_verified") is False, "record claims boundary or media rights")
        check(record.get("destination_membership_status") == "UNRESOLVED" and record.get("archaeological_interpretation_status") == "UNRESOLVED", "record overstates identity or interpretation")
        check(all("C:\\" not in json.dumps(ref, ensure_ascii=False) for ref in record.get("source_references", [])), "absolute source path recorded")
        first_ref = record.get("source_references", [{}])[0]
        source_entry = registry_by_export.get(first_ref.get("export_file"), {})
        geometry_type = source_entry.get("geometry_type")
        quarantined_invalid = any(item.get("record", {}).get("review_id") == record.get("review_id") and item.get("quarantine_reason") == "INVALID_GEOMETRY" for item in quarantine)
        if quarantined_invalid:
            check(not _valid_geometry(geometry_type, record.get("source_geometry")), "invalid geometry quarantine contains valid geometry")
        else:
            check(_valid_geometry(geometry_type, record.get("source_geometry")), "clean or non-geometry quarantine record has invalid geometry")
        source_crs = source_entry.get("source_crs", {}).get("factory_code")
        geometry = record.get("source_geometry", {})
        if geometry_type == "esriGeometryPoint" and source_crs == 4326 and _valid_geometry(geometry_type, geometry):
            check(9.0 <= geometry["x"] <= 25.5 and 19.0 <= geometry["y"] <= 34.0, "WGS 84 point is outside Libya bounds")
        derived = record.get("derived_review_geometry")
        if derived is not None:
            check(derived.get("wkid") == 4326 and _finite(derived.get("longitude")) and _finite(derived.get("latitude")), "derived review geometry is invalid")
            if _finite(derived.get("longitude")) and _finite(derived.get("latitude")):
                check(9.0 <= derived["longitude"] <= 25.5 and 19.0 <= derived["latitude"] <= 34.0, "derived review geometry is outside Libya bounds")
    consolidated = [item for item in clean if len(item.get("source_references", [])) == 2]
    check(len(consolidated) == 1438, "duplicate copies are not represented exactly once")
    conflicts = artifact.get("geometry_conflicts", [])
    check(sum(item.get("quality_flag") == "CRS_METADATA_GEOMETRY_CONFLICT" for item in conflicts) == 14, "UTM/4326 conflict count mismatch")
    check(sum(item.get("quality_flag") == "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT" for item in conflicts) == 3, "heritage misalignment count mismatch")
    misaligned = [item.get("record", {}) for item in quarantine if item.get("quarantine_reason") == "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT"]
    check({item.get("source_name") for item in misaligned} == {"متحف المنحوتاث", "نبع ابوللو", "الحمامات الاغريقية"}, "misaligned quarantine identities mismatch")
    check(all("SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT" in item.get("quality_flags", []) for item in misaligned), "misaligned quarantine quality flag missing")
    check(all(item.get("proposed_identity_evidence") and item.get("resolution_status") == "UNRESOLVED_NO_AUTOMATIC_REPAIR" for item in misaligned), "misaligned quarantine evidence or resolution status mismatch")
    check(all(item.get("proposed_identity_evidence", {}).get("canonical_approval") is False and item.get("proposed_identity_evidence", {}).get("publication_approved") is False for item in misaligned), "misalignment evidence grants approval")
    qurina = [item for item in collections.get("heritage_points", []) if item.get("source_references", [{}])[0].get("export_file") == "qurina_cy__001.esri.json"]
    check(len(qurina) == 14 and all(item.get("derived_review_geometry", {}).get("method") == "SOURCE_ATTRIBUTE_XY" for item in qurina), "derived qurina review geometry mismatch")
    outliers = [item for item in quarantine if item.get("quarantine_reason") == "SPATIAL_OUTLIER"]
    check(len(outliers) == 1 and outliers[0].get("record", {}).get("source_name") == "كافي الشلال شحات", "Cyrene cafe outlier mismatch")
    groups = artifact.get("identity_candidate_groups", [])
    check(sum(item.get("candidate_type") == "FUEL_NEAR_PAIR" for item in groups) == 3, "fuel candidate groups mismatch")
    check(sum(item.get("candidate_type") == "BANK_NEAR_PAIR" for item in groups) == 3, "bank candidate groups mismatch")
    check(all("NO_CONSOLIDATION" in item.get("decision", "") or "PRESERVE" in item.get("decision", "") for item in groups), "candidate group automatically consolidates proximity records")
    clean_id_counts = {review_id: ids.count(review_id) for review_id in clean_ids}
    check(all(count == 1 for count in clean_id_counts.values()), "clean record appears in more than one thematic collection")
    for group in groups:
        member_ids = group.get("member_review_ids", [])
        check(len(member_ids) == len(set(member_ids)), f"duplicate identity group member: {group.get('candidate_type')}")
        check(all(review_id in clean_ids for review_id in member_ids), f"identity group references non-clean record: {group.get('candidate_type')}")
    heritage_group = next((item for item in groups if item.get("candidate_type") == "HERITAGE_CROSS_SOURCE_REVIEW"), {})
    check(len(heritage_group.get("member_review_ids", [])) == 57, "heritage review group clean membership mismatch")
    member_cross_tab = heritage_group.get("member_cross_tab", [])
    check([item.get("review_id") for item in member_cross_tab] == heritage_group.get("member_review_ids"), "heritage member cross-tab mismatch")
    check(all(item.get("state") == "CLEAN" and item.get("review_id") in clean_ids for item in member_cross_tab), "heritage group labels quarantined evidence as clean")
    summary = artifact.get("summary", {})
    check(summary.get("raw_record_count") == 3083 and summary.get("exact_duplicate_second_copies_removed") == 1438, "summary raw or duplicate count mismatch")
    check(summary.get("represented_record_count") == 1645 and summary.get("clean_inventory_record_count") == 1634 and summary.get("quarantined_record_count") == 11, "summary represented counts mismatch")
    computed_collection_counts = {name: len(collections.get(name, [])) for name in COLLECTIONS}
    check(summary.get("clean_counts_by_collection") == computed_collection_counts and sum(computed_collection_counts.values()) == 1634, "thematic counts mismatch")
    audit = summary.get("reporting_audit", {})
    expected_states = {"CLEAN": 1634, "QUARANTINED": 11}
    expected_reasons = {"INVALID_GEOMETRY": 7, "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT": 3, "SPATIAL_OUTLIER": 1}
    expected_flags = {"CRS_METADATA_GEOMETRY_CONFLICT": 14, "INVALID_GEOMETRY_QUARANTINED": 7, "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT": 3, "SPATIAL_OUTLIER": 1}
    check(audit.get("record_count_by_state") == expected_states, "reporting state audit mismatch")
    check(audit.get("heritage_review_group_membership_by_state") == {"CLEAN": 57, "QUARANTINED": 0}, "heritage membership state audit mismatch")
    check(audit.get("quarantine_reason_counts") == expected_reasons, "quarantine reason audit mismatch")
    check(audit.get("quality_flag_counts") == expected_flags, "quality flag audit mismatch")
    check(audit.get("represented_record_count") == 1645 and audit.get("source_reference_count") == 3083, "reporting represented/source reference count mismatch")
    check(sum(item.get("record_count", 0) for item in audit.get("source_layer_collection_state_cross_tab", [])) == 3083, "source/layer reporting cross-tab mismatch")
    check(sum(item.get("record_count", 0) for item in audit.get("thematic_collection_state_cross_tab", [])) == 1645, "collection/state reporting cross-tab mismatch")
    check(summary.get("publication_or_registry_gis_count_added") == 0, "review inventory changes publication GIS count")
    governance = artifact.get("governance", {})
    for field in GOVERNANCE_FALSE_FIELDS:
        check(governance.get(field) is False, f"artifact grants {field}")
    check(governance.get("runtime_source") is False and governance.get("authoritative_boundary_present") is False, "artifact claims runtime or boundary authority")
    registry = json.loads((root / REGISTRY_PATH.relative_to(ROOT)).read_text(encoding="utf-8"))
    check(sum(item.get("gis_record_count", 0) for item in registry.get("records", [])) == 214, "registry GIS count changed")
    cyrene_registry = next((item for item in registry.get("records", []) if item.get("registry_record_id") == "ndr-shahat-cyrene"), {})
    check(cyrene_registry.get("gis_source_reconciliation_present") is True, "registry reconciliation reference missing")
    check(cyrene_registry.get("gis_source_reconciliation_path") == "backend/data/gis/cyrene-source-reconciliation.review.json", "registry reconciliation path mismatch")
    check(cyrene_registry.get("gis_layer_present") is False and cyrene_registry.get("gis_record_count") == 0, "registry treats reconciliation as detailed GIS")
    if check_git:
        result = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", *PROTECTED_PATHS], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        check(not result.stdout.strip(), f"protected artifacts changed: {result.stdout.strip()}")
    if errors:
        raise CyreneReconciliationError("\n".join(errors))
    return {"source_exports": 32, "raw_records": 3083, "clean_records": 1634, "quarantined_records": 11, "duplicates_removed": 1438}


def validate_serialization(path: Path = ARTIFACT_PATH) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r\n" in raw:
        raise CyreneReconciliationError("artifact must be UTF-8 without BOM, LF, and exactly one final newline")
    if b"C:\\\\" in raw or b"visitlibya-local-backups" in raw:
        raise CyreneReconciliationError("artifact contains an absolute local path")


def main() -> int:
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "build":
            artifact = build_artifact(Path(sys.argv[2]))
            ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        elif len(sys.argv) != 1:
            raise CyreneReconciliationError("usage: cyrene_source_reconciliation.py [build SOURCE_EXPORT_DIRECTORY]")
        validate_serialization()
        result = validate_artifact(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError, CyreneReconciliationError) as exc:
        print(f"Cyrene source reconciliation failed:\n{exc}", file=sys.stderr)
        return 1
    print("Cyrene source reconciliation passed: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
