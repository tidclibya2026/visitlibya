import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_PATH = (
    ROOT / "data" / "gis" / "libya-boundary-candidate.review.json"
)


def load_candidate():
    return json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))


def test_libya_boundary_candidate_remains_blocked_without_authority():
    candidate = load_candidate()

    assert candidate["candidate_id"] == "libya-national-boundary"
    assert candidate["publication_status"] == "BLOCKED"
    assert candidate["authority_status"] == "NOT_AUTHORITATIVE"
    assert candidate["geometry_status"] == "NOT_AVAILABLE"

    assert candidate["source_id"] is None
    assert candidate["source_file"] is None
    assert candidate["institutional_source_reference"] is None


def test_no_existing_polygon_source_is_accepted_as_national_boundary():
    candidate = load_candidate()

    reviewed = candidate["polygon_sources_reviewed"]

    assert reviewed
    assert all(
        item["decision"] == "REJECT_AS_NATIONAL_BOUNDARY"
        for item in reviewed
    )


def test_boundary_publication_requires_governed_source_evidence():
    candidate = load_candidate()

    requirements = set(candidate["publication_requirements"])

    required = {
        "Identifiable authoritative source",
        "Documented provenance",
        "Declared CRS",
        "Geometry validity verification",
        "National coverage verification",
        "Institutional review",
        "Explicit publication approval",
    }

    assert required <= requirements


def test_audit_did_not_resolve_national_scale_boundary():
    candidate = load_candidate()

    evidence = candidate["evidence"]

    assert evidence["institutional_audit_sources_checked"] == 13
    assert evidence["national_scale_boundary_found"] is False
    assert (
        evidence["taxonomy_crosswalk"]["mapping_status"]
        == "REVIEW_REQUIRED"
    )
