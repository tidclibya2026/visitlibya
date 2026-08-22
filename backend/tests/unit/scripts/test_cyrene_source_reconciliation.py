from __future__ import annotations

import copy
import json

import pytest

from scripts.cyrene_source_reconciliation import (
    ARTIFACT_PATH,
    COLLECTIONS,
    ROOT,
    CyreneReconciliationError,
    _record_id,
    validate_artifact,
    validate_serialization,
)


@pytest.fixture
def artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_valid_reconciliation_passes(artifact: dict) -> None:
    assert validate_artifact(artifact, check_git=False) == {
        "source_exports": 32,
        "raw_records": 3083,
        "clean_records": 1634,
        "quarantined_records": 11,
        "duplicates_removed": 1438,
    }
    validate_serialization()


def test_source_evaluation_matrix_is_exact(artifact: dict) -> None:
    evaluations = {item["source_id"]: item for item in artifact["source_evaluation"]}
    assert evaluations["cyrene_shahhat"]["feature_class_count"] == 18
    assert evaluations["cyrene_shahhat"]["raw_record_count"] == 1537
    assert evaluations["cyrene_shahhat"]["role"] == "PRIMARY_THEMATIC_SOURCE"
    assert evaluations["qurina_cy"]["feature_class_count"] == 13
    assert evaluations["qurina_cy"]["raw_record_count"] == 1519
    assert evaluations["qurina_cy"]["role"] == "COMPLEMENTARY_SOURCE"
    assert evaluations["points_world_heritage"]["raw_record_count"] == 27
    assert evaluations["cyrene1"]["decision"] == "EMPTY_SOURCE_DATABASE"


def test_manifest_registry_hashes_counts_and_errors(artifact: dict) -> None:
    assert artifact["manifest_provenance"]["export_count"] == 32
    assert artifact["manifest_provenance"]["export_error_count"] == 0
    assert artifact["manifest_provenance"]["absolute_source_path_recorded"] is False
    registry = artifact["source_registry"]
    assert len(registry) == 32
    assert sum(item["record_count"] for item in registry) == 3083
    assert all(len(item["sha256"]) == 64 for item in registry)
    assert all(item["verification_status"] == "HASH_COUNT_AND_SCHEMA_VERIFIED" for item in registry)


def test_exact_duplicate_layers_consolidate_once_with_both_sources(artifact: dict) -> None:
    expected = {"roads": 1376, "buildings": 38, "schools": 11, "mosques": 11, "lodges": 2}
    decisions = {item["logical_layer"]: item for item in artifact["exact_duplicate_consolidations"]}
    assert {key: value["record_count"] for key, value in decisions.items()} == expected
    assert sum(expected.values()) == 1438
    assert all(len(item["source_references"]) == 2 for item in decisions.values())
    clean = [record for collection in artifact["collections"].values() for record in collection]
    assert sum(len(item["source_references"]) == 2 for item in clean) == 1438


def test_clean_collection_counts_are_exact(artifact: dict) -> None:
    assert artifact["summary"]["clean_counts_by_collection"] == {
        "heritage_points": 31,
        "heritage_polygons": 14,
        "natural_context_points": 14,
        "visitor_services_points": 128,
        "access_roads": 1376,
        "buildings_context": 71,
    }
    assert artifact["summary"]["clean_inventory_record_count"] == 1634
    assert artifact["summary"]["represented_record_count"] == 1645


def test_temple_and_archaeological_invalid_geometries_are_quarantined(artifact: dict) -> None:
    invalid = [item["record"] for item in artifact["quarantined_records"] if item["quarantine_reason"] == "INVALID_GEOMETRY"]
    names = [item["source_name"] for item in invalid]
    for name in ("معبد باخوس", "معبد الكابيتاليوم", "معبد افروديث", "منزل جايوس ماغنوس", "مسرح 3"):
        assert name in names
    assert names.count(None) == 1
    assert "مطعم الكرم العربي" in names
    assert all("INVALID_GEOMETRY_QUARANTINED" in item["quality_flags"] for item in invalid)


