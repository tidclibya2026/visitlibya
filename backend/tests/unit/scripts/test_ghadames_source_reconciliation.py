from __future__ import annotations

import copy
import json

import pytest

from scripts.ghadames_source_reconciliation import (
    ARTIFACT_PATH, COLLECTIONS, GhadamesReconciliationError,
    HERITAGE_INTERSECTION_NAMES, INPUT_HASHES, _review_id,
    validate_artifact, validate_serialization,
)


@pytest.fixture
def artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def records(artifact: dict) -> list[dict]:
    return [record for name in COLLECTIONS for record in artifact["collections"][name]]


def test_valid_artifact_passes(artifact: dict) -> None:
    assert validate_artifact(artifact, check_git=False) == {"clean_records": 770, "quarantined_records": 3, "represented_evidence": 773, "duplicate_copies_excluded": 1540}
    validate_serialization()


def test_inspection_hashes_are_exact_and_portable(artifact: dict) -> None:
    assert {item["basename"]: item["sha256"] for item in artifact["inspection_provenance"]["input_hashes"]} == INPUT_HASHES
    assert artifact["inspection_provenance"]["absolute_source_paths_recorded"] is False


def test_source_copy_accounting_is_exact(artifact: dict) -> None:
    source = artifact["source_copy_assessment"]
    assert source["assessed_source_ids"] == ["gadamas_flash16", "gadamas_flash16_cloud", "gadamas_flash8_cloud"]
    assert source["primary_record_count"] == 770
    assert source["excluded_duplicate_copy_count"] == 2
    assert source["excluded_redundant_record_copy_count"] == 1540
    assert source["unique_records_lost"] == source["conflicting_schema_count"] == source["conflicting_geometry_count"] == source["unique_complementary_record_count"] == 0


def test_layer_and_collection_counts_are_exact(artifact: dict) -> None:
    assert {item["relative_layer"]: item["record_count"] for item in artifact["layer_registry"]} == {"buildings": 81, "natural": 15, "places": 4, "roads": 599, "select_landuse": 20, "select_point": 51}
    assert artifact["summary"]["clean_counts_by_collection"] == {"buildings_context": 81, "natural_context": 15, "places_context": 4, "access_roads": 599, "landuse_context": 20, "heritage_core_candidates": 5, "visitor_services": 28, "other_tourism_context": 18}


def test_all_primary_records_are_represented_once(artifact: dict) -> None:
    keys = [(item["source_reference"]["relative_layer"], item["source_reference"]["source_row_ordinal"]) for item in records(artifact)]
    assert len(keys) == len(set(keys)) == 770
    assert all(item["source_reference"]["source_id"] == "gadamas_flash16" for item in records(artifact))


def test_review_ids_are_unique_and_content_derived(artifact: dict) -> None:
    all_records = records(artifact) + [item["record"] for item in artifact["quarantined_records"]]
    assert len({item["review_id"] for item in all_records}) == 773
    for item in records(artifact):
        ref = item["source_reference"]
        assert item["review_id"] == _review_id("record", ref["source_id"], ref["relative_layer"], item["source_attributes_ordered"], item["source_geometry"])


def test_osm_origin_is_not_misrepresented(artifact: dict) -> None:
    assert all(item["source_content_origin"] == "OSM_DERIVED_WHERE_OSM_ID_PRESENT_IN_INSTITUTIONALLY_HELD_GEODATABASE" for item in records(artifact))
    assert all(item["institutional_authorship_of_osm_content_claimed"] is False for item in records(artifact))


