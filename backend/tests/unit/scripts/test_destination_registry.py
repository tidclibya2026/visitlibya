from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.destination_registry import REGISTRY_PATH, RegistryValidationError, validate_registry


ROOT = Path(__file__).resolve().parents[4]
PROTECTED_ARTIFACTS = [
    "assets/js/data/natural-tourism-layers.js",
    "assets/js/data/curated-destinations.js",
    "backend/data/dev/destinations.json",
    "backend/data/governance/publication-policy.json",
    "backend/data/governance/publication-approval-ledger.jsonl",
    "backend/data/governance/legacy-publication-baseline.json",
    "backend/data/governance/publication-generation-manifest.json",
]


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def validate_modified(tmp_path: Path, registry: dict) -> None:
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate_registry(ROOT, path)


def record(registry: dict, key: str) -> dict:
    return next(item for item in registry["records"] if item["coverage_unit_key"] == key)


def test_valid_registry_passes() -> None:
    assert validate_registry()["records"] == 15


def test_missing_record_fails(tmp_path: Path, registry: dict) -> None:
    registry["records"].pop()
    with pytest.raises(RegistryValidationError, match="exactly fifteen"):
        validate_modified(tmp_path, registry)


def test_priority_tier_counts_are_exact(registry: dict) -> None:
    tiers = [item["development_priority_tier"] for item in registry["records"]]
    assert tiers.count("PRIMARY") == 9
    assert tiers.count("COMPLEMENTARY") == 6


def test_unknown_priority_tier_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "tripoli")["development_priority_tier"] = "URGENT"
    with pytest.raises(RegistryValidationError, match="development priority tier"):
        validate_modified(tmp_path, registry)


def test_wrong_priority_tier_counts_fail(tmp_path: Path, registry: dict) -> None:
    record(registry, "waddan")["development_priority_tier"] = "PRIMARY"
    with pytest.raises(RegistryValidationError, match="exactly nine PRIMARY"):
        validate_modified(tmp_path, registry)


def test_priority_does_not_imply_institutional_approval(registry: dict) -> None:
    assert all(item["institutional_publication_approved"] is False for item in registry["records"])
    assert registry["policy"]["development_priority_grants_approval"] is False


def test_priority_does_not_imply_runtime_eligibility(registry: dict) -> None:
    assert registry["policy"]["development_priority_grants_runtime_eligibility"] is False
    assert record(registry, "girza")["publication_eligibility_classification"] == "GOVERNED_RECORD_INELIGIBLE"


def test_duplicate_canonical_identity_fails_without_distinct_relationship(tmp_path: Path, registry: dict) -> None:
    record(registry, "awjila")["current_canonical_slug"] = "nafusa"
    with pytest.raises(RegistryValidationError, match="duplicate canonical identities"):
        validate_modified(tmp_path, registry)


def test_lakes_are_primary_but_remain_nested(registry: dict) -> None:
    lakes = record(registry, "natural-desert-lakes")
    assert lakes["development_priority_tier"] == "PRIMARY"
    assert lakes["current_canonical_slug"] is None
    assert lakes["parent_destination_slug"] == "desert"
    assert lakes["representation_mode"] == "NESTED_COLLECTION_WITHIN_PARENT"


def test_ghadames_is_primary_and_preserves_canonical_relationship(registry: dict) -> None:
    ghadames = record(registry, "ghadames")
    assert ghadames["development_priority_tier"] == "PRIMARY"
    assert ghadames["current_canonical_slug"] == "ghadames"
    assert "Old Town of Ghadames" in ghadames["alternate_repository_names"]
    assert ghadames["related_canonical_destination_relationships"] == [
        {"slug": "old-city-ghadames", "relationship": "CONTAINS_HERITAGE_CORE"}
    ]
    assert ghadames["coordinates_present"] is False


def test_nafusa_mountains_is_complementary(registry: dict) -> None:
    nafusa = record(registry, "nafusa-mountains")
    assert nafusa["development_priority_tier"] == "COMPLEMENTARY"
    assert nafusa["current_canonical_slug"] == "nafusa"
    assert nafusa["entity_type"] == "GEOGRAPHIC_REGION"


