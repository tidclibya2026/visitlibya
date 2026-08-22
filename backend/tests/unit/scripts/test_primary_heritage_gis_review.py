from __future__ import annotations

import copy
import json

import pytest

from scripts.primary_heritage_gis_review import (
    CANONICAL_REVIEW_PATH,
    COORDINATES_PATH,
    REGISTRY_PATH,
    ROOT,
    SCOPE_PATHS,
    HeritageScopeValidationError,
    build_review_inventory,
    validate_repository,
    validate_scope_payloads,
)


@pytest.fixture
def payloads() -> tuple[list[dict], dict, dict, dict]:
    scopes = [json.loads((ROOT / path).read_text(encoding="utf-8")) for path in SCOPE_PATHS]
    coordinates = json.loads((ROOT / COORDINATES_PATH).read_text(encoding="utf-8"))
    canonical = json.loads((ROOT / CANONICAL_REVIEW_PATH).read_text(encoding="utf-8"))
    registry = json.loads((ROOT / REGISTRY_PATH).read_text(encoding="utf-8"))
    return scopes, coordinates, canonical, registry


def validate(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    validate_scope_payloads(*payloads, root=ROOT)


def test_both_valid_scope_files_pass(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    validate(payloads)
    assert validate_repository(check_git=False)["scope_count"] == 2


def test_review_inventory_counts_provenance_and_classification(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    scopes = {item["canonical_destination_slug"]: item for item in payloads[0]}
    leptis = scopes["leptis-magna"]["review_inventory"]
    sabratha = scopes["sabratha"]["review_inventory"]
    assert len(leptis["records"]) == 51
    assert len(sabratha["records"]) == 39
    assert sum(len(item["review_inventory"]["records"]) for item in scopes.values()) == 90
    assert leptis["source_provenance"]["source_database"] == "points_world_heritage.gdb"
    assert leptis["source_provenance"]["source_artifact_sha256"] == "51be7a822a221e3ff4170c2f0104a83a9a99fc3b3ea916ca3a57a7723fd6f281"
    assert sabratha["source_provenance"]["source_artifact_sha256"] == "ffb3612844670770fafedf559860827a37b2ee556ee28794c94a6d62652de5d3"
    assert not leptis["source_provenance"]["absolute_source_path_recorded"]
    assert sum(leptis["classification_counts"].values()) == 51
    assert sum(sabratha["classification_counts"].values()) == 39


def test_leptis_required_quality_findings(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    leptis = payloads[0][0]["review_inventory"]
    assert leptis["quality_summary"] == {
        "record_count": 51,
        "unique_nonblank_name_count": 49,
        "unique_coordinate_count": 49,
        "blank_popupinfo_count": 49,
        "blank_en_name_count": 33,
        "blank_photo_count": 42,
        "parseable_photo_attachment_json_count": 4,
        "truncated_photo_attachment_json_count": 5,
    }
    by_name = {}
    for item in leptis["records"]:
        by_name.setdefault(item["source_name"].strip(), []).append(item)
    museums = by_name["متحف الفسيفساء"]
    assert len(museums) == 2
    assert museums[0]["source_geometry"] == museums[1]["source_geometry"]
    assert all("DUPLICATE_EXACT_NAME_AND_COORDINATE_REVIEW" in item["quality_flags"] for item in museums)
    jupiter = [by_name["معبد جوبيتير دوليكينوس"][0], by_name["معبد جوبيتير"][0]]
    assert jupiter[0]["source_geometry"] == jupiter[1]["source_geometry"]
    assert all("EXACT_COORDINATE_IDENTITY_CONFLICT_REVIEW" in item["quality_flags"] for item in jupiter)
    assert sum(item["source_attributes"]["objectid"] == 0 for item in leptis["records"]) == 2
    assert "ATTACHMENT_JSON_IN_EN_NAME_FIELD_REVIEW" in by_name["قوس الإمبراطور تراجان"][0]["quality_flags"]
    assert "MEDIA_IDENTITY_CONFLICT_REVIEW" in by_name["قوس سبتيموس سفيروس"][0]["quality_flags"]


def test_sabratha_required_quality_findings(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    sabratha = payloads[0][1]["review_inventory"]
    assert sabratha["quality_summary"] == {
        "record_count": 39,
        "unique_nonblank_name_count": 36,
        "unique_coordinate_count": 39,
        "blank_description_count": 39,
        "geometry_xy_match_within_tolerance_count": 39,
    }
    by_name = {}
    for item in sabratha["records"]:
        by_name.setdefault(item["source_name"].strip(), []).append(item)
    for name in ("معبد سيرابيس", "حوض المعمودية", "معبد ايزيس وإيزوريس"):
        assert len(by_name[name]) == 2
        assert all("REPEATED_NAME_DISTINCT_COORDINATES_REVIEW" in item["quality_flags"] for item in by_name[name])
    incomplete = by_name["Serapaeum (Sabratha"][0]
    assert incomplete["source_name"] == "Serapaeum (Sabratha"
    assert incomplete["proposed_normalized_name"] == "Serapaeum (Sabratha)"
    assert "INCOMPLETE_SOURCE_NAME_REVIEW" in incomplete["quality_flags"]
    assert all("NEARBY_DISTINCT_NAMES_REVIEW" in by_name[name][0]["quality_flags"] for name in ("حمامات أوفانيوس", "حمامات ريجيو السابع"))


def test_inventory_ids_are_unique_and_deterministic(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    for scope in payloads[0]:
        inventory = scope["review_inventory"]
        provenance = inventory["source_provenance"]
        export = {
            "geometryType": "esriGeometryPoint",
            "spatialReference": {"wkid": 4326},
            "fields": [{"name": value} for value in provenance["source_field_names"]],
            "features": [
                {
                    "attributes": item["source_attributes"],
                    "geometry": {"x": item["source_geometry"]["longitude"], "y": item["source_geometry"]["latitude"]},
                }
                for item in inventory["records"]
            ],
        }
        rebuilt = build_review_inventory(scope["canonical_destination_slug"], export, provenance["source_artifact_basename"], provenance["source_artifact_sha256"])
        ids = [item["review_feature_id"] for item in inventory["records"]]
        assert len(ids) == len(set(ids))
        assert rebuilt == inventory


def test_inventory_remains_distinct_from_anchor_and_boundary(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    for scope in payloads[0]:
        assert scope["site_anchor"]["anchor_role"] == "REVIEWED_CANONICAL_DESTINATION_SITE_ANCHOR"
        assert scope["review_inventory"]["status"] == "REVIEW_ONLY_POINT_INVENTORY_NOT_RUNTIME_SOURCE"
        assert scope["review_inventory"]["boundary_authority"] is False
        assert scope["boundary"]["geometry_present"] is False
        assert scope["boundary"]["status"] == "AUTHORITATIVE_BOUNDARY_REQUIRED"


def test_inventory_invalid_coordinate_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["review_inventory"]["records"][0]["source_geometry"]["longitude"] = float("inf")
    with pytest.raises(HeritageScopeValidationError, match="coordinates must be finite"):
        validate(broken)


def test_inventory_provenance_hash_mismatch_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["review_inventory"]["source_provenance"]["source_artifact_sha256"] = "0" * 64
    with pytest.raises(HeritageScopeValidationError, match="source hash mismatch"):
        validate(broken)


def test_inventory_publication_or_visibility_cannot_be_enabled(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    for field in ("canonical_approval", "publication_approved", "public_visibility_enabled"):
        broken = copy.deepcopy(payloads)
        broken[0][0]["review_inventory"]["records"][0][field] = True
        with pytest.raises(HeritageScopeValidationError, match=field):
            validate(broken)


def test_inventory_institutional_review_remains_unresolved(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][1]["review_inventory"]["records"][0]["institutional_review_status"] = "APPROVED"
    with pytest.raises(HeritageScopeValidationError, match="institutional review"):
        validate(broken)


def test_missing_scope_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0].pop()
    with pytest.raises(HeritageScopeValidationError, match="exactly two"):
        validate(broken)


def test_duplicate_scope_id_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][1]["scope_id"] = broken[0][0]["scope_id"]
    with pytest.raises(HeritageScopeValidationError, match="duplicate scope ID"):
        validate(broken)


def test_wrong_canonical_slug_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["canonical_destination_slug"] = "cyrene"
    with pytest.raises(HeritageScopeValidationError, match="canonical-slug order"):
        validate(broken)


@pytest.mark.parametrize("value", [None, "32.0"])
def test_invalid_or_missing_anchor_coordinate_fails(payloads: tuple[list[dict], dict, dict, dict], value: object) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["site_anchor"]["latitude"] = value
    with pytest.raises(HeritageScopeValidationError, match="finite numeric"):
        validate(broken)


def test_out_of_libya_anchor_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["site_anchor"]["longitude"] = 40.0
    with pytest.raises(HeritageScopeValidationError, match="outside Libya"):
        validate(broken)


def test_incorrect_coordinate_provenance_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["provenance"]["coordinate_source"]["source_reference"] = "invented"
    with pytest.raises(HeritageScopeValidationError, match="provenance reference"):
        validate(broken)


def test_anchor_cannot_be_boundary_centroid(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["site_anchor"]["anchor_role"] = "BOUNDARY_CENTROID"
    broken[0][0]["site_anchor"]["is_boundary_centroid"] = True
    with pytest.raises(HeritageScopeValidationError, match="relabeled role"):
        validate(broken)


def test_fabricated_boundary_geometry_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["boundary"].update({"geometry_present": True, "geometry_type": "Polygon", "source": "guessed"})
    with pytest.raises(HeritageScopeValidationError, match="fabricated boundary"):
        validate(broken)


def test_unsupported_boundary_status_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["boundary"]["status"] = "APPROVED"
    with pytest.raises(HeritageScopeValidationError, match="unsupported boundary status"):
        validate(broken)


def test_unsupported_taxonomy_category_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["layer_taxonomy"][0]["category"] = "TEMPLE"
    with pytest.raises(HeritageScopeValidationError, match="taxonomy is unsupported"):
        validate(broken)


def test_invalid_taxonomy_geometry_type_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["layer_taxonomy"][0]["allowable_geometry_types"] = ["Circle"]
    with pytest.raises(HeritageScopeValidationError, match="invalid geometry type"):
        validate(broken)


def _candidate() -> dict:
    return {
        "source_feature_id": "review-candidate-1",
        "destination_slug": "leptis-magna",
        "feature_category": "OTHER_REVIEW_REQUIRED",
        "source_path": "backend/data/gis/canonical-destination-coordinate-review.json",
        "selection_reason": "Repository review candidate retained for human destination-membership review.",
        "review_required": True,
        "publication_approved": False,
    }


def test_duplicate_candidate_source_id_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    candidate = _candidate()
    broken[0][0]["candidate_features"] = [candidate, copy.deepcopy(candidate)]
    broken[0][0]["summary"]["candidate_feature_count"] = 2
    with pytest.raises(HeritageScopeValidationError, match="duplicate candidate"):
        validate(broken)


def test_candidate_without_evidence_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    candidate = _candidate()
    candidate["selection_reason"] = ""
    broken[0][0]["candidate_features"] = [candidate]
    broken[0][0]["summary"]["candidate_feature_count"] = 1
    with pytest.raises(HeritageScopeValidationError, match="lacks evidence"):
        validate(broken)


def test_candidate_publication_approval_true_fails(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    candidate = _candidate()
    candidate["publication_approved"] = True
    broken[0][0]["candidate_features"] = [candidate]
    broken[0][0]["summary"]["candidate_feature_count"] = 1
    with pytest.raises(HeritageScopeValidationError, match="grants publication approval"):
        validate(broken)


def test_media_cannot_grant_coordinate_authority(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["media_evidence"][0]["grants_spatial_authority"] = True
    with pytest.raises(HeritageScopeValidationError, match="media grants coordinate"):
        validate(broken)


def test_scope_cannot_claim_runtime_eligibility(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    broken = copy.deepcopy(payloads)
    broken[0][0]["publication_governance"]["runtime_eligible"] = True
    with pytest.raises(HeritageScopeValidationError, match="runtime_eligible"):
        validate(broken)


def test_empty_candidate_arrays_pass(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    assert all(scope["candidate_features"] == [] for scope in payloads[0])
    validate(payloads)


def test_registry_counts_priorities_and_scope_distinction(payloads: tuple[list[dict], dict, dict, dict]) -> None:
    registry = payloads[3]
    assert len(registry["records"]) == 15
    records = {item["current_canonical_slug"]: item for item in registry["records"]}
    for slug in ("leptis-magna", "sabratha"):
        assert records[slug]["development_priority_tier"] == "PRIMARY"
        assert records[slug]["gis_scope_contract_present"] is True
        assert records[slug]["gis_layer_present"] is False
        assert records[slug]["gis_record_count"] == 0
    assert sum(item["gis_record_count"] for item in registry["records"]) == 214


def test_ledger_protected_files_and_heritage_exclusions() -> None:
    assert (ROOT / "backend/data/governance/publication-approval-ledger.jsonl").read_bytes() == b""
    natural = (ROOT / "assets/js/data/natural-tourism-layers.js").read_text(encoding="utf-8")
    assert "sourceFeatureId: 832" not in natural
    assert "sourceFeatureId: 913" not in natural
    assert validate_repository(check_git=True)["scoped_gis_record_count"] == 214


def test_scope_files_are_utf8_without_bom_with_one_newline() -> None:
    for path in SCOPE_PATHS:
        raw = (ROOT / path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")


def test_validator_makes_no_writes() -> None:
    paths = [ROOT / path for path in (*SCOPE_PATHS, REGISTRY_PATH, COORDINATES_PATH, CANONICAL_REVIEW_PATH)]
    before = {path: path.read_bytes() for path in paths}
    validate_repository(check_git=False)
    assert before == {path: path.read_bytes() for path in paths}
