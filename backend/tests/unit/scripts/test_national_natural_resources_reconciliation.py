from __future__ import annotations

import copy
import json

import pytest

from scripts.national_natural_resources_reconciliation import (
    ARTIFACT_PATH,
    AUDIT_HASHES,
    COLLECTIONS,
    GEOMETRY_METADATA_MISMATCH_ORDINALS,
    MANDATORY_EXCLUSIONS,
    NATURAL_ROUTING,
    NON_NATURAL_ROUTING,
    OVERLAP_PARTITION,
    NaturalResourcesReconciliationError,
    _expected_review_id,
    validate_artifact,
    validate_serialization,
)


@pytest.fixture
def artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def records(artifact: dict) -> list[dict]:
    return [item for name in COLLECTIONS for item in artifact["collections"][name]]


def by_ordinal(artifact: dict, ordinal: int) -> dict:
    return next(item for item in records(artifact) if item["source_ordinal"] == ordinal)


def test_valid_artifact_passes(artifact: dict) -> None:
    assert validate_artifact(artifact, check_git=False) == {
        "source_ordinals": 945,
        "clean_natural": 876,
        "non_natural_or_mixed": 69,
        "media_references": 32,
        "governed_overlaps": 258,
    }
    validate_serialization()


def test_source_and_external_audit_provenance_are_exact(artifact: dict) -> None:
    source = artifact["source_provenance"]
    assert source["source_sha256"] == "b389136b4d9f8fcc138f48999745b26b899747830489475b70988f679c442f49"
    assert source["source_size_bytes"] == 809652
    assert {item["basename"]: item["sha256"] for item in source["audit_inputs"]} == AUDIT_HASHES
    assert source["registered_source_hash_relationship"] == "IDENTICAL_CONTENT_ALREADY_REGISTERED"
    assert source["source_manifest_change_required"] is False
    assert source["absolute_source_path_recorded"] is False


def test_exact_accounting_and_routing(artifact: dict) -> None:
    assert len(records(artifact)) == 945
    assert {name: len(artifact["collections"][name]) for name in NATURAL_ROUTING} == NATURAL_ROUTING
    assert {name: len(artifact["collections"][name]) for name in NON_NATURAL_ROUTING} == NON_NATURAL_ROUTING
    summary = artifact["summary"]
    assert summary["clean_natural_resource_review_representatives"] == 876
    assert summary["category_scope_mismatch"] == 4
    assert summary["mixed_natural_cultural_review"] == 6
    assert summary["other_non_natural_review"] == 59
    assert summary["safe_duplicate_members"] == 0
    assert summary["coordinate_or_identity_quarantine"] == 0


def test_every_source_ordinal_resolves_exactly_once(artifact: dict) -> None:
    ordinals = [item["source_ordinal"] for item in records(artifact)]
    assert len(ordinals) == len(set(ordinals)) == 945
    assert set(ordinals) == set(range(1, 946))
    resolution = artifact["ordinal_resolution"]
    assert [item["source_ordinal"] for item in resolution] == list(range(1, 946))
    assert len({item["review_id"] for item in resolution}) == 945


def test_review_ids_bind_complete_preserved_evidence(artifact: dict) -> None:
    items = records(artifact)
    assert all(item["review_id"] == _expected_review_id(item) for item in items)
    invalid = copy.deepcopy(artifact)
    invalid["collections"]["WATER_RESOURCES_AND_SPRINGS"][0]["preserved_properties"]["name"] += " changed"
    with pytest.raises(NaturalResourcesReconciliationError, match="deterministic ID mismatch"):
        validate_artifact(invalid, check_git=False)


@pytest.mark.parametrize("ordinal,name", sorted(MANDATORY_EXCLUSIONS.items()))
def test_mandatory_exclusions_are_non_natural_and_non_public(artifact: dict, ordinal: int, name: str) -> None:
    record = by_ordinal(artifact, ordinal)
    assert record["raw_name"] == name
    assert record["proposed_review_collection"] == "CATEGORY_SCOPE_MISMATCH_REVIEW"
    assert record["exclusion_from_natural_display"] is True
    assert record["exclusion_from_natural_media"] is True
    assert all(record not in artifact["collections"][collection] for collection in NATURAL_ROUTING)
    assert record["canonical_destination"] is None
    assert record["publication_approved"] is False
    assert record["canonical_approval"] is False
    assert record["public_visibility_enabled"] is False


