#!/usr/bin/env python3
"""Build and validate the governed national natural-resources review source."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = ROOT / "backend/data/gis/national-natural-resources-source-reconciliation.review.json"
SOURCE_SHA256 = "b389136b4d9f8fcc138f48999745b26b899747830489475b70988f679c442f49"
SOURCE_SIZE = 809652
AUDIT_HASHES = {
    "national-natural-resources-inventory.json": "16f288b801fa2cfa2c3a1df79e7c31d7e3091b6aaa347d658f3e291ba997871c",
    "national-natural-resources-reconciliation-audit.json": "b705f9d570c9b880dc303a88e960e589fe6a20d6af27deba0d7c6ec90562b70b",
    "audit_national_natural_resources.py": "f0d6fedcae4b5cc44136792fec55652fa7f4e43cdbf069f5877219eb4ed0d71b",
    "validate_national_natural_resources_audit.py": "cfaf1da4472c749ecc6e4cdd9c2d4af12d9692f4f977f32f287d31b7cc7c9623",
    "national-natural-resources-inspection-hashes.json": "3d0a40ad46edb620ee73610a1d81e1b5ab60c76db597af151a52b6192801f703",
}
NATURAL_ROUTING = {
    "WATER_RESOURCES_AND_SPRINGS": 382,
    "LAKES_AND_WETLANDS": 92,
    "OASES_AND_PALM_LANDSCAPES": 1,
    "VALLEYS_AND_WADIS": 380,
    "MOUNTAINS_AND_HIGHLANDS": 0,
    "DESERT_AND_DUNE_LANDSCAPES": 2,
    "GEOLOGY_AND_GEOMORPHOLOGY": 1,
    "CAVES_AND_ROCK_FORMATIONS": 6,
    "COASTS_BEACHES_AND_ISLANDS": 3,
    "FORESTS_AND_VEGETATION": 1,
    "PROTECTED_AREAS_AND_PARKS_REVIEW": 7,
    "WILDLIFE_AND_BIODIVERSITY_REVIEW": 1,
    "NATURAL_VIEWPOINTS_AND_LANDSCAPES": 0,
    "UNRESOLVED_NATURAL_CONTEXT": 0,
}
NON_NATURAL_ROUTING = {
    "CATEGORY_SCOPE_MISMATCH_REVIEW": 4,
    "ARCHAEOLOGICAL_OR_HERITAGE_REVIEW": 23,
    "HISTORICAL_OR_MEMORIAL_REVIEW": 0,
    "SETTLEMENT_OR_URBAN_REVIEW": 3,
    "VISITOR_SERVICE_OR_FACILITY_REVIEW": 15,
    "AGRICULTURAL_OR_PRODUCTIVE_SITE_REVIEW": 6,
    "INFRASTRUCTURE_OR_TRANSPORT_REVIEW": 12,
    "MIXED_NATURAL_CULTURAL_REVIEW": 6,
    "UNRESOLVED_NON_NATURAL_CONTEXT": 0,
}
COLLECTIONS = tuple(NATURAL_ROUTING) + tuple(NON_NATURAL_ROUTING)
OVERLAP_PARTITION = {
    "DIRECT_CURATED_SOURCE_ID_OVERLAP": 249,
    "INFERRED_CURATED_NAME_COORDINATE_OVERLAP_WITHOUT_DIRECT_ID": 1,
    "OTHER_GOVERNED_DATASET_ONLY_OVERLAP": 8,
    "NO_INSPECTED_GOVERNED_OVERLAP": 687,
}
MANDATORY_EXCLUSIONS = {
    1: "أطلال حصن بئر احكيم",
    2: "الفرارة موقع أثري مغمور بالمياه",
    3: "المقبرة الايطالية",
    4: "المنطقة الجنائزية",
}
GEOMETRY_METADATA_MISMATCH_ORDINALS = {579, 734, 792, 846, 847}
FALSE_FIELDS = ("publication_approved", "canonical_approval", "public_visibility_enabled")
ALLOWED_CHANGED_PATHS = {
    "backend/data/gis/national-natural-resources-source-reconciliation.review.json",
    "backend/scripts/national_natural_resources_reconciliation.py",
    "backend/tests/unit/scripts/test_national_natural_resources_reconciliation.py",
    "backend/docs/national-natural-resources-reconciliation.md",
}
PROTECTED_PATHS = (
    "backend/data/destinations/national-destination-registry.review.json",
    "backend/scripts/destination_registry.py",
    "backend/tests/unit/scripts/test_destination_registry.py",
    "backend/docs/national-destination-registry.md",
    "backend/data/gis/source-manifest.json",
    "backend/data/gis/institutional-sources.json",
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
    "backend/data/governance",
    "assets",
    "backend/app",
    "backend/models",
    "backend/migrations",
)


class NaturalResourcesReconciliationError(ValueError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _expected_review_id(record: dict) -> str:
    preserved = {
        "source_ordinal": record.get("source_ordinal"),
        "raw_id": record.get("raw_id"),
        "properties": record.get("preserved_properties"),
        "geometry": record.get("geometry"),
        "normalized_name": record.get("proposed_normalized_name"),
    }
    return "nnr-" + hashlib.sha256(SOURCE_SHA256.encode("ascii") + b"\n" + _canonical(preserved)).hexdigest()[:24]


def _overlap_state(record: dict) -> str:
    overlaps = record.get("existing_governed_overlaps", [])
    direct = any(item.get("publication_layer_overlap") is True and item.get("match_type") == "EXACT_REGISTERED_SOURCE_FEATURE_ID" for item in overlaps)
    curated = any(item.get("publication_layer_overlap") is True for item in overlaps)
    if direct:
        return "DIRECT_CURATED_SOURCE_ID_OVERLAP"
    if curated:
        return "INFERRED_CURATED_NAME_COORDINATE_OVERLAP_WITHOUT_DIRECT_ID"
    if overlaps:
        return "OTHER_GOVERNED_DATASET_ONLY_OVERLAP"
    return "NO_INSPECTED_GOVERNED_OVERLAP"


def _governed_media(record: dict) -> list[dict]:
    return [
        {
            "source_reference": path,
            "repository_asset_available": False,
            "publication_media_eligible": False,
            "ownership_or_usage_rights_verified": False,
            "natural_classification_or_destination_identity_granted": False,
        }
        for path in record.get("media_audit", {}).get("referenced_paths", [])
    ]


def build_artifact(audit_directory: Path, source_geojson: Path) -> dict:
    source_raw = source_geojson.read_bytes()
    if len(source_raw) != SOURCE_SIZE or _sha256(source_raw) != SOURCE_SHA256:
        raise NaturalResourcesReconciliationError("authoritative source size or SHA-256 mismatch")
    source = json.loads(source_raw.decode("utf-8-sig"))
    if source.get("type") != "FeatureCollection" or len(source.get("features", [])) != 945:
        raise NaturalResourcesReconciliationError("authoritative source structure mismatch")
    for basename, expected in AUDIT_HASHES.items():
        path = audit_directory / basename
        if not path.is_file() or _sha256(path.read_bytes()) != expected:
            raise NaturalResourcesReconciliationError(f"external audit hash mismatch: {basename}")
    inventory = json.loads((audit_directory / "national-natural-resources-inventory.json").read_text(encoding="utf-8"))
    audit = json.loads((audit_directory / "national-natural-resources-reconciliation-audit.json").read_text(encoding="utf-8"))
    collections = {name: [] for name in COLLECTIONS}
    ordinal_resolution = []
    for source_record in inventory["records"]:
        record = dict(source_record)
        ordinal = record["source_ordinal"]
        record["overlap_partition"] = _overlap_state(record)
        record["source_geometry_metadata_mismatch"] = ordinal in GEOMETRY_METADATA_MISMATCH_ORDINALS
        record["media_references"] = _governed_media(record)
        record["exclusion_from_natural_media"] = record.get("exclusion_from_natural_display", False)
        record["source_status_is_approval"] = False
        collections[record["proposed_review_collection"]].append(record)
        ordinal_resolution.append({
            "source_ordinal": ordinal,
            "review_id": record["review_id"],
            "resolution_bucket": record["resolution_bucket"],
            "review_collection": record["proposed_review_collection"],
            "overlap_partition": record["overlap_partition"],
        })
    for records in collections.values():
        records.sort(key=lambda item: item["source_ordinal"])
    duplicate = audit["duplicate_and_identity_audit"]
    return {
        "schema_version": 1,
        "reconciliation_id": "national-natural-resources-source-reconciliation-v1",
        "status": "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE",
        "scope": "NATIONAL_CROSS_DESTINATION_REVIEW_SOURCE",
        "source_provenance": {
            "source_id": "natural-atlas-media",
            "portable_source_label": "national_natural_resources_atlas_with_media_2026",
            "source_basename": "atlasnatrual-with-media.geojson",
            "source_size_bytes": SOURCE_SIZE,
            "source_sha256": SOURCE_SHA256,
            "source_format": "GeoJSON FeatureCollection",
            "source_geometry_type": "Point",
            "registered_source_hash_relationship": "IDENTICAL_CONTENT_ALREADY_REGISTERED",
            "source_manifest_change_required": False,
            "absolute_source_path_recorded": False,
            "audit_inputs": [{"basename": name, "sha256": digest} for name, digest in AUDIT_HASHES.items()],
        },
        "source_field_profile": {
            "property_keys": inventory["property_keys"],
            "field_completeness": inventory["field_completeness"],
            "frequency_tables": inventory["frequency_tables"],
            "raw_status_is_source_text_not_approval": True,
            "raw_id_is_sole_deterministic_identity": False,
        },
        "collections": collections,
        "ordinal_resolution": ordinal_resolution,
        "mandatory_natural_display_exclusions": [
            {
                "source_ordinal": ordinal,
                "raw_name": name,
                "review_collection": "CATEGORY_SCOPE_MISMATCH_REVIEW",
                "exclusion_from_natural_display": True,
                "exclusion_from_natural_media": True,
                "reason": "ARCHAEOLOGICAL_OR_HISTORICAL_EVIDENCE_IS_NOT_NATURAL_BY_WATER_ADJACENCY_CATEGORY_OR_SUBMERSION",
            }
            for ordinal, name in MANDATORY_EXCLUSIONS.items()
        ],
        "overlap_policy": {
            "partition_counts": OVERLAP_PARTITION,
            "any_inspected_governed_overlap": 258,
            "any_curated_natural_overlap": 250,
            "direct_green_mountain_source_id_overlap": 180,
            "direct_libyan_sahara_source_id_overlap": 69,
            "inferred_curated_overlap_ordinal": 540,
            "orthogonal_to_resolution_accounting": True,
            "creates_duplicate_public_record": False,
            "increases_registry_counts": False,
            "grants_canonical_identity": False,
            "overwrites_curated_data": False,
            "authorizes_automatic_consolidation": False,
            "heritage_source_id_overlap_ordinals_preserved": [832, 913],
        },
        "duplicate_and_conflict_review": {
            "duplicate_raw_id_groups": duplicate["duplicate_raw_id_groups"],
            "exact_complete_feature_duplicate_groups": duplicate["exact_duplicate_feature_groups"],
            "normalized_name_exact_coordinate_groups": duplicate["normalized_name_exact_coordinate_groups"],
            "different_name_identical_coordinate_groups": duplicate["different_name_identical_coordinate_groups"],
            "same_name_different_coordinate_groups": duplicate["same_name_different_coordinate_groups"],
            "near_coordinate_candidates": duplicate["near_coordinate_candidates"],
            "automatic_consolidation_performed": False,
        },
        "spatial_quality": {
            **audit["spatial_quality"],
            "source_geometry_metadata_mismatch_ordinals": sorted(GEOMETRY_METADATA_MISMATCH_ORDINALS),
            "all_source_geometries_preserved_without_repair": True,
        },
        "media_policy": {
            "enriched_or_linked_records": 21,
            "records_with_nonempty_images": 14,
            "source_image_references": 32,
            "repository_missing_references": 32,
            "duplicate_media_linkage_groups": audit["media_audit"]["duplicate_image_linkage"],
            "rights_evidence_present": False,
            "all_missing_references_excluded_from_display": True,
            "media_copied_to_public_assets": False,
            "media_grants_classification_identity_approval_or_visibility": False,
        },
        "publication_and_registry_invariants": {
            "green_mountain_curated_features": 180,
            "libyan_sahara_curated_features": 69,
            "curated_natural_frontend_total": 249,
            "publication_oriented_national_gis_count": 214,
            "review_records_added_to_publication_count": 0,
            "registry_modified": False,
            "source_manifest_modified": False,
            "approval_ledger_event_created": False,
        },
        "summary": {
            "raw_source_ordinals": 945,
            "clean_natural_resource_review_representatives": 876,
            "category_scope_mismatch": 4,
            "mixed_natural_cultural_review": 6,
            "other_non_natural_review": 59,
            "safe_duplicate_members": 0,
            "coordinate_or_identity_quarantine": 0,
            "resolved_source_ordinals": 945,
            "natural_routing_counts": NATURAL_ROUTING,
            "non_natural_and_mixed_routing_counts": NON_NATURAL_ROUTING,
            "overlap_partition_counts": OVERLAP_PARTITION,
        },
        "governance": {
            "review_only": True,
            "runtime_source": False,
            "publication_approved": False,
            "canonical_approval": False,
            "public_visibility_enabled": False,
            "institutional_review_status": "UNRESOLVED",
            "canonical_destination": None,
            "resolution": "UNRESOLVED_NO_AUTOMATIC_REPAIR",
        },
    }


def _all_records(artifact: dict) -> list[dict]:
    return [record for name in COLLECTIONS for record in artifact.get("collections", {}).get(name, [])]


def validate_artifact(artifact: dict, root: Path = ROOT, check_git: bool = True) -> dict:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(artifact.get("schema_version") == 1, "schema version mismatch")
    check(artifact.get("status") == "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE", "review status mismatch")
    check(artifact.get("scope") == "NATIONAL_CROSS_DESTINATION_REVIEW_SOURCE", "national scope mismatch")
    provenance = artifact.get("source_provenance", {})
    check(provenance.get("source_sha256") == SOURCE_SHA256 and provenance.get("source_size_bytes") == SOURCE_SIZE, "source provenance mismatch")
    check({item.get("basename"): item.get("sha256") for item in provenance.get("audit_inputs", [])} == AUDIT_HASHES, "audit hash provenance mismatch")
    check(provenance.get("source_manifest_change_required") is False and provenance.get("absolute_source_path_recorded") is False, "source governance mismatch")
    check(list(artifact.get("collections", {})) == list(COLLECTIONS), "collection order mismatch")
    expected_routing = NATURAL_ROUTING | NON_NATURAL_ROUTING
    check({name: len(artifact.get("collections", {}).get(name, [])) for name in COLLECTIONS} == expected_routing, "routing count mismatch")
    records = _all_records(artifact)
    check(len(records) == 945, "record count mismatch")
    ordinals = [record.get("source_ordinal") for record in records]
    check(len(set(ordinals)) == 945 and set(ordinals) == set(range(1, 946)), "source ordinals do not resolve exactly once")
    check(len({record.get("review_id") for record in records}) == 945, "review IDs are not unique")
    overlap_counts = Counter(record.get("overlap_partition") for record in records)
    check(overlap_counts == Counter(OVERLAP_PARTITION), "overlap partition mismatch")
    check(next((record for record in records if record.get("source_ordinal") == 540), {}).get("overlap_partition") == "INFERRED_CURATED_NAME_COORDINATE_OVERLAP_WITHOUT_DIRECT_ID", "ordinal 540 overlap mismatch")
    media_reference_count = 0
    for record in records:
        ordinal = record.get("source_ordinal")
        geometry = record.get("geometry", {})
        coordinates = geometry.get("coordinates")
        check(geometry.get("type") == "Point" and isinstance(coordinates, list) and len(coordinates) == 2 and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in coordinates), f"invalid Point geometry at ordinal {ordinal}")
        check(9.0 <= coordinates[0] <= 25.5 and 19.0 <= coordinates[1] <= 33.5, f"coordinate outside Libya review bounds at ordinal {ordinal}")
        check(record.get("review_id") == _expected_review_id(record), f"deterministic ID mismatch at ordinal {ordinal}")
        check(record.get("source_geometry_metadata_mismatch") is (ordinal in GEOMETRY_METADATA_MISMATCH_ORDINALS), f"geometry metadata mismatch flag drift at ordinal {ordinal}")
        for field in FALSE_FIELDS:
            check(record.get(field) is False, f"ordinal {ordinal} grants {field}")
        check(record.get("institutional_review_status") == "UNRESOLVED" and record.get("canonical_destination") is None and record.get("resolution") == "UNRESOLVED_NO_AUTOMATIC_REPAIR", f"ordinal {ordinal} governance drift")
        check(record.get("source_status_is_approval") is False, f"source status promoted at ordinal {ordinal}")
        for media in record.get("media_references", []):
            media_reference_count += 1
            check(media.get("repository_asset_available") is False and media.get("publication_media_eligible") is False and media.get("ownership_or_usage_rights_verified") is False, f"media authority granted at ordinal {ordinal}")
    for ordinal, name in MANDATORY_EXCLUSIONS.items():
        record = next((item for item in records if item.get("source_ordinal") == ordinal), {})
        check(record.get("raw_name") == name and record.get("proposed_review_collection") == "CATEGORY_SCOPE_MISMATCH_REVIEW", f"mandatory exclusion identity/routing mismatch at ordinal {ordinal}")
        check(record.get("exclusion_from_natural_display") is True and record.get("exclusion_from_natural_media") is True, f"mandatory display/media exclusion missing at ordinal {ordinal}")
        check(all(record not in artifact["collections"][collection] for collection in NATURAL_ROUTING), f"mandatory exclusion appears in clean collection at ordinal {ordinal}")
    check(media_reference_count == 32, "media reference count mismatch")
    duplicate = artifact.get("duplicate_and_conflict_review", {})
    check(not duplicate.get("duplicate_raw_id_groups") and not duplicate.get("exact_complete_feature_duplicate_groups"), "unexpected automatic duplicate evidence")
    check([item.get("source_ordinals") for item in duplicate.get("normalized_name_exact_coordinate_groups", [])] == [[539, 540], [889, 890]], "name/coordinate groups changed")
    check(len(duplicate.get("same_name_different_coordinate_groups", [])) == 76, "same-name/different-coordinate count changed")
    check(len(duplicate.get("near_coordinate_candidates", {}).get("10", [])) == 22 and len(duplicate.get("near_coordinate_candidates", {}).get("25", [])) == 24 and len(duplicate.get("near_coordinate_candidates", {}).get("100", [])) == 39, "near-coordinate evidence changed")
    conflict = duplicate.get("different_name_identical_coordinate_groups", [])
    check(len(conflict) == 1 and conflict[0].get("source_ordinals") == [597, 601], "coordinate identity conflict changed")
    summary = artifact.get("summary", {})
    expected_summary = {"raw_source_ordinals": 945, "clean_natural_resource_review_representatives": 876, "category_scope_mismatch": 4, "mixed_natural_cultural_review": 6, "other_non_natural_review": 59, "safe_duplicate_members": 0, "coordinate_or_identity_quarantine": 0, "resolved_source_ordinals": 945}
    check(all(summary.get(key) == value for key, value in expected_summary.items()), "summary accounting mismatch")
    check(summary.get("natural_routing_counts") == NATURAL_ROUTING and summary.get("non_natural_and_mixed_routing_counts") == NON_NATURAL_ROUTING and summary.get("overlap_partition_counts") == OVERLAP_PARTITION, "summary routing/overlap mismatch")
    invariants = artifact.get("publication_and_registry_invariants", {})
    check(invariants == {"green_mountain_curated_features": 180, "libyan_sahara_curated_features": 69, "curated_natural_frontend_total": 249, "publication_oriented_national_gis_count": 214, "review_records_added_to_publication_count": 0, "registry_modified": False, "source_manifest_modified": False, "approval_ledger_event_created": False}, "publication invariant declaration mismatch")
    green = json.loads((root / "backend/data/gis/green-mountain-tourism-curated.review.json").read_text(encoding="utf-8"))
    sahara = json.loads((root / "backend/data/gis/libyan-sahara-tourism-curated.review.json").read_text(encoding="utf-8"))
    registry = json.loads((root / "backend/data/destinations/national-destination-registry.review.json").read_text(encoding="utf-8"))
    check(len(green.get("records", [])) == 180 and len(sahara.get("records", [])) == 69, "curated natural counts changed")
    check(sum(item.get("gis_record_count", 0) for item in registry.get("records", [])) == 214, "publication-oriented registry GIS count changed")
    check((root / "backend/data/governance/publication-approval-ledger.jsonl").stat().st_size == 0, "approval ledger is not empty")
    institutional = json.loads((root / "backend/data/gis/institutional-sources.json").read_text(encoding="utf-8"))
    serialized_institutional = json.dumps(institutional, ensure_ascii=False)
    check("natural-atlas-media" in serialized_institutional and SOURCE_SHA256 in serialized_institutional, "exact source is not registered")
    governance = artifact.get("governance", {})
    check(governance.get("review_only") is True and governance.get("runtime_source") is False, "artifact runtime governance mismatch")
    for field in FALSE_FIELDS:
        check(governance.get(field) is False, f"artifact grants {field}")
    if check_git:
        result = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        changed = {line[3:].replace("\\", "/") for line in result.stdout.splitlines() if len(line) >= 4}
        check(changed <= ALLOWED_CHANGED_PATHS, f"changed-file allowlist violation: {sorted(changed - ALLOWED_CHANGED_PATHS)}")
        protected = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", *PROTECTED_PATHS], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        check(not protected.stdout.strip(), f"protected artifacts changed: {protected.stdout.strip()}")
    if errors:
        raise NaturalResourcesReconciliationError("\n".join(errors))
    return {"source_ordinals": 945, "clean_natural": 876, "non_natural_or_mixed": 69, "media_references": 32, "governed_overlaps": 258}


def validate_serialization(path: Path = ARTIFACT_PATH) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r\n" in raw:
        raise NaturalResourcesReconciliationError("artifact must be UTF-8 without BOM, LF, and exactly one final newline")
    if re.search(rb"[A-Za-z]:\\", raw) or b"visitlibya-local-backups" in raw or b"visitlibya-gis-sources" in raw:
        raise NaturalResourcesReconciliationError("artifact contains an absolute/local source path")


def main() -> int:
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "build":
            artifact = build_artifact(Path(sys.argv[2]), Path(sys.argv[3]))
            ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        elif len(sys.argv) != 1:
            raise NaturalResourcesReconciliationError("usage: national_natural_resources_reconciliation.py [build AUDIT_DIRECTORY SOURCE_GEOJSON]")
        validate_serialization()
        result = validate_artifact(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")))
        print("National natural-resources reconciliation validation passed: " + json.dumps(result, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, NaturalResourcesReconciliationError) as exc:
        print(f"National natural-resources reconciliation validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