def test_added_identities_are_evidence_backed(registry: dict) -> None:
    expected = {
        "waddan": (None, "REPOSITORY_MENTION_ONLY"),
        "hun": (None, "REPOSITORY_MENTION_ONLY"),
        "sokna": (None, "REPOSITORY_MENTION_ONLY"),
        "awjila": ("awjila", "INDEPENDENT_CANONICAL_DESTINATION"),
        "girza": (None, "NOT_FOUND_IN_REPOSITORY"),
    }
    for key, (slug, mode) in expected.items():
        item = record(registry, key)
        assert item["current_canonical_slug"] == slug
        assert item["representation_mode"] == mode


def test_duplicate_record_id_fails(tmp_path: Path, registry: dict) -> None:
    registry["records"][1]["registry_record_id"] = registry["records"][0]["registry_record_id"]
    with pytest.raises(RegistryValidationError, match="registry_record_id"):
        validate_modified(tmp_path, registry)


def test_duplicate_coverage_key_fails(tmp_path: Path, registry: dict) -> None:
    registry["records"][1]["coverage_unit_key"] = registry["records"][0]["coverage_unit_key"]
    with pytest.raises(RegistryValidationError, match="coverage_unit_key"):
        validate_modified(tmp_path, registry)


def test_unknown_canonical_slug_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "tripoli")["current_canonical_slug"] = "not-a-destination"
    with pytest.raises(RegistryValidationError, match="unknown canonical slug"):
        validate_modified(tmp_path, registry)


def test_missing_evidence_file_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "tripoli")["evidence"][0]["path"] = "missing/evidence.json"
    with pytest.raises(RegistryValidationError, match="does not exist"):
        validate_modified(tmp_path, registry)


def test_invalid_coordinates_fail(tmp_path: Path, registry: dict) -> None:
    shahat = record(registry, "shahat-cyrene")
    shahat["coordinates_present"] = True
    shahat["coordinate_source"] = "backend/data/dev/destination-coordinates.reviewed.json"
    with pytest.raises(RegistryValidationError, match="no reviewed authoritative coordinate"):
        validate_modified(tmp_path, registry)


def test_false_gis_count_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "green-mountain")["gis_record_count"] = 179
    with pytest.raises(RegistryValidationError, match="GIS record count"):
        validate_modified(tmp_path, registry)


def test_invalid_parent_destination_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "natural-desert-lakes")["parent_destination_slug"] = "unknown-parent"
    with pytest.raises(RegistryValidationError, match="unknown parent slug"):
        validate_modified(tmp_path, registry)


def test_unsupported_vocabulary_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "tripoli")["coverage_status"] = "MADE_UP_STATUS"
    with pytest.raises(RegistryValidationError, match="unsupported coverage status"):
        validate_modified(tmp_path, registry)


def test_lakes_cannot_be_promoted_to_independent_destination(tmp_path: Path, registry: dict) -> None:
    lakes = record(registry, "natural-desert-lakes")
    lakes["current_canonical_slug"] = "desert"
    lakes["representation_mode"] = "INDEPENDENT_CANONICAL_DESTINATION"
    with pytest.raises(RegistryValidationError, match="must not be promoted"):
        validate_modified(tmp_path, registry)


def test_cyrene_shahat_exact_bilingual_project_identity(registry: dict) -> None:
    cyrene = record(registry, "shahat-cyrene")
    assert cyrene["name_ar"] == "قورينا – شحات"
    assert cyrene["name_en"] == "Cyrene (Shahat)"


def test_cyrene_shahat_is_unified_with_future_slug_only(registry: dict) -> None:
    cyrene = record(registry, "shahat-cyrene")
    model = cyrene["identity_model"]
    assert model["identity_model_status"] == "PROJECT_MODEL_RESOLVED"
    assert model["project_identity_decision"] == "UNIFIED_CYRENE_SHAHAT_DESTINATION"
    assert model["future_canonical_slug"] == "cyrene"
    assert cyrene["current_canonical_slug"] is None


