from __future__ import annotations

import copy
import json
import re
from collections import Counter

import pytest

from scripts.high_priority_natural_candidates import (
    ARTIFACT_PATH,
    EXTERNAL_HASHES,
    EXPECTED_ACTIONS,
    EXPECTED_DECISIONS,
    EXPECTED_ORDINAL_ORDER,
    FALSE_FIELDS,
    GOVERNANCE,
    HighPriorityReviewError,
    ROUTING_REQUIREMENTS,
    build_artifact,
    validate_artifact,
    validate_serialization,
)


@pytest.fixture
def artifact():
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def by_ordinal(artifact):
    return {item["identity"]["source_ordinal"]: item for item in artifact["candidates"]}


def test_valid_artifact_passes(artifact):
    result = validate_artifact(artifact, check_git=False)
    assert result == {
        "records": 7,
        "decisions": EXPECTED_DECISIONS,
        "approved": 0,
        "publicly_visible": 0,
        "publication_media_eligible": 0,
    }
    validate_serialization()


def test_corrected_external_hash_contract_and_fail_closed_build(tmp_path):
    assert EXTERNAL_HASHES == {
        "high-priority-natural-candidates.review.json": "4f6725b67ce91be836de44566790823893a61e11457eefed562cbe43ae99d458",
        "high-priority-natural-candidates-review.md": "760bf4ce1d85664c98a71d521cafb7d135a31f500a939d806d74bc124b562f24",
        "validate_high_priority_natural_candidates.py": "d7cc97590e45b68fcc10bf3e8d3a2a56ad2e4c4cd36150c8dc4e24061a7d3f31",
        "high-priority-natural-candidates-hashes.json": "615877480fd7795e60a92b4ced15fe5be42a4ded519f2b66742fdbee7f21bad0",
    }
    with pytest.raises(HighPriorityReviewError, match="external packet hash mismatch"):
        build_artifact(tmp_path)


def test_exact_ordinals_order_and_action_matrix(artifact):
    records = artifact["candidates"]
    assert tuple(item["identity"]["source_ordinal"] for item in records) == EXPECTED_ORDINAL_ORDER
    assert {
        item["identity"]["source_ordinal"]: item["institutional_review"]["review_routing_action"]
        for item in records
    } == EXPECTED_ACTIONS
    assert Counter(item["institutional_review"]["review_routing_action"] for item in records) == Counter(EXPECTED_DECISIONS)


def test_complete_governed_evidence_is_preserved(artifact):
    for item in artifact["candidates"]:
        assert set(item) == {"identity", "source_evidence", "editorial_readiness", "institutional_review", "governance"}
        assert item["identity"]["editorial_candidate_id"].startswith("nnr-phase1-")
        assert item["identity"]["governed_review_id"].startswith("nnr-")
        assert item["identity"]["geometry_type"] == "Point"
        assert item["source_evidence"]["complete_source_description"]
        assert item["source_evidence"]["preserved_properties"]
        assert "quality_flags" in item["source_evidence"]
        assert "existing_governed_overlaps" in item["source_evidence"]
        assert item["editorial_readiness"]["score"] == sum(item["editorial_readiness"]["score_components"].values())


def test_candidate_specific_safeguards_are_exact(artifact):
    records = by_ordinal(artifact)
    assert all(records[ordinal]["institutional_review"]["routing_requirements"] == expected for ordinal, expected in ROUTING_REQUIREMENTS.items())
    assert records[640]["institutional_review"]["routing_requirements"]["acceptance_condition"] == "CONDITIONAL_DAM_VERIFICATION"
    assert records[640]["institutional_review"]["routing_requirements"]["dam_safety_verification_required"] is True
    assert records[849]["institutional_review"]["routing_requirements"]["environmental_sensitivity_review_required"] is True
    assert records[80]["institutional_review"]["routing_requirements"]["mining_or_artificial_excavation_review_required"] is True
    assert records[182]["institutional_review"]["routing_requirements"]["settlement_road_agriculture_infrastructure_review_required"] is True


def test_description_returns_preserve_flag_and_block_field_acceptance(artifact):
    records = by_ordinal(artifact)
    for ordinal in (770, 938):
        item = records[ordinal]
        assert item["institutional_review"]["review_routing_action"] == "RETURN_FOR_DESCRIPTION"
        assert item["institutional_review"]["routing_requirements"]["scope_review_required"] is True
        assert item["institutional_review"]["routing_requirements"]["field_acceptance_blocked_until_description_and_scope_resolved"] is True
        assert "DESCRIPTION_CONTAINS_NON_NATURAL_OR_MIXED_SCOPE_SIGNALS" in item["source_evidence"]["quality_flags"]


def test_all_governance_is_unresolved_and_prohibited(artifact):
    assert artifact["packet_governance"] == GOVERNANCE
    for item in artifact["candidates"]:
        assert item["governance"] == GOVERNANCE
        assert item["institutional_review"]["institutional_decision"] == "PENDING"
        assert item["institutional_review"]["review_routing_is_final_approval"] is False
        assert item["institutional_review"]["routing_requirements"]["publication_remains_prohibited"] is True
        assert all(item["governance"][field] is False for field in FALSE_FIELDS)


@pytest.mark.parametrize("field", FALSE_FIELDS)
def test_governance_drift_fails_closed(artifact, field):
    invalid = copy.deepcopy(artifact)
    invalid["candidates"][0]["governance"][field] = True
    with pytest.raises(HighPriorityReviewError, match="governance drift"):
        validate_artifact(invalid, check_git=False)


def test_action_matrix_drift_fails_closed(artifact):
    invalid = copy.deepcopy(artifact)
    invalid["candidates"][0]["institutional_review"]["review_routing_action"] = "ACCEPT_FOR_FIELD_VERIFICATION"
    with pytest.raises(HighPriorityReviewError, match="decision distribution|review action"):
        validate_artifact(invalid, check_git=False)


def test_safeguard_drift_fails_closed(artifact):
    invalid = copy.deepcopy(artifact)
    by_ordinal(invalid)[640]["institutional_review"]["routing_requirements"]["dam_safety_verification_required"] = False
    with pytest.raises(HighPriorityReviewError, match="safeguards drift"):
        validate_artifact(invalid, check_git=False)


def test_source_evidence_drift_fails_closed(artifact):
    invalid = copy.deepcopy(artifact)
    invalid["candidates"][0]["source_evidence"]["complete_source_description"] = "invented"
    with pytest.raises(HighPriorityReviewError, match="description drift"):
        validate_artifact(invalid, check_git=False)


def test_media_remains_unavailable_and_rights_unresolved(artifact):
    for item in artifact["candidates"]:
        readiness = item["editorial_readiness"]
        assert readiness["media_availability"] == "NO_SOURCE_MEDIA_REFERENCE"
        assert readiness["media_rights_status"] == "NO_INDEPENDENT_RIGHTS_EVIDENCE"
        assert item["governance"]["publication_media_eligible"] is False


def test_serialization_is_portable_utf8_lf():
    raw = ARTIFACT_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert b"visitlibya-local-backups" not in raw
    assert not re.search(rb"(?i)[a-z]:[\\/]", raw)