def test_mandatory_exclusion_promotion_fails_closed(artifact: dict) -> None:
    invalid = copy.deepcopy(artifact)
    record = invalid["collections"]["CATEGORY_SCOPE_MISMATCH_REVIEW"].pop(0)
    record["proposed_review_collection"] = "WATER_RESOURCES_AND_SPRINGS"
    invalid["collections"]["WATER_RESOURCES_AND_SPRINGS"].append(record)
    with pytest.raises(NaturalResourcesReconciliationError, match="routing count mismatch|mandatory exclusion"):
        validate_artifact(invalid, check_git=False)


def test_overlap_partition_is_mutually_exclusive_and_exact(artifact: dict) -> None:
    items = records(artifact)
    counts = {state: sum(item["overlap_partition"] == state for item in items) for state in OVERLAP_PARTITION}
    assert counts == OVERLAP_PARTITION
    assert sum(counts.values()) == 945
    assert by_ordinal(artifact, 540)["overlap_partition"] == "INFERRED_CURATED_NAME_COORDINATE_OVERLAP_WITHOUT_DIRECT_ID"
    policy = artifact["overlap_policy"]
    assert policy["any_inspected_governed_overlap"] == 258
    assert policy["any_curated_natural_overlap"] == 250
    assert policy["direct_green_mountain_source_id_overlap"] == 180
    assert policy["direct_libyan_sahara_source_id_overlap"] == 69
    assert policy["heritage_source_id_overlap_ordinals_preserved"] == [832, 913]
    assert policy["orthogonal_to_resolution_accounting"] is True


def test_overlap_does_not_grant_authority_or_consolidation(artifact: dict) -> None:
    policy = artifact["overlap_policy"]
    assert policy["creates_duplicate_public_record"] is False
    assert policy["increases_registry_counts"] is False
    assert policy["grants_canonical_identity"] is False
    assert policy["overwrites_curated_data"] is False
    assert policy["authorizes_automatic_consolidation"] is False


def test_duplicate_and_conflict_evidence_remains_unresolved(artifact: dict) -> None:
    review = artifact["duplicate_and_conflict_review"]
    assert review["duplicate_raw_id_groups"] == []
    assert review["exact_complete_feature_duplicate_groups"] == []
    assert review["automatic_consolidation_performed"] is False
    assert [item["source_ordinals"] for item in review["normalized_name_exact_coordinate_groups"]] == [[539, 540], [889, 890]]
    assert review["different_name_identical_coordinate_groups"] == [{
        "coordinate": [21.5163889, 32.84],
        "names": ["سبخة أم سيد", "سبخة الحنية"],
        "source_ordinals": [597, 601],
    }]
    assert len(review["same_name_different_coordinate_groups"]) == 76
    assert {distance: len(review["near_coordinate_candidates"][distance]) for distance in ("10", "25", "100")} == {"10": 22, "25": 24, "100": 39}


def test_all_geometry_is_valid_preserved_point_evidence(artifact: dict) -> None:
    for item in records(artifact):
        assert item["geometry"]["type"] == "Point"
        assert item["geometry"]["coordinates"] == item["coordinate"]
        assert item["geometry_valid"] is True
        assert item["libya_plausible"] is True
    assert artifact["spatial_quality"]["automatic_coordinate_repairs"] == 0
    assert artifact["spatial_quality"]["all_source_geometries_preserved_without_repair"] is True


def test_geometry_metadata_mismatches_are_explicit(artifact: dict) -> None:
    flagged = {item["source_ordinal"] for item in records(artifact) if item["source_geometry_metadata_mismatch"]}
    assert flagged == GEOMETRY_METADATA_MISMATCH_ORDINALS
    assert artifact["spatial_quality"]["source_geometry_metadata_mismatch_ordinals"] == sorted(GEOMETRY_METADATA_MISMATCH_ORDINALS)