def test_cyrene_remains_within_green_mountain_without_route_promotion(registry: dict) -> None:
    model = record(registry, "shahat-cyrene")["identity_model"]
    assert model["regional_relationships"] == [
        {"relationship": "WITHIN_REGION", "destination_slug": "green-mountain"}
    ]
    assert model["current_repository_representation"]["dedicated_public_route_present"] is False
    assert model["runtime_promotion_status"] == "NOT_PROMOTED"


def test_cyrene_current_runtime_slug_cannot_be_promoted(tmp_path: Path, registry: dict) -> None:
    record(registry, "shahat-cyrene")["current_canonical_slug"] = "cyrene"
    with pytest.raises(RegistryValidationError, match="unknown canonical slug|must not claim a current runtime"):
        validate_modified(tmp_path, registry)


def test_ghadames_contains_distinct_old_city_heritage_core(registry: dict) -> None:
    ghadames = record(registry, "ghadames")
    contained = ghadames["identity_model"]["contained_heritage_entities"]
    assert contained == [{
        "relationship": "CONTAINS_HERITAGE_CORE",
        "canonical_slug": "old-city-ghadames",
        "coordinate_inherited_by_destination": False,
        "separate_evidence_and_publication_requirements": True,
    }]
    authoritative = json.loads((ROOT / "backend/data/dev/destinations.json").read_text(encoding="utf-8"))
    slugs = {item["slug"] for item in authoritative["records"]}
    assert {"ghadames", "old-city-ghadames"}.issubset(slugs)


def test_old_city_coordinate_cannot_be_assigned_to_broader_ghadames(tmp_path: Path, registry: dict) -> None:
    ghadames = record(registry, "ghadames")
    ghadames["coordinates_present"] = True
    ghadames["coordinate_source"] = "backend/data/dev/destination-coordinates.reviewed.json"
    with pytest.raises(RegistryValidationError, match="no reviewed authoritative coordinate|must not be reused"):
        validate_modified(tmp_path, registry)


def test_acacus_composite_model_has_all_five_dimensions(registry: dict) -> None:
    acacus = record(registry, "acacus")
    assert acacus["entity_type"] == "COMPOSITE_CULTURAL_NATURAL_DESTINATION"
    assert acacus["identity_model"]["project_identity_decision"] == "COMPOSITE_CULTURAL_NATURAL_DESTINATION"
    assert acacus["identity_model"]["destination_dimensions"] == [
        "ARCHAEOLOGY",
        "ROCK_ART_AND_INSCRIPTIONS",
        "CULTURAL_HERITAGE",
        "NATURE_AND_DESERT_LANDSCAPE",
        "GEOLOGY_AND_GEOMORPHOLOGY",
    ]


def test_missing_acacus_dimension_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "acacus")["identity_model"]["destination_dimensions"].pop()
    with pytest.raises(RegistryValidationError, match="all five controlled destination dimensions"):
        validate_modified(tmp_path, registry)


def test_unknown_acacus_dimension_fails(tmp_path: Path, registry: dict) -> None:
    record(registry, "acacus")["identity_model"]["destination_dimensions"][0] = "UNKNOWN_DIMENSION"
    with pytest.raises(RegistryValidationError, match="unknown destination dimension"):
        validate_modified(tmp_path, registry)


def test_acacus_promotional_identity_requires_source_verification(registry: dict) -> None:
    promotional = record(registry, "acacus")["identity_model"]["promotional_identity"]
    assert promotional["name_ar"] == "المتحف العالمي المفتوح"
    assert promotional["name_en"] == "Open-air world museum"
    assert promotional["verification_status"] == "SOURCE_VERIFICATION_REQUIRED"
    assert promotional["official_title"] is False


def test_promotional_identity_cannot_imply_approval(tmp_path: Path, registry: dict) -> None:
    record(registry, "acacus")["identity_model"]["promotional_identity"]["grants_publication_approval"] = True
    with pytest.raises(RegistryValidationError, match="non-official and source-verification-required"):
        validate_modified(tmp_path, registry)


