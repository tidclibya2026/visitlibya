from __future__ import annotations

import copy
import json

import pytest

from scripts.old_tripoli_source_reconciliation import (
    ARTIFACT_PATH,
    AUDIT_HASHES,
    COLLECTIONS,
    EXPECTED_ROUTING,
    OldTripoliReconciliationError,
    _expected_review_id,
    validate_artifact,
    validate_serialization,
)


@pytest.fixture
def artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def records(artifact: dict) -> list[dict]:
    return [item for name in COLLECTIONS for item in artifact["collections"][name]]


def test_valid_artifact_passes(artifact: dict) -> None:
    assert validate_artifact(artifact, check_git=False) == {
        "source_ordinals": 430,
        "site_oriented": 145,
        "contextual_network": 285,
        "technical_quarantine": 0,
        "safe_duplicate_members": 0,
    }
    validate_serialization()


def test_source_and_corrected_audit_provenance_are_exact(artifact: dict) -> None:
    source = artifact["source_provenance"]
    assert source["source_sha256"] == "26ffc9519ebccfaafbd029e070dd21e736c0f0bc839b36231668792d6866eab5"
    assert source["source_size_bytes"] == 967226
    assert {item["basename"]: item["sha256"] for item in source["audit_inputs"]} == AUDIT_HASHES
    assert source["absolute_source_path_recorded"] is False


def test_exact_accounting_and_routing(artifact: dict) -> None:
    assert len(records(artifact)) == 430
    assert {name: len(artifact["collections"][name]) for name in COLLECTIONS} == EXPECTED_ROUTING
    summary = artifact["summary"]
    assert summary["site_oriented_review_geometry_count"] == 145
    assert summary["contextual_network_geometry_count"] == 285
    assert summary["technical_quarantine_count"] == 0
    assert summary["safe_duplicate_member_count"] == 0


def test_every_source_ordinal_resolves_exactly_once(artifact: dict) -> None:
    ordinals = [item["source_ordinal"] for item in records(artifact)]
    assert len(ordinals) == len(set(ordinals)) == 430
    assert set(ordinals) == set(range(1, 431))
    assert [item["source_ordinal"] for item in artifact["ordinal_resolution"]] == list(range(1, 431))


def test_review_ids_are_deterministic_and_unique(artifact: dict) -> None:
    items = records(artifact)
    assert len({item["review_id"] for item in items}) == 430
    assert all(item["review_id"] == _expected_review_id(item) for item in items)


def test_geometry_and_line_name_counts(artifact: dict) -> None:
    items = records(artifact)
    assert sum(item["geometry_type"] == "Point" for item in items) == 135
    assert sum(item["geometry_type"] == "Polygon" for item in items) == 10
    lines = [item for item in items if item["geometry_type"] == "LineString"]
    assert len(lines) == 285
    assert sum(bool(item["raw_name"].strip()) for item in lines) == 49
    assert sum(not item["raw_name"].strip() for item in lines) == 236


def test_all_lines_are_contextual_not_proven_historic(artifact: dict) -> None:
    lines = [item for item in records(artifact) if item["geometry_type"] == "LineString"]
    assert all(item["proposed_review_collection"] == "CONTEXTUAL_URBAN_NETWORK_REVIEW" for item in lines)
    prohibited = "HISTORIC_URBAN_LINES" + "_AND_NETWORKS"
    assert prohibited not in json.dumps(artifact, ensure_ascii=False)
    policy = artifact["line_network_policy"]
    assert policy["historic_or_heritage_network_claimed"] is False
    assert policy["official_or_visitor_route_claimed"] is False
    assert "OSM_FIELDS" in policy["prohibited_inference_bases"]


def test_line_historic_classification_fails_closed(artifact: dict) -> None:
    invalid = copy.deepcopy(artifact)
    item = invalid["collections"]["CONTEXTUAL_URBAN_NETWORK_REVIEW"][0]
    item["proposed_review_collection"] = "HISTORIC_URBAN_LINES" + "_AND_NETWORKS"
    with pytest.raises(OldTripoliReconciliationError, match="unsupported semantic routing|prohibited historic"):
        validate_artifact(invalid, check_git=False)


def test_polygons_remain_non_authoritative_review_areas(artifact: dict) -> None:
    polygons = [item for item in records(artifact) if item["geometry_type"] == "Polygon"]
    assert len(polygons) == 10
    assert all(item["proposed_review_collection"] == "REVIEW_POLYGONS_AND_AREAS" for item in polygons)
    assert artifact["polygon_policy"] == {
        "review_collection": "REVIEW_POLYGONS_AND_AREAS",
        "authoritative_old_tripoli_boundary": False,
        "authoritative_footprint": False,
        "public_boundary": False,
        "boundary_derived_from_geometry_envelope_or_distribution": False,
    }
    assert artifact["polygon_overlap_review_candidates"][0]["source_ordinals"] == [136, 137]


