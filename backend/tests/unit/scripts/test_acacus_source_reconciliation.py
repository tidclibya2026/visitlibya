from __future__ import annotations

import copy
import json

import pytest

from scripts.acacus_source_reconciliation import (
    ARTIFACT_PATH, AUDIT_HASHES, COLLECTIONS, EXPECTED_ROUTING,
    AcacusReconciliationError, _review_id, validate_artifact, validate_serialization,
)


@pytest.fixture
def artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def clean(artifact: dict) -> list[dict]:
    return [item for name in COLLECTIONS for item in artifact["collections"][name]]


def duplicates(artifact: dict) -> list[dict]:
    return [item for group in artifact["safe_duplicate_groups"] for item in group["duplicate_members"]]


def test_valid_artifact_passes(artifact: dict) -> None:
    assert validate_artifact(artifact, check_git=False) == {"source_ordinals": 430, "clean": 360, "duplicate_members": 66, "quarantined": 4, "reconciled_review_records": 364}
    validate_serialization()


def test_source_and_audit_provenance_are_exact(artifact: dict) -> None:
    source = artifact["source_provenance"]
    assert source["source_sha256"] == "641ab45b3ace5e77eae78e63931b08fb925f2494a536f3736d74e01bf5ed2988"
    assert source["source_size_bytes"] == 605606
    assert {item["basename"]: item["sha256"] for item in source["audit_inputs"]} == AUDIT_HASHES
    assert source["earlier_akakuas_gdb_overrides_kml"] is False
    assert source["absolute_source_path_recorded"] is False


def test_accounting_and_routing_are_exact(artifact: dict) -> None:
    assert len(clean(artifact)) == 360
    assert len(duplicates(artifact)) == 66
    assert len(artifact["quarantined_records"]) == 4
    assert {name: len(artifact["collections"][name]) for name in COLLECTIONS} == EXPECTED_ROUTING
    assert artifact["summary"]["reconciled_review_record_count"] == 364


def test_every_source_ordinal_resolves_exactly_once(artifact: dict) -> None:
    records = clean(artifact) + duplicates(artifact) + artifact["quarantined_records"]
    ordinals = [item["source_ordinal"] for item in records]
    assert len(ordinals) == len(set(ordinals)) == 430
    assert set(ordinals) == set(range(1, 431))


def test_deterministic_unique_review_ids(artifact: dict) -> None:
    records = clean(artifact) + duplicates(artifact) + artifact["quarantined_records"]
    assert len({item["review_id"] for item in records}) == 430
    for item in clean(artifact):
        assert item["review_id"] == _review_id("record", item["source_record"])


def test_mathendous_is_cross_destination_quarantine_only(artifact: dict) -> None:
    assert all(item["source_ordinal"] != 23 for item in clean(artifact))
    matches = [item for item in artifact["quarantined_records"] if item["source_ordinal"] == 23]
    assert len(matches) == 1
    item = matches[0]
    assert item["quarantine_reason"] == "CROSS_DESTINATION_SCOPE_AND_COORDINATE_CONFLICT"
    review = item["cross_destination_review"]
    assert review["proposed_destination_scope"] == "UBARI_MESSAK_REVIEW"
    assert review["proposed_heritage_theme"] == "ROCK_ART_AND_INSCRIPTIONS"
    assert review["heritage_priority"] == "HIGH"
    assert review["notable_subject"] == "نقش القطتين المتصارعتين"
    assert review["canonical_destination_assignment"] is None
    assert review["resolution_status"] == "UNRESOLVED_NO_AUTOMATIC_REPAIR"


def test_mathendous_coordinates_are_preserved_not_repaired(artifact: dict) -> None:
    item = next(item for item in artifact["quarantined_records"] if item["source_ordinal"] == 23)
    assert item["source_record"]["complete_coordinates"][0][:2] == [10.516772, 24.957273]
    evidence = item["cross_destination_review"]["coordinate_conflict_evidence"]
    assert evidence["preserved_source_x"] == 12.245440
    assert evidence["preserved_source_y"] == 26103950
    assert evidence["possible_decimal_interpretation"] == [12.245440, 26.103950]
    assert evidence["possible_interpretation_status"] == "REVIEW_EVIDENCE_ONLY_NOT_APPLIED"
    assert evidence["automatic_coordinate_repair_performed"] is False