def test_identity_model_resolution_cannot_grant_runtime_eligibility(registry: dict) -> None:
    assert registry["policy"]["identity_model_resolution_grants_approval"] is False
    assert registry["policy"]["identity_model_resolution_grants_runtime_eligibility"] is False
    for key in ("shahat-cyrene", "ghadames", "acacus"):
        item = record(registry, key)
        assert item["identity_model"]["runtime_promotion_status"] == "NOT_PROMOTED"
        assert item["institutional_publication_approved"] is False


def test_legacy_visibility_cannot_be_marked_institutionally_approved(tmp_path: Path, registry: dict) -> None:
    record(registry, "tripoli")["institutional_publication_approved"] = True
    with pytest.raises(RegistryValidationError, match="legacy visibility as institutional approval"):
        validate_modified(tmp_path, registry)


def test_empty_ledger_preserves_false_institutional_approval(registry: dict) -> None:
    assert (ROOT / "backend/data/governance/publication-approval-ledger.jsonl").stat().st_size == 0
    assert all(item["institutional_publication_approved"] is False for item in registry["records"])


def test_heritage_ids_remain_excluded_from_natural_layer() -> None:
    natural = (ROOT / "assets/js/data/natural-tourism-layers.js").read_text(encoding="utf-8")
    assert "sourceFeatureId: 832" not in natural
    assert "sourceFeatureId: 913" not in natural
    assert validate_registry()["approved_events"] == 0


def test_protected_artifacts_are_unchanged() -> None:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_ARTIFACTS],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_deterministic_ordering_is_enforced(tmp_path: Path, registry: dict) -> None:
    registry["records"][0], registry["records"][1] = registry["records"][1], registry["records"][0]
    with pytest.raises(RegistryValidationError, match="deterministic"):
        validate_modified(tmp_path, registry)


def test_utf8_arabic_content_parses_correctly(registry: dict) -> None:
    assert record(registry, "leptis-magna")["name_ar"] == "لبدة الكبرى"
    assert record(registry, "natural-desert-lakes")["name_ar"] == "البحيرات الطبيعية والصحراوية"
    raw = REGISTRY_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")


def test_primary_heritage_scope_contracts_are_not_detailed_layers(registry: dict) -> None:
    for key in ("leptis-magna", "sabratha"):
        item = record(registry, key)
        assert item["development_priority_tier"] == "PRIMARY"
        assert item["gis_scope_contract_present"] is True
        assert item["gis_scope_contract_path"] == f"backend/data/gis/{key}-heritage-scope.review.json"
        assert item["gis_layer_present"] is False
        assert item["gis_record_count"] == 0


def test_scope_contract_cannot_claim_detailed_coverage(tmp_path: Path, registry: dict) -> None:
    item = record(registry, "leptis-magna")
    item["gis_layer_present"] = True
    with pytest.raises(RegistryValidationError, match="GIS presence conflicts"):
        validate_modified(tmp_path, registry)


def test_cyrene_source_reconciliation_is_not_detailed_gis(registry: dict) -> None:
    cyrene = record(registry, "shahat-cyrene")
    assert cyrene["gis_source_reconciliation_present"] is True
    assert cyrene["gis_source_reconciliation_path"] == "backend/data/gis/cyrene-source-reconciliation.review.json"
    assert cyrene["gis_layer_present"] is False
    assert cyrene["gis_record_count"] == 0
    assert cyrene["identity_model"]["runtime_promotion_status"] == "NOT_PROMOTED"


def test_cyrene_reconciliation_cannot_increase_registry_gis_count(registry: dict) -> None:
    assert sum(item["gis_record_count"] for item in registry["records"]) == 214


def test_ghadames_source_reconciliation_is_review_evidence_not_detailed_gis(registry: dict) -> None:
    ghadames = record(registry, "ghadames")
    assert ghadames["gis_source_reconciliation_present"] is True
    assert ghadames["gis_source_reconciliation_path"] == "backend/data/gis/ghadames-source-reconciliation.review.json"
    assert ghadames["gis_review_evidence_record_count"] == 773
    assert ghadames["gis_layer_present"] is False
    assert ghadames["gis_record_count"] == 0
    assert ghadames["coordinates_present"] is False
    assert sum(item["gis_record_count"] for item in registry["records"]) == 214
