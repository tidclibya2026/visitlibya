#!/usr/bin/env python3
"""Build and validate the review-only Acacus institutional KML reconciliation."""

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
ARTIFACT_PATH = ROOT / "backend/data/gis/acacus-source-reconciliation.review.json"
REGISTRY_PATH = ROOT / "backend/data/destinations/national-destination-registry.review.json"
SOURCE_SHA256 = "641ab45b3ace5e77eae78e63931b08fb925f2494a536f3736d74e01bf5ed2988"
SOURCE_SIZE = 605606
AUDIT_HASHES = {
    "acacus-kml-inventory.json": "5c50205dfe618fd73a031bc3ef0b0f98ea6411437d24fd9f821efd878ba4d33f",
    "acacus-kml-reconciliation-audit.json": "acbd1fc758591e301029bde782d7f6e7d552ece2a8441f2060c5f03d1de2dd3c",
    "acacus-inspection-hashes.json": "ddafd410179659c41292a66497cf662bd5e5d3df61d894afa66feaf1dedbeb83",
    "audit_acacus_kml.py": "cc2eb3a422fa2b593dfd783f6937f8fe5fa527784d43d26090561264b68d7007",
    "validate_acacus_correction.py": "57cca8c44589f26c30b9691fa17282b6d84d4f6168c02bf491a61465c5652334",
}
COLLECTIONS = (
    "ARCHAEOLOGY", "ROCK_ART_AND_INSCRIPTIONS", "CULTURAL_HERITAGE",
    "NATURE_AND_DESERT_LANDSCAPE", "GEOLOGY_AND_GEOMORPHOLOGY", "WATER_RESOURCES",
    "ENTRANCES_AND_VISITOR_ROUTES", "SETTLEMENTS_AND_VISITOR_SERVICES",
    "CAVES_AND_SHELTERS", "UNRESOLVED_OTHER_CONTEXT",
)
EXPECTED_ROUTING = {
    "ARCHAEOLOGY": 0, "ROCK_ART_AND_INSCRIPTIONS": 35, "CULTURAL_HERITAGE": 0,
    "NATURE_AND_DESERT_LANDSCAPE": 57, "GEOLOGY_AND_GEOMORPHOLOGY": 22,
    "WATER_RESOURCES": 19, "ENTRANCES_AND_VISITOR_ROUTES": 10,
    "SETTLEMENTS_AND_VISITOR_SERVICES": 43, "CAVES_AND_SHELTERS": 9,
    "UNRESOLVED_OTHER_CONTEXT": 165,
}
FALSE_FIELDS = ("publication_approved", "canonical_approval", "public_visibility_enabled")
PROTECTED_PATHS = (
    "assets/js/data/natural-tourism-layers.js", "assets/js/data/curated-destinations.js",
    "backend/data/dev/destinations.json", "backend/data/governance",
    "backend/data/gis/source-manifest.json", "backend/data/gis/institutional-sources.json",
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
)


class AcacusReconciliationError(ValueError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _review_id(kind: str, record: dict) -> str:
    return f"acacus-{kind}-{_sha256(_canonical(record))[:24]}"


def _governance() -> dict:
    return {"publication_approved": False, "canonical_approval": False, "public_visibility_enabled": False, "institutional_review_status": "UNRESOLVED"}


def _valid_geometry(record: dict) -> bool:
    geometry_type, coordinates = record.get("geometry_type"), record.get("complete_coordinates")
    if geometry_type is None:
        return coordinates is None
    if geometry_type == "Point":
        return isinstance(coordinates, list) and len(coordinates) == 1 and len(coordinates[0]) >= 2 and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in coordinates[0][:2])
    if geometry_type == "Polygon":
        return isinstance(coordinates, list) and coordinates and all(isinstance(ring, list) and len(ring) >= 4 and all(len(pair) >= 2 and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in pair[:2]) for pair in ring) for ring in coordinates)
    return False