def test_fighting_cats_evidence_is_not_publication_copy(artifact: dict) -> None:
    item = next(item for item in artifact["quarantined_records"] if item["source_ordinal"] == 23)
    review = item["cross_destination_review"]
    assert review["notable_subject"] == "نقش القطتين المتصارعتين"
    assert review["notable_subject_publication_approved"] is False
    assert review["publication_approved"] is review["canonical_approval"] is review["public_visibility_enabled"] is False


def test_uan_muhuggiag_review_metadata_is_proposed_only(artifact: dict) -> None:
    item = next(item for item in artifact["collections"]["CAVES_AND_SHELTERS"] if item["source_ordinal"] == 191)
    review = item["proposed_identity_review"]
    assert item["source_record"]["source_name"] == "كهف وان موهجاج"
    assert review["proposed_name_en"] == "Uan Muhuggiag"
    assert review["identity_verification_status"] == "REQUIRED"
    assert review["primary_routing_unchanged"] == "CAVES_AND_SHELTERS"
    assert review["proposed_cross_domain_review_tags"] == ["ARCHAEOLOGY", "CULTURAL_HERITAGE", "ROCK_ART_AND_INSCRIPTIONS", "MUMMY_DISCOVERY_ASSOCIATION"]
    assert review["canonical_classification_granted"] is False
    assert review["publication_approved"] is review["canonical_approval"] is review["public_visibility_enabled"] is False


def test_all_four_quarantine_reasons_are_exact(artifact: dict) -> None:
    assert {item["quarantine_reason"] for item in artifact["quarantined_records"]} == {"CROSS_DESTINATION_SCOPE_AND_COORDINATE_CONFLICT", "MISSING_GEOMETRY", "MISSING_IDENTITY_AND_GEOMETRY", "EXTERNAL_ADMINISTRATIVE_POLYGON_UNRESOLVED_SCOPE"}
    assert next(item for item in artifact["quarantined_records"] if item["source_ordinal"] == 199)["quarantine_reason"] == "EXTERNAL_ADMINISTRATIVE_POLYGON_UNRESOLVED_SCOPE"
    assert artifact["governance"]["authoritative_acacus_boundary_present"] is False


def test_identity_conflicts_remain_separate(artifact: dict) -> None:
    assert {tuple(item["source_ordinals"]) for item in artifact["identity_conflicts"]} == {(154, 396), (34, 278)}
    assert all(item["status"] == "SAME_COORDINATE_DIFFERENT_NAME_REVIEW_REQUIRED" for item in artifact["identity_conflicts"])


def test_local_hotels_remain_separate_and_tripoli_is_absent(artifact: dict) -> None:
    hotels = [item for item in clean(artifact) if item["source_ordinal"] in {181, 423}]
    assert len(hotels) == 2
    assert {tuple(item["source_record"]["complete_coordinates"][0][:2]) for item in hotels} == {(10.18259, 24.95834), (10.18258, 24.95834)}
    assert artifact["hotel_identity_safeguard"]["tripoli_record_present"] is False
    assert artifact["hotel_identity_safeguard"]["name_similarity_establishes_identity"] is False


def test_every_record_is_fail_closed(artifact: dict) -> None:
    records = clean(artifact) + duplicates(artifact) + artifact["quarantined_records"]
    assert all(item["publication_approved"] is False and item["canonical_approval"] is False and item["public_visibility_enabled"] is False and item["institutional_review_status"] == "UNRESOLVED" for item in records)


@pytest.mark.parametrize("field", ["publication_approved", "canonical_approval", "public_visibility_enabled"])
def test_true_governance_field_fails(artifact: dict, field: str) -> None:
    broken = copy.deepcopy(artifact)
    broken["collections"]["ROCK_ART_AND_INSCRIPTIONS"][0][field] = True
    with pytest.raises(AcacusReconciliationError, match=field):
        validate_artifact(broken, check_git=False)


def test_review_records_do_not_inflate_publication_gis(artifact: dict) -> None:
    assert artifact["summary"]["publication_or_registry_gis_count_added"] == 0
    assert artifact["governance"]["runtime_source"] is False


def test_serialization_is_deterministic_utf8_and_path_free(artifact: dict) -> None:
    raw = ARTIFACT_PATH.read_bytes()
    assert raw == (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw
    assert b"C:\\\\" not in raw and b"visitlibya-local-backups" not in raw and b"visitlibya-gis-sources" not in raw


def test_validator_makes_no_writes(artifact: dict) -> None:
    before = ARTIFACT_PATH.read_bytes()
    validate_artifact(artifact, check_git=False)
    assert ARTIFACT_PATH.read_bytes() == before