def test_geometry_metadata_flag_drift_fails_closed(artifact: dict) -> None:
    invalid = copy.deepcopy(artifact)
    by_ordinal(invalid, 579)["source_geometry_metadata_mismatch"] = False
    with pytest.raises(NaturalResourcesReconciliationError, match="geometry metadata mismatch flag drift"):
        validate_artifact(invalid, check_git=False)


def test_media_references_are_preserved_but_never_eligible(artifact: dict) -> None:
    references = [media for item in records(artifact) for media in item["media_references"]]
    assert len(references) == 32
    assert all(media["repository_asset_available"] is False for media in references)
    assert all(media["publication_media_eligible"] is False for media in references)
    assert all(media["ownership_or_usage_rights_verified"] is False for media in references)
    assert artifact["media_policy"]["enriched_or_linked_records"] == 21
    assert artifact["media_policy"]["records_with_nonempty_images"] == 14
    assert artifact["media_policy"]["repository_missing_references"] == 32
    assert len(artifact["media_policy"]["duplicate_media_linkage_groups"]) == 4


def test_media_eligibility_fails_closed(artifact: dict) -> None:
    invalid = copy.deepcopy(artifact)
    next(item for item in records(invalid) if item["media_references"])["media_references"][0]["publication_media_eligible"] = True
    with pytest.raises(NaturalResourcesReconciliationError, match="media authority granted"):
        validate_artifact(invalid, check_git=False)


def test_all_source_properties_and_status_are_preserved_without_approval(artifact: dict) -> None:
    assert len(artifact["source_field_profile"]["property_keys"]) == 32
    assert len(artifact["source_field_profile"]["field_completeness"]) == 32
    assert artifact["source_field_profile"]["raw_status_is_source_text_not_approval"] is True
    assert artifact["source_field_profile"]["raw_id_is_sole_deterministic_identity"] is False
    ready = [item for item in records(artifact) if item["raw_status"] == "جاهز مبدئياً"]
    assert len(ready) == 921
    assert all(item["source_status_is_approval"] is False for item in ready)


def test_all_record_governance_remains_unresolved(artifact: dict) -> None:
    for item in records(artifact):
        assert item["publication_approved"] is False
        assert item["canonical_approval"] is False
        assert item["public_visibility_enabled"] is False
        assert item["institutional_review_status"] == "UNRESOLVED"
        assert item["canonical_destination"] is None
        assert item["resolution"] == "UNRESOLVED_NO_AUTOMATIC_REPAIR"


@pytest.mark.parametrize("field", ["publication_approved", "canonical_approval", "public_visibility_enabled"])
def test_record_approval_or_visibility_fails_closed(artifact: dict, field: str) -> None:
    invalid = copy.deepcopy(artifact)
    invalid["collections"]["WATER_RESOURCES_AND_SPRINGS"][0][field] = True
    with pytest.raises(NaturalResourcesReconciliationError, match=field):
        validate_artifact(invalid, check_git=False)


def test_publication_registry_and_curated_counts_are_unchanged(artifact: dict) -> None:
    invariants = artifact["publication_and_registry_invariants"]
    assert invariants["green_mountain_curated_features"] == 180
    assert invariants["libyan_sahara_curated_features"] == 69
    assert invariants["curated_natural_frontend_total"] == 249
    assert invariants["publication_oriented_national_gis_count"] == 214
    assert invariants["review_records_added_to_publication_count"] == 0
    assert invariants["registry_modified"] is False
    assert invariants["source_manifest_modified"] is False
    assert invariants["approval_ledger_event_created"] is False


def test_artifact_has_portable_utf8_serialization() -> None:
    raw = ARTIFACT_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert b"\r\n" not in raw
    assert b"visitlibya-local-backups" not in raw
    assert b"visitlibya-gis-sources" not in raw