def build_artifact(audit_directory: Path, source_kml: Path) -> dict:
    source_raw = source_kml.read_bytes()
    if len(source_raw) != SOURCE_SIZE or _sha256(source_raw) != SOURCE_SHA256:
        raise AcacusReconciliationError("authoritative KML size or hash mismatch")
    inputs = {}
    for basename, expected in AUDIT_HASHES.items():
        raw = (audit_directory / basename).read_bytes()
        if _sha256(raw) != expected:
            raise AcacusReconciliationError(f"corrected audit hash mismatch: {basename}")
        inputs[basename] = raw
    inventory = json.loads(inputs["acacus-kml-inventory.json"])
    audit = json.loads(inputs["acacus-kml-reconciliation-audit.json"])
    inventory_by_ordinal = {item["source_ordinal"]: item for item in inventory["records"]}
    duplicate_group_by_representative = {item["representative_ordinal"]: item for item in audit["safe_duplicate_consolidations"]}
    collections = {name: [] for name in COLLECTIONS}
    for clean in audit["clean_review_records"]:
        ordinal = clean["representative_ordinal"]
        source_record = inventory_by_ordinal[ordinal]
        wrapper = {
            "review_id": _review_id("record", source_record),
            "source_ordinal": ordinal,
            "routing_collection": clean["routing_collection"],
            "routing_status": "REVIEW_ONLY_NOT_CANONICAL_CLASSIFICATION",
            "source_record": source_record,
            "identity_conflict": clean["identity_conflict"],
            "safe_duplicate_member_ordinals": clean["duplicate_member_ordinals"],
            **_governance(),
        }
        if ordinal == 191:
            wrapper["proposed_identity_review"] = {
                "source_name_ar": "كهف وان موهجاج", "proposed_name_en": "Uan Muhuggiag",
                "identity_verification_status": "REQUIRED", "primary_routing_unchanged": "CAVES_AND_SHELTERS",
                "proposed_cross_domain_review_tags": ["ARCHAEOLOGY", "CULTURAL_HERITAGE", "ROCK_ART_AND_INSCRIPTIONS", "MUMMY_DISCOVERY_ASSOCIATION"],
                "canonical_classification_granted": False, **_governance(),
            }
        collections[clean["routing_collection"]].append(wrapper)
    safe_duplicate_groups = []
    for representative, group in sorted(duplicate_group_by_representative.items()):
        members = []
        for ordinal in group["duplicate_copy_ordinals"]:
            source_record = inventory_by_ordinal[ordinal]
            members.append({"review_id": _review_id("duplicate-member", source_record), "source_ordinal": ordinal, "source_record": source_record, **_governance()})
        safe_duplicate_groups.append({
            "group_id": group["group_id"], "representative_ordinal": representative,
            "representative_review_id": _review_id("record", inventory_by_ordinal[representative]),
            "normalized_name": group["normalized_name"], "exact_coordinate": group["coordinate"],
            "selection_policy": "NORMALIZED_NAME_AND_EXACT_COORDINATE_SPECIFIC_FOLDER_PREFERRED_FOR_ROUTING",
            "duplicate_members": members,
        })
    quarantine = []
    for item in audit["quarantined_records"]:
        source_record = inventory_by_ordinal[item["source_ordinal"]]
        quarantine.append({
            "review_id": _review_id("quarantine", source_record), "source_ordinal": item["source_ordinal"],
            "quarantine_reason": item["reason"], "source_record": source_record,
            "cross_destination_review": item.get("institutional_review"), **_governance(),
        })
    return {
        "schema_version": 1, "reconciliation_id": "acacus-source-reconciliation-v1",
        "status": "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE", "registry_record_id": "ndr-acacus",
        "canonical_destination": {"slug": "acacus", "name_ar": "تادرارت أكاكوس", "name_en": "Tadrart Acacus", "entity_type": "COMPOSITE_CULTURAL_NATURAL_DESTINATION"},
        "governed_dimensions": ["ARCHAEOLOGY", "ROCK_ART_AND_INSCRIPTIONS", "CULTURAL_HERITAGE", "NATURE_AND_DESERT_LANDSCAPE", "GEOLOGY_AND_GEOMORPHOLOGY"],
        "supporting_context_collections": ["WATER_RESOURCES", "ENTRANCES_AND_VISITOR_ROUTES", "SETTLEMENTS_AND_VISITOR_SERVICES", "CAVES_AND_SHELTERS", "UNRESOLVED_OTHER_CONTEXT"],
        "promotional_wording": {"name_ar": "المتحف العالمي المفتوح", "name_en": "Open-air world museum", "verification_status": "SOURCE_VERIFICATION_REQUIRED", "official_title": False, "publication_approved": False, "runtime_promoted": False},
        "source_provenance": {"source_id": "acacus-features", "source_basename": "اكاكوس.kml", "source_sha256": SOURCE_SHA256, "source_size_bytes": SOURCE_SIZE, "source_role": "CURRENT_PRIMARY_RECONCILIATION_SOURCE", "earlier_akakuas_gdb_overrides_kml": False, "absolute_source_path_recorded": False, "audit_inputs": [{"basename": name, "sha256": digest} for name, digest in AUDIT_HASHES.items()]},
        "collections": collections, "safe_duplicate_groups": safe_duplicate_groups,
        "identity_conflicts": audit["same_coordinate_different_name_conflicts"],
        "quarantined_records": quarantine,
        "hotel_identity_safeguard": {"local_source_ordinals": [181, 423], "kept_separate": True, "tripoli_coordinate": [13.19143, 32.89236], "tripoli_record_present": False, "name_similarity_establishes_identity": False, "operational_status_verified": False},
        "ordinal_resolution": audit["ordinal_resolution"],
        "summary": {"source_record_count": 430, "reconciled_review_record_count": 364, "clean_representative_count": 360, "safe_duplicate_member_count": 66, "quarantined_cross_destination_count": 4, "resolved_source_ordinal_count": 430, "clean_counts_by_collection": EXPECTED_ROUTING, "quarantine_reason_counts": dict(sorted(Counter(item["reason"] for item in audit["quarantined_records"]).items())), "publication_or_registry_gis_count_added": 0},
        "governance": {"review_only": True, "runtime_source": False, "authoritative_acacus_boundary_present": False, **_governance()},
    }


