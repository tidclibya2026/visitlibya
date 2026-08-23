#!/usr/bin/env python3
"""Build and validate the review-only Old Tripoli KML reconciliation."""

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
ARTIFACT_PATH = ROOT / "backend/data/gis/old-tripoli-source-reconciliation.review.json"
REGISTRY_PATH = ROOT / "backend/data/destinations/national-destination-registry.review.json"
SOURCE_SHA256 = "26ffc9519ebccfaafbd029e070dd21e736c0f0bc839b36231668792d6866eab5"
SOURCE_SIZE = 967226
AUDIT_HASHES = {
    "old-tripoli-kml-inventory.json": "a2b2079e1e192121c2913f8130177d3b76820573aacb01757a6dcef19f9b59d0",
    "old-tripoli-kml-reconciliation-audit.json": "744ea36e8c697713b9a3e543d18959bde27ed4a6b936be5a08e228990f60bd3c",
    "audit_old_tripoli_kml.py": "71f421c8b2133882b059cb042ea725ebab1478f24317ebc47814f3c877ebc086",
    "validate_old_tripoli_audit.py": "0fc02da08078bd05ba74862b41c1fd5b6956fb83bc0525926f07d82810a5a89f",
    "old-tripoli-inspection-hashes.json": "89b90e480b0f22291fb12a48e1e20657fba5bbbfbc2fb4bf8d00042c3794e6f8",
}
COLLECTIONS = (
    "CONTEXTUAL_URBAN_NETWORK_REVIEW",
    "RELIGIOUS_HERITAGE",
    "ACCESS_AND_VISITOR_ROUTES",
    "HISTORIC_BUILDINGS_AND_URBAN_HERITAGE",
    "VISITOR_SERVICES_AND_FACILITIES",
    "ARCHAEOLOGICAL_AND_MONUMENTAL_HERITAGE",
    "REVIEW_POLYGONS_AND_AREAS",
    "TRADITIONAL_MARKETS_AND_CRAFTS",
    "UNRESOLVED_OTHER_CONTEXT",
    "LANDSCAPE_AND_OPEN_SPACES",
    "MUSEUMS_AND_CULTURAL_FACILITIES",
)
EXPECTED_ROUTING = {
    "CONTEXTUAL_URBAN_NETWORK_REVIEW": 285,
    "RELIGIOUS_HERITAGE": 30,
    "ACCESS_AND_VISITOR_ROUTES": 26,
    "HISTORIC_BUILDINGS_AND_URBAN_HERITAGE": 24,
    "VISITOR_SERVICES_AND_FACILITIES": 19,
    "ARCHAEOLOGICAL_AND_MONUMENTAL_HERITAGE": 13,
    "REVIEW_POLYGONS_AND_AREAS": 10,
    "TRADITIONAL_MARKETS_AND_CRAFTS": 8,
    "UNRESOLVED_OTHER_CONTEXT": 8,
    "LANDSCAPE_AND_OPEN_SPACES": 5,
    "MUSEUMS_AND_CULTURAL_FACILITIES": 2,
}
FALSE_FIELDS = ("publication_approved", "canonical_approval", "public_visibility_enabled")
PROTECTED_PATHS = (
    "assets/js/data/natural-tourism-layers.js",
    "assets/js/data/curated-destinations.js",
    "backend/data/dev/destinations.json",
    "backend/data/governance",
    "backend/data/gis/source-manifest.json",
    "backend/data/gis/institutional-sources.json",
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
)