def test_three_attribute_geometry_misalignments_preserve_world_evidence(artifact: dict) -> None:
    conflicts = [item for item in artifact["geometry_conflicts"] if item["quality_flag"] == "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT"]
    assert {item["source_name"] for item in conflicts} == {"متحف المنحوتاث", "نبع ابوللو", "الحمامات الاغريقية"}
    assert {item["proposed_identity_evidence"]["source_name"] for item in conflicts} == {"معبد الكبيتوليوم", "الحمامات الاغريقية", "أثار قورينا"}
    assert all(item["preserved_source_geometry"] == item["proposed_identity_evidence"]["source_geometry"] for item in conflicts)
    assert all(item["proposed_identity_evidence"]["canonical_approval"] is False for item in conflicts)
    quarantined = [item["record"] for item in artifact["quarantined_records"] if item["quarantine_reason"] == "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT"]
    assert {item["source_name"] for item in quarantined} == {"متحف المنحوتاث", "نبع ابوللو", "الحمامات الاغريقية"}
    assert all(item["resolution_status"] == "UNRESOLVED_NO_AUTOMATIC_REPAIR" for item in quarantined)
    assert all(item["proposed_identity_evidence"] for item in quarantined)
    assert all(item["canonical_approval"] is False and item["publication_approved"] is False and item["public_visibility_enabled"] is False for item in quarantined)
    clean_ids = {item["review_id"] for collection in artifact["collections"].values() for item in collection}
    assert clean_ids.isdisjoint(item["review_id"] for item in quarantined)


def test_qurina_crs_conflict_preserves_utm_and_derives_wgs_review_points(artifact: dict) -> None:
    records = [item for item in artifact["collections"]["heritage_points"] if item["source_references"][0]["export_file"] == "qurina_cy__001.esri.json"]
    assert len(records) == 14
    assert all(item["source_geometry"]["x"] > 1_000_000 for item in records)
    assert all(item["derived_review_geometry"]["method"] == "SOURCE_ATTRIBUTE_XY" for item in records)
    assert all(item["derived_review_geometry"]["longitude"] == item["source_attributes"]["x"] for item in records)
    assert all(item["derived_review_geometry"]["latitude"] == item["source_attributes"]["y"] for item in records)
    assert all("CRS_METADATA_GEOMETRY_CONFLICT" in item["quality_flags"] for item in records)


def test_world_heritage_cafe_outlier_is_quarantined(artifact: dict) -> None:
    outlier = next(item["record"] for item in artifact["quarantined_records"] if item["quarantine_reason"] == "SPATIAL_OUTLIER")
    assert outlier["source_name"] == "كافي الشلال شحات"
    assert outlier["source_geometry"]["x"] == pytest.approx(20.10552400000006)
    assert outlier["source_geometry"]["y"] == pytest.approx(32.086851000000024)
    assert "SPATIAL_OUTLIER" in outlier["quality_flags"]


def test_proximity_candidates_are_not_consolidated(artifact: dict) -> None:
    groups = artifact["identity_candidate_groups"]
    fuel = [item for item in groups if item["candidate_type"] == "FUEL_NEAR_PAIR"]
    banks = [item for item in groups if item["candidate_type"] == "BANK_NEAR_PAIR"]
    assert len(fuel) == 3
    assert [item["distance_m"] for item in fuel] == pytest.approx([13.899, 15.541, 18.427], abs=0.01)
    assert len(banks) == 3
    assert [item["distance_m"] for item in banks] == pytest.approx([6.076, 8.247, 15.822], abs=0.01)
    assert next(item for item in groups if item["candidate_type"] == "BANK_UNPAIRED_SOURCE_RECORD")["member_review_ids"]
    assert all("NO_CONSOLIDATION" in item["decision"] or "PRESERVE" in item["decision"] for item in groups)


def test_restaurant_cafe_and_heritage_unions_remain_review_groups(artifact: dict) -> None:
    groups = {item["candidate_type"]: item for item in artifact["identity_candidate_groups"]}
    assert len(groups["RESTAURANT_UNION_REVIEW"]["member_review_ids"]) == 20
    assert len(groups["CAFE_DISTINCT_REVIEW"]["member_review_ids"]) == 4
    heritage = groups["HERITAGE_CROSS_SOURCE_REVIEW"]
    assert len(heritage["member_review_ids"]) == 57
    assert heritage["membership_policy"] == "CLEAN_RECORDS_ONLY_QUARANTINED_EVIDENCE_REFERENCED_THROUGH_CONFLICTS"
    assert {item["review_collection"] for item in heritage["member_cross_tab"]} == {"heritage_points", "natural_context_points", "visitor_services_points"}
    assert all(item["state"] == "CLEAN" for item in heritage["member_cross_tab"])
    assert [item["review_id"] for item in heritage["member_cross_tab"]] == heritage["member_review_ids"]