def validate_artifact(artifact: dict, root: Path = ROOT, check_git: bool = True) -> dict:
    errors = []
    def check(condition: bool, message: str) -> None:
        if not condition: errors.append(message)
    check(artifact.get("schema_version") == 1 and artifact.get("status") == "REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE", "schema or review status mismatch")
    check(artifact.get("registry_record_id") == "ndr-acacus", "registry linkage mismatch")
    provenance = artifact.get("source_provenance", {})
    check(provenance.get("source_sha256") == SOURCE_SHA256 and provenance.get("source_size_bytes") == SOURCE_SIZE, "source provenance mismatch")
    check({item.get("basename"): item.get("sha256") for item in provenance.get("audit_inputs", [])} == AUDIT_HASHES, "audit provenance mismatch")
    check(provenance.get("absolute_source_path_recorded") is False and provenance.get("earlier_akakuas_gdb_overrides_kml") is False, "source hierarchy or path policy mismatch")
    collections = artifact.get("collections", {})
    check(list(collections) == list(COLLECTIONS), "collection order mismatch")
    clean = [item for name in COLLECTIONS for item in collections.get(name, [])]
    duplicates = [item for group in artifact.get("safe_duplicate_groups", []) for item in group.get("duplicate_members", [])]
    quarantine = artifact.get("quarantined_records", [])
    check(len(clean) == 360 and len(duplicates) == 66 and len(quarantine) == 4, "360/66/4 accounting mismatch")
    check({name: len(collections.get(name, [])) for name in COLLECTIONS} == EXPECTED_ROUTING, "routing counts mismatch")
    all_wrappers = clean + duplicates + quarantine
    ordinals = [item.get("source_ordinal") for item in all_wrappers]
    check(len(ordinals) == len(set(ordinals)) == 430 and set(ordinals) == set(range(1, 431)), "source ordinals do not resolve exactly once")
    ids = [item.get("review_id") for item in all_wrappers]
    check(len(ids) == len(set(ids)), "review IDs are not unique")
    for item in all_wrappers:
        kind = "quarantine" if "quarantine_reason" in item else "duplicate-member" if item in duplicates else "record"
        check(item.get("review_id") == _review_id(kind, item.get("source_record", {})), "deterministic review ID mismatch")
        check(_valid_geometry(item.get("source_record", {})), "invalid preserved geometry")
        for field in FALSE_FIELDS: check(item.get(field) is False, f"record grants {field}")
        check(item.get("institutional_review_status") == "UNRESOLVED", "record review status resolved")
    mathendous = [item for item in quarantine if item.get("source_ordinal") == 23]
    check(len(mathendous) == 1 and all(item.get("source_ordinal") != 23 for item in clean), "Mathendous clean/quarantine routing mismatch")
    if mathendous:
        item, review = mathendous[0], mathendous[0].get("cross_destination_review", {})
        check(item.get("quarantine_reason") == "CROSS_DESTINATION_SCOPE_AND_COORDINATE_CONFLICT", "Mathendous quarantine reason mismatch")
        check(review.get("proposed_destination_scope") == "UBARI_MESSAK_REVIEW" and review.get("proposed_heritage_theme") == "ROCK_ART_AND_INSCRIPTIONS" and review.get("heritage_priority") == "HIGH", "Mathendous proposed routing mismatch")
        check(review.get("notable_subject") == "نقش القطتين المتصارعتين" and review.get("canonical_destination_assignment") is None and review.get("resolution_status") == "UNRESOLVED_NO_AUTOMATIC_REPAIR", "Mathendous identity governance mismatch")
        evidence = review.get("coordinate_conflict_evidence", {})
        check(item.get("source_record", {}).get("complete_coordinates", [[]])[0][:2] == [10.516772, 24.957273], "Mathendous geometry changed")
        check(evidence.get("preserved_source_x") == 12.245440 and evidence.get("preserved_source_y") == 26103950 and evidence.get("possible_decimal_interpretation") == [12.245440, 26.103950] and evidence.get("automatic_coordinate_repair_performed") is False, "Mathendous coordinate evidence mismatch")
        for field in FALSE_FIELDS: check(review.get(field) is False, f"Mathendous review grants {field}")
        check(review.get("notable_subject_publication_approved") is False, "fighting-cats evidence became publication copy")
    uan = [item for item in collections.get("CAVES_AND_SHELTERS", []) if item.get("source_ordinal") == 191]
    check(len(uan) == 1, "Uan Muhuggiag routing missing")
    if uan:
        review = uan[0].get("proposed_identity_review", {})
        check(review.get("source_name_ar") == "كهف وان موهجاج" and review.get("proposed_name_en") == "Uan Muhuggiag" and review.get("identity_verification_status") == "REQUIRED", "Uan Muhuggiag identity review mismatch")
        check(review.get("proposed_cross_domain_review_tags") == ["ARCHAEOLOGY", "CULTURAL_HERITAGE", "ROCK_ART_AND_INSCRIPTIONS", "MUMMY_DISCOVERY_ASSOCIATION"] and review.get("canonical_classification_granted") is False, "Uan Muhuggiag tags or classification mismatch")
        for field in FALSE_FIELDS: check(review.get(field) is False, f"Uan Muhuggiag review grants {field}")
    expected_reasons = {"CROSS_DESTINATION_SCOPE_AND_COORDINATE_CONFLICT": 1, "EXTERNAL_ADMINISTRATIVE_POLYGON_UNRESOLVED_SCOPE": 1, "MISSING_GEOMETRY": 1, "MISSING_IDENTITY_AND_GEOMETRY": 1}
    check(Counter(item.get("quarantine_reason") for item in quarantine) == Counter(expected_reasons), "quarantine reasons mismatch")
    ghat = next((item for item in quarantine if item.get("source_ordinal") == 199), {})
    check(ghat.get("quarantine_reason") == "EXTERNAL_ADMINISTRATIVE_POLYGON_UNRESOLVED_SCOPE" and artifact.get("governance", {}).get("authoritative_acacus_boundary_present") is False, "Ghat polygon boundary safeguard mismatch")
    conflicts = artifact.get("identity_conflicts", [])
    check(len(conflicts) == 2 and {tuple(item.get("source_ordinals", [])) for item in conflicts} == {(154, 396), (34, 278)}, "identity conflicts changed or merged")
    hotels = artifact.get("hotel_identity_safeguard", {})
    check(hotels.get("local_source_ordinals") == [181, 423] and hotels.get("kept_separate") is True and hotels.get("tripoli_record_present") is False, "hotel identity safeguard mismatch")
    summary = artifact.get("summary", {})
    check(summary.get("source_record_count") == 430 and summary.get("reconciled_review_record_count") == 364 and summary.get("clean_representative_count") == 360 and summary.get("safe_duplicate_member_count") == 66 and summary.get("quarantined_cross_destination_count") == 4, "summary accounting mismatch")
    check(summary.get("publication_or_registry_gis_count_added") == 0, "review evidence inflates publication GIS count")
    registry = json.loads((root / REGISTRY_PATH.relative_to(ROOT)).read_text(encoding="utf-8"))
    check(sum(item.get("gis_record_count", 0) for item in registry.get("records", [])) == 214, "registry GIS count changed")
    acacus = next((item for item in registry.get("records", []) if item.get("registry_record_id") == "ndr-acacus"), {})
    check(acacus.get("gis_source_reconciliation_present") is True and acacus.get("gis_source_reconciliation_path") == "backend/data/gis/acacus-source-reconciliation.review.json", "registry reconciliation reference mismatch")
    check(acacus.get("gis_layer_present") is False and acacus.get("gis_record_count") == 0, "registry promotes review evidence")
    if check_git:
        result = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", *PROTECTED_PATHS], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        check(not result.stdout.strip(), f"protected artifacts changed: {result.stdout.strip()}")
    if errors: raise AcacusReconciliationError("\n".join(errors))
    return {"source_ordinals": 430, "clean": 360, "duplicate_members": 66, "quarantined": 4, "reconciled_review_records": 364}


def validate_serialization(path: Path = ARTIFACT_PATH) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r\n" in raw:
        raise AcacusReconciliationError("artifact must be UTF-8 without BOM, LF, and exactly one final newline")
    if b"C:\\\\" in raw or b"visitlibya-local-backups" in raw or b"visitlibya-gis-sources" in raw:
        raise AcacusReconciliationError("artifact contains an absolute/local source path")


def main() -> int:
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "build":
            artifact = build_artifact(Path(sys.argv[2]), Path(sys.argv[3]))
            ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        elif len(sys.argv) != 1:
            raise AcacusReconciliationError("usage: acacus_source_reconciliation.py [build AUDIT_DIRECTORY SOURCE_KML]")
        validate_serialization()
        result = validate_artifact(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError, AcacusReconciliationError) as exc:
        print(f"Acacus source reconciliation failed:\n{exc}", file=sys.stderr)
        return 1
    print("Acacus source reconciliation passed: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