def test_boundaries_are_quarantined_and_unapproved(artifact: dict) -> None:
    quarantined = artifact["quarantined_records"]
    assert {item["record"]["source_reference"]["source_id"] for item in quarantined} == {"old_city", "zone", "third_zone"}
    assert all(item["quarantine_reason"] == "UNRESOLVED_BOUNDARY_SEMANTICS" for item in quarantined)
    old_city = next(item["record"] for item in quarantined if item["record"]["source_reference"]["source_id"] == "old_city")
    assert old_city["source_attributes"]["name"] == "مدينة غدامس القديمة"
    for item in quarantined:
        record = item["record"]
        assert record["semantic_status"] == "UNRESOLVED_SOURCE_POLYGON_EVIDENCE"
        assert record["canonical_boundary_approval"] is False
        assert record["unesco_boundary_approval"] is False
        assert record["unesco_buffer_zone_approval"] is False


def test_spatial_intersection_is_review_only(artifact: dict) -> None:
    evidence = artifact["spatial_review_evidence"]
    assert set(evidence["source_names"]) == HERITAGE_INTERSECTION_NAMES
    assert len(evidence["member_review_ids"]) == 5
    assert all(value is False for key, value in evidence.items() if key.startswith("grants_"))
    assert {item["source_attributes"]["Name"] for item in artifact["collections"]["heritage_core_candidates"]} == HERITAGE_INTERSECTION_NAMES


def test_identity_containment_has_no_inheritance(artifact: dict) -> None:
    identity = artifact["identity_architecture"]
    assert identity["broader_destination_slug"] == "ghadames"
    assert identity["heritage_core_slug"] == "old-city-ghadames"
    assert identity["relationship"] == "CONTAINS_HERITAGE_CORE"
    assert identity["identities_merged"] is False
    assert identity["old_city_coordinate_inherited_by_broader_destination"] is False
    assert identity["old_city_boundary_inherited_by_broader_destination"] is False
    assert identity["records_duplicated_for_containment"] is False


def test_tripoli_name_false_positive_is_excluded(artifact: dict) -> None:
    assert all(item["source_attributes"].get("Name") != "فندق الغدامسية" for item in records(artifact))
    assert artifact["false_positive_protection"]["known_other_destination"] == "tripoli"
    assert artifact["false_positive_protection"]["present_in_reconciliation"] is False
    assert artifact["false_positive_protection"]["name_similarity_establishes_membership"] is False


def test_every_record_is_fail_closed_and_sets_are_disjoint(artifact: dict) -> None:
    clean = records(artifact)
    quarantined = [item["record"] for item in artifact["quarantined_records"]]
    assert {item["review_id"] for item in clean}.isdisjoint(item["review_id"] for item in quarantined)
    assert all(item["publication_approved"] is False and item["canonical_approval"] is False and item["public_visibility_enabled"] is False and item["institutional_review_status"] == "UNRESOLVED" for item in clean + quarantined)


@pytest.mark.parametrize("field", ["publication_approved", "canonical_approval", "public_visibility_enabled"])
def test_true_governance_field_fails(artifact: dict, field: str) -> None:
    broken = copy.deepcopy(artifact)
    broken["collections"]["buildings_context"][0][field] = True
    with pytest.raises(GhadamesReconciliationError, match=field):
        validate_artifact(broken, check_git=False)


def test_unesco_boundary_claim_fails(artifact: dict) -> None:
    broken = copy.deepcopy(artifact)
    broken["quarantined_records"][0]["record"]["unesco_boundary_approval"] = True
    with pytest.raises(GhadamesReconciliationError, match="unesco_boundary_approval"):
        validate_artifact(broken, check_git=False)


def test_review_count_does_not_inflate_registry_gis(artifact: dict) -> None:
    assert artifact["summary"]["represented_evidence_record_count"] == 773
    assert artifact["summary"]["publication_or_registry_gis_count_added"] == 0


def test_serialization_is_deterministic_and_path_free(artifact: dict) -> None:
    raw = ARTIFACT_PATH.read_bytes()
    assert raw == (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw
    assert b"C:\\\\" not in raw and b"visitlibya-local-backups" not in raw


def test_validator_makes_no_writes(artifact: dict) -> None:
    before = ARTIFACT_PATH.read_bytes()
    validate_artifact(artifact, check_git=False)
    assert ARTIFACT_PATH.read_bytes() == before
