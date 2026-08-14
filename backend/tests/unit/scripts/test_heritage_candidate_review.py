from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.heritage_candidate_review import (
    ARTIFACT_PATH,
    CROSS_LAYER_PATH,
    LEAKAGE_PATHS,
    REPOSITORY_ROOT,
    HeritageValidationError,
    validate_no_leakage,
    validate_payload,
    validate_repository,
)


def load(relative: Path) -> dict:
    return json.loads((REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))


@pytest.fixture
def payloads() -> tuple[dict, dict]:
    return load(ARTIFACT_PATH), load(CROSS_LAYER_PATH)


def test_valid_two_record_artifact(payloads: tuple[dict, dict]) -> None:
    artifact, cross_layer = payloads
    validate_payload(artifact, cross_layer)
    assert {item["source_feature_id"] for item in artifact["records"]} == {832, 913}


def test_exact_source_identity_and_coordinates_are_preserved(payloads: tuple[dict, dict]) -> None:
    artifact, cross_layer = payloads
    source = {item["source_feature_id"]: item for item in cross_layer["records"]["sahara_cross_layer"]}
    for record in artifact["records"]:
        original = source[record["source_feature_id"]]
        assert record["name"] == original["name"]
        assert record["latitude"] == original["latitude"]
        assert record["longitude"] == original["longitude"]
        assert record["source"] == original["source"]
        assert record["origin"] == original["origin"]


def test_duplicate_id_is_rejected(payloads: tuple[dict, dict]) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    artifact["records"][1]["source_feature_id"] = 832
    with pytest.raises(HeritageValidationError, match="duplicate"):
        validate_payload(artifact, cross_layer)


@pytest.mark.parametrize("mode", ["missing", "extra"])
def test_missing_or_extra_id_is_rejected(payloads: tuple[dict, dict], mode: str) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    if mode == "missing":
        artifact["records"].pop()
    else:
        extra = copy.deepcopy(artifact["records"][0])
        extra["source_feature_id"] = 999
        artifact["records"].append(extra)
    with pytest.raises(HeritageValidationError, match="exactly"):
        validate_payload(artifact, cross_layer)


def test_unsupported_schema_is_rejected(payloads: tuple[dict, dict]) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    artifact["schema_version"] = 2
    with pytest.raises(HeritageValidationError, match="unsupported schema"):
        validate_payload(artifact, cross_layer)


@pytest.mark.parametrize("field,value", [("latitude", 91.0), ("longitude", float("inf"))])
def test_invalid_coordinate_is_rejected(payloads: tuple[dict, dict], field: str, value: float) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    artifact["records"][0][field] = value
    with pytest.raises(HeritageValidationError):
        validate_payload(artifact, cross_layer)


@pytest.mark.parametrize(
    "field",
    [
        "canonical_approval", "publication_approved", "canonical_identity_approved",
        "coordinate_approved", "destination_membership_approved", "media_approved",
    ],
)
def test_any_approval_becoming_true_is_rejected(payloads: tuple[dict, dict], field: str) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    artifact["records"][0][field] = True
    with pytest.raises(HeritageValidationError):
        validate_payload(artifact, cross_layer)


@pytest.mark.parametrize("field", ["institutional_review", "publication_decision"])
def test_premature_decision_is_rejected(payloads: tuple[dict, dict], field: str) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    artifact["records"][0][field] = {"decision": "approved"}
    with pytest.raises(HeritageValidationError, match="must remain null"):
        validate_payload(artifact, cross_layer)


@pytest.mark.parametrize(
    "field",
    ["name_en", "slug", "municipality", "description", "historical_period", "source_registry_id", "media_url"],
)
def test_forbidden_editorial_field_is_rejected(payloads: tuple[dict, dict], field: str) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    artifact["records"][0][field] = "invented"
    with pytest.raises(HeritageValidationError):
        validate_payload(artifact, cross_layer)


@pytest.mark.parametrize("field", ["routing_status", "recommended_review_path"])
def test_invalid_routing_enum_is_rejected(payloads: tuple[dict, dict], field: str) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    artifact["records"][0][field] = "PUBLISHED"
    with pytest.raises(HeritageValidationError, match="invalid"):
        validate_payload(artifact, cross_layer)


def test_cross_layer_reference_mismatch_is_rejected(payloads: tuple[dict, dict]) -> None:
    artifact, cross_layer = copy.deepcopy(payloads)
    cross_layer["records"]["sahara_cross_layer"][0]["routed_artifact"] = "wrong.json"
    with pytest.raises(HeritageValidationError, match="routed_artifact mismatch"):
        validate_payload(artifact, cross_layer)


@pytest.mark.parametrize(
    "name,content",
    [
        ("natural.json", '{"records":[{"source_feature_id":832}]}'),
        ("natural.js", 'const feature = {"sourceFeatureId": 913};'),
        ("heritage.html", "<h2>قلعة أم العبيد</h2>"),
    ],
)
def test_natural_frontend_or_destination_leakage_is_rejected(name: str, content: str) -> None:
    with pytest.raises(HeritageValidationError, match="leaked"):
        validate_no_leakage({name: content})


def test_validation_mode_makes_no_writes() -> None:
    paths = [ARTIFACT_PATH, CROSS_LAYER_PATH, *LEAKAGE_PATHS]
    before = {path: (REPOSITORY_ROOT / path).read_bytes() for path in paths}
    validate_repository()
    after = {path: (REPOSITORY_ROOT / path).read_bytes() for path in paths}
    assert after == before