def test_authoritative_polygon_claim_fails_closed(artifact: dict) -> None:
    invalid = copy.deepcopy(artifact)
    invalid["polygon_policy"]["authoritative_old_tripoli_boundary"] = True
    with pytest.raises(OldTripoliReconciliationError, match="polygon authority"):
        validate_artifact(invalid, check_git=False)


def test_exact_coordinate_identity_conflict_remains_separate(artifact: dict) -> None:
    conflict = artifact["identity_conflicts"]
    assert len(conflict) == 1
    assert conflict[0]["source_ordinals"] == [23, 50]
    by_ordinal = {item["source_ordinal"]: item for item in records(artifact)}
    assert by_ordinal[23]["raw_name"].strip() == "الساحة ميدان الشهداء"
    assert by_ordinal[50]["raw_name"].strip() == "الساحة الشهداء"
    assert by_ordinal[23]["review_id"] != by_ordinal[50]["review_id"]


def test_review_groups_and_near_pairs_are_preserved(artifact: dict) -> None:
    assert len(artifact["same_name_different_geometry_groups"]) == 15
    assert len(artifact["near_point_review_pairs"]) == 30
    assert artifact["safe_duplicate_members"] == []


@pytest.mark.parametrize(
    ("proposed", "source_fragment"),
    [
        ("برج القديس جورج", 'برج "القديس جورج"'),
        ("الكنيسة الأرثوذكسية", "الكنيسة الأرتذوكسية"),
        ("الحنفية العثمانية", "الحنفية (الشيشمة) العثمانية"),
    ],
)
def test_key_identity_normalization_preserves_source(artifact: dict, proposed: str, source_fragment: str) -> None:
    review = next(item for item in artifact["key_identity_review"] if item["requested_identity"] == proposed)
    assert len(review["matches"]) == 1
    assert source_fragment in review["matches"][0]["raw_name"]
    assert review["matches"][0]["identity_match_status"] == "SOURCE_VARIANT_REQUIRES_IDENTITY_REVIEW"


def test_every_record_remains_unapproved_and_unassigned(artifact: dict) -> None:
    for item in records(artifact):
        assert item["publication_approved"] is False
        assert item["canonical_approval"] is False
        assert item["public_visibility_enabled"] is False
        assert item["institutional_review_status"] == "UNRESOLVED"
        assert item["canonical_destination"] is None
        assert item["resolution"] == "UNRESOLVED_NO_AUTOMATIC_REPAIR"


def test_record_publication_approval_fails_closed(artifact: dict) -> None:
    invalid = copy.deepcopy(artifact)
    invalid["collections"]["RELIGIOUS_HERITAGE"][0]["publication_approved"] = True
    with pytest.raises(OldTripoliReconciliationError, match="grants publication_approved"):
        validate_artifact(invalid, check_git=False)


def test_nested_identity_model_creates_no_runtime_destination(artifact: dict) -> None:
    identity = artifact["identity_model"]
    assert identity["relationship"] == "tripoli CONTAINS_HERITAGE_DESTINATION old-tripoli"
    assert identity["identities_merged"] is False
    assert identity["coordinate_or_boundary_inheritance"] is False
    assert identity["old_tripoli"]["public_runtime_identity_created"] is False


def test_media_is_evidence_without_rights_or_authority(artifact: dict) -> None:
    media = artifact["media_policy"]
    assert media["records_with_media_references"] == 114
    assert media["source_evidence_only"] is True
    assert media["ownership_or_usage_rights_granted"] is False
    assert media["identity_or_spatial_authority_granted"] is False
    assert media["publication_permission_granted"] is False
    assert media["media_copied_to_public_assets"] is False


def test_registry_accounting_does_not_inflate_publication_gis(artifact: dict) -> None:
    assert artifact["summary"]["publication_or_registry_gis_count_added"] == 0
    validate_artifact(artifact, check_git=False)


def test_serialization_is_deterministic_utf8_and_portable(artifact: dict) -> None:
    expected = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    assert ARTIFACT_PATH.read_bytes() == expected.encode("utf-8")
    assert "C:\\" not in expected
    assert "visitlibya-local-backups" not in expected
    assert "visitlibya-gis-sources" not in expected
