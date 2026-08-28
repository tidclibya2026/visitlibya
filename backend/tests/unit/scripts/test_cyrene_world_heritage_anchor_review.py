from __future__ import annotations

import copy
import json

import pytest

from scripts.cyrene_world_heritage_anchor_review import (
    ARTIFACT_PATH,
    CyreneAnchorReviewError,
    validate_artifact,
    validate_serialization,
)


def artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_blocked_review_is_deterministic_and_source_backed() -> None:
    assert validate_artifact(artifact()) == {
        "classification": "NO_SAFE_GEOMETRY",
        "coordinate_candidates": 2,
        "distance_m": 1455.322,
    }
    validate_serialization()


def test_identity_layers_remain_distinct() -> None:
    review = artifact()
    assert review["canonical_property_identity"]["identity_decision"] == "UNESCO_PROPERTY_DISTINCT_FROM_MODERN_SHAHAT_AND_REGIONAL_CONTEXT"
    assert review["destination_identity"]["classification"] == "IDENTITY_REVIEW_REQUIRED"
    assert review["supporting_evidence"][0]["classification"] == "REGIONAL_CONTEXT_ONLY"
    assert review["supporting_evidence"][1]["classification"] == "BOUNDARY_SEMANTICS_UNRESOLVED"


def test_no_ingestion_feature_or_publication_authority_is_emitted() -> None:
    review = artifact()
    assert review["geometry_decision"]["ingestion_feature"] is None
    assert review["geometry_decision"]["world_heritage_ingestion_eligible"] is False
    assert review["governance"]["authority_status"] == "unapproved"
    assert review["governance"]["is_published"] is False
    assert review["governance"]["postgis_ingestion_performed"] is False


def test_coordinate_selection_cannot_be_silently_enabled() -> None:
    review = copy.deepcopy(artifact())
    review["geometry_decision"]["canonical_site_anchor_ready"] = True
    with pytest.raises(CyreneAnchorReviewError, match="fail-closed"):
        validate_artifact(review)