def test_accounting_groups_and_reporting_cross_tabs_are_fail_closed(artifact: dict) -> None:
    clean = [item for collection in artifact["collections"].values() for item in collection]
    quarantined = [item["record"] for item in artifact["quarantined_records"]]
    clean_ids = [item["review_id"] for item in clean]
    quarantined_ids = [item["review_id"] for item in quarantined]
    assert len(clean_ids) == 1634 and len(quarantined_ids) == 11
    assert len(set(clean_ids)) == len(clean_ids)
    assert set(clean_ids).isdisjoint(quarantined_ids)
    assert len(set(clean_ids) | set(quarantined_ids)) == 1645
    for group in artifact["identity_candidate_groups"]:
        assert len(group["member_review_ids"]) == len(set(group["member_review_ids"]))
        assert set(group["member_review_ids"]) <= set(clean_ids)
    audit = artifact["summary"]["reporting_audit"]
    assert audit["record_count_by_state"] == {"CLEAN": 1634, "QUARANTINED": 11}
    assert audit["heritage_review_group_membership_by_state"] == {"CLEAN": 57, "QUARANTINED": 0}
    assert audit["quarantine_reason_counts"] == {"INVALID_GEOMETRY": 7, "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT": 3, "SPATIAL_OUTLIER": 1}
    assert audit["quality_flag_counts"] == {"CRS_METADATA_GEOMETRY_CONFLICT": 14, "INVALID_GEOMETRY_QUARANTINED": 7, "SOURCE_ATTRIBUTE_GEOMETRY_MISALIGNMENT": 3, "SPATIAL_OUTLIER": 1}
    assert sum(item["record_count"] for item in audit["source_layer_collection_state_cross_tab"]) == 3083
    assert sum(item["record_count"] for item in audit["thematic_collection_state_cross_tab"]) == 1645


def test_review_ids_are_unique_and_content_derived(artifact: dict) -> None:
    records = [item for collection in artifact["collections"].values() for item in collection]
    records += [item["record"] for item in artifact["quarantined_records"]]
    ids = [item["review_id"] for item in records]
    assert len(ids) == len(set(ids))
    for item in records:
        assert item["review_id"] == _record_id(item["review_collection"], item["source_references"], item["source_attributes"], item["source_geometry"], item["derived_review_geometry"])


def test_governance_is_fail_closed_for_every_record(artifact: dict) -> None:
    records = [item for collection in artifact["collections"].values() for item in collection]
    records += [item["record"] for item in artifact["quarantined_records"]]
    for item in records:
        assert item["publication_approved"] is False
        assert item["canonical_approval"] is False
        assert item["public_visibility_enabled"] is False
        assert item["institutional_review_status"] == "UNRESOLVED"
        assert item["destination_membership_status"] == "UNRESOLVED"
        assert item["authoritative_boundary"] is False
        assert item["media_rights_verified"] is False


def test_mutated_approval_fails(artifact: dict) -> None:
    broken = copy.deepcopy(artifact)
    broken["collections"]["heritage_points"][0]["publication_approved"] = True
    with pytest.raises(CyreneReconciliationError, match="publication_approved"):
        validate_artifact(broken, check_git=False)


def test_mutated_registry_count_contract_fails(artifact: dict) -> None:
    broken = copy.deepcopy(artifact)
    broken["summary"]["publication_or_registry_gis_count_added"] = 1
    with pytest.raises(CyreneReconciliationError, match="publication GIS count"):
        validate_artifact(broken, check_git=False)


def test_serialization_is_deterministic_utf8_and_path_free(artifact: dict) -> None:
    raw = ARTIFACT_PATH.read_bytes()
    assert raw == (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"visitlibya-local-backups" not in raw and b"C:\\\\" not in raw


def test_validation_makes_no_writes() -> None:
    before = ARTIFACT_PATH.read_bytes()
    validate_artifact(json.loads(before.decode("utf-8")), check_git=False)
    assert ARTIFACT_PATH.read_bytes() == before