class OldTripoliReconciliationError(ValueError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _expected_review_id(record: dict) -> str:
    preserved = {
        "source_ordinal": record.get("source_ordinal"),
        "folder_path": record.get("folder_path"),
        "raw_name": record.get("raw_name"),
        "raw_description": record.get("raw_description"),
        "extended_data": record.get("extended_data"),
        "style_url": record.get("style_url"),
        "inline_style_xml": record.get("inline_style_xml"),
        "geometry_parts": record.get("geometry_parts"),
    }
    digest = hashlib.sha256((SOURCE_SHA256 + "\n").encode("utf-8") + _canonical(preserved)).hexdigest()
    return f"otr-{digest[:24]}"


def _iter_xy(parts: Any):
    if not isinstance(parts, list):
        return
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("type") in {"Point", "LineString"}:
            rows = part.get("coordinates", [])
        elif part.get("type") == "Polygon":
            rows = [row for ring in part.get("coordinates", []) if isinstance(ring, list) for row in ring]
        else:
            rows = []
        for row in rows:
            if isinstance(row, list) and len(row) >= 2:
                yield row[0], row[1]


def _valid_geometry(record: dict) -> bool:
    geometry_type = record.get("geometry_type")
    parts = record.get("geometry_parts")
    if geometry_type not in {"Point", "LineString", "Polygon"} or not isinstance(parts, list) or len(parts) != 1:
        return False
    part = parts[0]
    if part.get("type") != geometry_type:
        return False
    points = list(_iter_xy(parts))
    if geometry_type == "Point" and len(points) != 1:
        return False
    if geometry_type == "LineString" and len(points) < 2:
        return False
    if geometry_type == "Polygon":
        rings = part.get("coordinates")
        if not isinstance(rings, list) or not rings or any(not isinstance(ring, list) or len(ring) < 4 for ring in rings):
            return False
    return bool(points) and all(
        isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        for point in points for value in point
    ) and all(-180 <= x <= 180 and -90 <= y <= 90 for x, y in points)


def build_artifact(audit_directory: Path, source_kml: Path) -> dict:
    source_raw = source_kml.read_bytes()
    if len(source_raw) != SOURCE_SIZE or _sha256(source_raw) != SOURCE_SHA256:
        raise OldTripoliReconciliationError("authoritative KML size or hash mismatch")
    inputs = {}
    for basename, expected in AUDIT_HASHES.items():
        raw = (audit_directory / basename).read_bytes()
        if _sha256(raw) != expected:
            raise OldTripoliReconciliationError(f"corrected audit hash mismatch: {basename}")
        inputs[basename] = raw
    inventory = json.loads(inputs["old-tripoli-kml-inventory.json"])
    audit = json.loads(inputs["old-tripoli-kml-reconciliation-audit.json"])
    records = inventory.get("records", [])
    if len(records) != 430 or audit.get("summary", {}).get("raw_placemarks") != 430:
        raise OldTripoliReconciliationError("corrected audit source accounting mismatch")
    collections = {name: [] for name in COLLECTIONS}
    for record in records:
        collection = record.get("proposed_review_collection")
        if collection not in collections:
            raise OldTripoliReconciliationError(f"unsupported review collection: {collection!r}")
        collections[collection].append(record)
    conflicts = audit.get("conflicts", {})
    return {
        "schema_version": 1,
        "reconciliation_id": "old-tripoli-source-reconciliation-v1",
        "status": "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE",
        "registry_record_id": "ndr-tripoli",
        "identity_model": {
            "tripoli": {"slug": "tripoli", "role": "MODERN_CITY_AND_BROAD_DESTINATION", "public_runtime_identity_existing": True},
            "old_tripoli": {"proposed_slug": "old-tripoli", "name_ar": "المدينة القديمة بطرابلس", "name_en": "Old Tripoli", "role": "DISTINCT_NESTED_HISTORIC_URBAN_HERITAGE_DESTINATION", "public_runtime_identity_created": False},
            "relationship": "tripoli CONTAINS_HERITAGE_DESTINATION old-tripoli",
            "relationship_status": "REVIEW_GOVERNANCE_METADATA_ONLY",
            "identities_merged": False,
            "coordinate_or_boundary_inheritance": False,
        },
        "source_provenance": {
            "source_id": "tripoli-old-city",
            "portable_source_label": "institutional_old_tripoli_kml_2026_08_15",
            "source_basename": "المدينة القديمة طرابلس.kml",
            "source_size_bytes": SOURCE_SIZE,
            "source_sha256": SOURCE_SHA256,
            "source_format": "KML",
            "coordinate_reference": "KML_LONGITUDE_LATITUDE_WGS84",
            "registered_source_hash_relationship": "IDENTICAL_CONTENT",
            "absolute_source_path_recorded": False,
            "audit_inputs": [{"basename": name, "sha256": digest} for name, digest in AUDIT_HASHES.items()],
        },
        "collections": collections,
        "technical_quarantine": [],
        "safe_duplicate_members": [],
        "identity_conflicts": conflicts.get("same_geometry_different_name", []),
        "same_name_different_geometry_groups": conflicts.get("same_name_different_geometry", []),
        "near_point_review_pairs": conflicts.get("near_point_candidates_within_20m", []),
        "polygon_overlap_review_candidates": conflicts.get("polygon_bbox_overlap_candidates", []),
        "key_identity_review": audit.get("key_heritage_identity_findings", []),
        "line_network_policy": audit.get("line_network_semantics"),
        "polygon_policy": {
            "review_collection": "REVIEW_POLYGONS_AND_AREAS",
            "authoritative_old_tripoli_boundary": False,
            "authoritative_footprint": False,
            "public_boundary": False,
            "boundary_derived_from_geometry_envelope_or_distribution": False,
        },
        "media_policy": {
            "records_with_media_references": 114,
            "source_evidence_only": True,
            "ownership_or_usage_rights_granted": False,
            "identity_or_spatial_authority_granted": False,
            "publication_permission_granted": False,
            "media_copied_to_public_assets": False,
        },
        "ordinal_resolution": [{"source_ordinal": record["source_ordinal"], "review_id": record["review_id"], "state": "CLEAN_REVIEW_REPRESENTATIVE"} for record in records],
        "summary": {
            "source_record_count": 430,
            "reconciled_review_record_count": 430,
            "clean_representative_count": 430,
            "site_oriented_review_geometry_count": 145,
            "contextual_network_geometry_count": 285,
            "point_count": 135,
            "linestring_count": 285,
            "polygon_count": 10,
            "named_linestring_count": 49,
            "unnamed_linestring_count": 236,
            "technical_quarantine_count": 0,
            "safe_duplicate_member_count": 0,
            "resolved_source_ordinal_count": 430,
            "routing_counts": EXPECTED_ROUTING,
            "same_name_different_geometry_group_count": 15,
            "near_point_review_pair_count": 30,
            "media_reference_record_count": 114,
            "publication_or_registry_gis_count_added": 0,
        },
        "governance": {
            "review_only": True,
            "runtime_source": False,
            "authoritative_destination_anchor_present": False,
            "authoritative_boundary_present": False,
            "publication_approved": False,
            "canonical_approval": False,
            "public_visibility_enabled": False,
            "institutional_review_status": "UNRESOLVED",
            "canonical_destination": None,
            "resolution": "UNRESOLVED_NO_AUTOMATIC_REPAIR",
        },
    }


def validate_artifact(artifact: dict, root: Path = ROOT, check_git: bool = True) -> dict:
    errors = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(artifact.get("schema_version") == 1, "schema version mismatch")
    check(artifact.get("status") == "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE", "review status mismatch")
    check(artifact.get("registry_record_id") == "ndr-tripoli", "registry linkage mismatch")
    provenance = artifact.get("source_provenance", {})
    check(provenance.get("source_sha256") == SOURCE_SHA256 and provenance.get("source_size_bytes") == SOURCE_SIZE, "source provenance mismatch")
    check({item.get("basename"): item.get("sha256") for item in provenance.get("audit_inputs", [])} == AUDIT_HASHES, "audit provenance mismatch")
    check(provenance.get("absolute_source_path_recorded") is False, "absolute source path policy mismatch")
    identity = artifact.get("identity_model", {})
    check(identity.get("relationship") == "tripoli CONTAINS_HERITAGE_DESTINATION old-tripoli", "nested relationship mismatch")
    check(identity.get("identities_merged") is False and identity.get("coordinate_or_boundary_inheritance") is False, "Tripoli identities merged or inherited")
    check(identity.get("old_tripoli", {}).get("public_runtime_identity_created") is False, "public Old Tripoli runtime identity created")
    collections = artifact.get("collections", {})
    check(list(collections) == list(COLLECTIONS), "collection order mismatch")
    check({name: len(collections.get(name, [])) for name in COLLECTIONS} == EXPECTED_ROUTING, "routing counts mismatch")
    records = [item for name in COLLECTIONS for item in collections.get(name, [])]
    check(len(records) == 430, "clean review record count mismatch")
    check(not artifact.get("technical_quarantine") and not artifact.get("safe_duplicate_members"), "unexpected quarantine or safe duplicate member")
    ordinals = [item.get("source_ordinal") for item in records]
    check(ordinals and len(ordinals) == len(set(ordinals)) == 430 and set(ordinals) == set(range(1, 431)), "source ordinals do not resolve exactly once")
    ids = [item.get("review_id") for item in records]
    check(len(ids) == len(set(ids)) == 430, "review IDs are not unique")
    geometry_counts = Counter(item.get("geometry_type") for item in records)
    check(geometry_counts == Counter({"Point": 135, "LineString": 285, "Polygon": 10}), "geometry accounting mismatch")
    line_records = [item for item in records if item.get("geometry_type") == "LineString"]
    check(sum(bool(str(item.get("raw_name", "")).strip()) for item in line_records) == 49, "named LineString count mismatch")
    check(sum(not str(item.get("raw_name", "")).strip() for item in line_records) == 236, "unnamed LineString count mismatch")
    for record in records:
        check(record.get("review_id") == _expected_review_id(record), f"deterministic review ID mismatch at ordinal {record.get('source_ordinal')}")
        check(_valid_geometry(record), f"invalid preserved geometry at ordinal {record.get('source_ordinal')}")
        for field in FALSE_FIELDS:
            check(record.get(field) is False, f"ordinal {record.get('source_ordinal')} grants {field}")
        check(record.get("institutional_review_status") == "UNRESOLVED", f"ordinal {record.get('source_ordinal')} resolves institutional review")
        check(record.get("canonical_destination") is None, f"ordinal {record.get('source_ordinal')} receives canonical destination")
        check(record.get("resolution") == "UNRESOLVED_NO_AUTOMATIC_REPAIR", f"ordinal {record.get('source_ordinal')} resolution changed")
        if record.get("geometry_type") == "LineString":
            check(record.get("proposed_review_collection") == "CONTEXTUAL_URBAN_NETWORK_REVIEW", f"LineString {record.get('source_ordinal')} has unsupported semantic routing")
        if record.get("geometry_type") == "Polygon":
            check(record.get("proposed_review_collection") == "REVIEW_POLYGONS_AND_AREAS", f"polygon {record.get('source_ordinal')} has unsupported routing")
    serialized = json.dumps(artifact, ensure_ascii=False)
    prohibited_network_value = "HISTORIC_URBAN_LINES" + "_AND_NETWORKS"
    check(prohibited_network_value not in serialized, "prohibited historic network classification appears")
    policy = artifact.get("line_network_policy", {})
    check(policy.get("review_collection") == "CONTEXTUAL_URBAN_NETWORK_REVIEW" and policy.get("historic_or_heritage_network_claimed") is False and policy.get("official_or_visitor_route_claimed") is False, "contextual network policy mismatch")
    polygon_policy = artifact.get("polygon_policy", {})
    check(all(polygon_policy.get(field) is False for field in ("authoritative_old_tripoli_boundary", "authoritative_footprint", "public_boundary", "boundary_derived_from_geometry_envelope_or_distribution")), "polygon authority granted")
    conflicts = artifact.get("identity_conflicts", [])
    check(len(conflicts) == 1 and conflicts[0].get("source_ordinals") == [23, 50], "exact-coordinate identity conflict changed")
    check(len(artifact.get("same_name_different_geometry_groups", [])) == 15, "same-name conflict groups changed")
    check(len(artifact.get("near_point_review_pairs", [])) == 30, "near-point evidence changed")
    overlap = artifact.get("polygon_overlap_review_candidates", [])
    check(len(overlap) == 1 and overlap[0].get("source_ordinals") == [136, 137], "polygon overlap evidence changed")
    key_reviews = {item.get("requested_identity"): item for item in artifact.get("key_identity_review", [])}
    variants = {
        "برج القديس جورج": 'برج "القديس جورج"',
        "الكنيسة الأرثوذكسية": "الكنيسة الأرتذوكسية",
        "الحنفية العثمانية": "الحنفية (الشيشمة) العثمانية",
    }
    for proposed, source_fragment in variants.items():
        matches = key_reviews.get(proposed, {}).get("matches", [])
        check(len(matches) == 1 and source_fragment in matches[0].get("raw_name", "") and matches[0].get("identity_match_status") == "SOURCE_VARIANT_REQUIRES_IDENTITY_REVIEW", f"identity normalization safeguard failed for {proposed}")
    media = artifact.get("media_policy", {})
    check(media.get("records_with_media_references") == 114 and media.get("source_evidence_only") is True, "media accounting mismatch")
    check(all(media.get(field) is False for field in ("ownership_or_usage_rights_granted", "identity_or_spatial_authority_granted", "publication_permission_granted", "media_copied_to_public_assets")), "media authority granted")
    summary = artifact.get("summary", {})
    expected_summary = {
        "source_record_count": 430, "reconciled_review_record_count": 430, "clean_representative_count": 430,
        "site_oriented_review_geometry_count": 145, "contextual_network_geometry_count": 285,
        "point_count": 135, "linestring_count": 285, "polygon_count": 10,
        "named_linestring_count": 49, "unnamed_linestring_count": 236,
        "technical_quarantine_count": 0, "safe_duplicate_member_count": 0,
        "resolved_source_ordinal_count": 430, "same_name_different_geometry_group_count": 15,
        "near_point_review_pair_count": 30, "media_reference_record_count": 114,
        "publication_or_registry_gis_count_added": 0,
    }
    check(all(summary.get(field) == value for field, value in expected_summary.items()), "summary accounting mismatch")
    check(summary.get("routing_counts") == EXPECTED_ROUTING, "summary routing mismatch")
    governance = artifact.get("governance", {})
    check(governance.get("review_only") is True and governance.get("runtime_source") is False, "artifact runtime governance mismatch")
    check(governance.get("authoritative_destination_anchor_present") is False and governance.get("authoritative_boundary_present") is False, "artifact claims anchor or boundary")
    for field in FALSE_FIELDS:
        check(governance.get(field) is False, f"artifact grants {field}")
    check(governance.get("canonical_destination") is None and governance.get("institutional_review_status") == "UNRESOLVED", "artifact canonical or institutional state mismatch")
    registry = json.loads((root / REGISTRY_PATH.relative_to(ROOT)).read_text(encoding="utf-8"))
    check(sum(item.get("gis_record_count", 0) for item in registry.get("records", [])) == 214, "registry GIS count changed")
    tripoli = next((item for item in registry.get("records", []) if item.get("registry_record_id") == "ndr-tripoli"), {})
    expected_registry = {
        "gis_source_record_count": 430, "gis_reconciled_review_record_count": 430,
        "gis_site_oriented_review_geometry_count": 145, "gis_contextual_network_geometry_count": 285,
        "gis_technical_quarantine_count": 0, "gis_safe_duplicate_member_count": 0,
    }
    check(tripoli.get("gis_source_reconciliation_present") is True and tripoli.get("gis_source_reconciliation_path") == "backend/data/gis/old-tripoli-source-reconciliation.review.json", "registry reconciliation reference mismatch")
    check(all(tripoli.get(field) == value for field, value in expected_registry.items()), "registry review accounting mismatch")
    check(tripoli.get("gis_layer_present") is False and tripoli.get("gis_record_count") == 0, "registry promotes review evidence")
    relationships = tripoli.get("related_canonical_destination_relationships", [])
    check(relationships == [{"slug": "old-tripoli", "relationship": "CONTAINS_HERITAGE_DESTINATION", "status": "REVIEW_GOVERNANCE_METADATA_ONLY", "public_runtime_destination_created": False}], "registry relationship mismatch")
    if check_git:
        result = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", *PROTECTED_PATHS], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        check(not result.stdout.strip(), f"protected artifacts changed: {result.stdout.strip()}")
    if errors:
        raise OldTripoliReconciliationError("\n".join(errors))
    return {"source_ordinals": 430, "site_oriented": 145, "contextual_network": 285, "technical_quarantine": 0, "safe_duplicate_members": 0}


def validate_serialization(path: Path = ARTIFACT_PATH) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r\n" in raw:
        raise OldTripoliReconciliationError("artifact must be UTF-8 without BOM, LF, and exactly one final newline")
    if re.search(rb"[A-Za-z]:\\", raw) or b"visitlibya-local-backups" in raw or b"visitlibya-gis-sources" in raw:
        raise OldTripoliReconciliationError("artifact contains an absolute/local source path")


def main() -> int:
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "build":
            artifact = build_artifact(Path(sys.argv[2]), Path(sys.argv[3]))
            ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        elif len(sys.argv) != 1:
            raise OldTripoliReconciliationError("usage: old_tripoli_source_reconciliation.py [build AUDIT_DIRECTORY SOURCE_KML]")
        validate_serialization()
        result = validate_artifact(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")))
        print("Old Tripoli source reconciliation validation passed: " + json.dumps(result, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, OldTripoliReconciliationError) as exc:
        print(f"Old Tripoli source reconciliation validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
