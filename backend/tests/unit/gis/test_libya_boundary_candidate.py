import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_PATH = (
    ROOT / "data" / "gis" / "libya-boundary-candidate.review.json"
)


def load_candidate():
    return json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))


def test_libya_boundary_source_is_resolved():
    candidate = load_candidate()

    assert candidate["candidate_id"] == "libya-national-boundary"
    assert candidate["authority_status"] == "INSTITUTIONAL_SOURCE_RESOLVED"
    assert candidate["geometry_status"] == "VALIDATED"
    assert candidate["review_status"] == "VALIDATION_COMPLETE"


def test_libya_boundary_source_identity():
    candidate = load_candidate()

    assert candidate["source_file"] == "LibyaData.mdb"
    assert candidate["feature_dataset"] == "الحدود"
    assert candidate["feature_class"] == "الحدودالدولية"
    assert candidate["source_filter"] == "Countries_EN = Libya"

    assert candidate["display_name_ar"] == "ليبيا"
    assert candidate["display_name_en"] == "Libya"


def test_libya_boundary_geometry_validation():
    candidate = load_candidate()

    assert candidate["geometry_type"] == "Polygon"
    assert candidate["crs"] == "GCS_WGS_1984"
    assert candidate["feature_count"] == 1

    validation = candidate["geometry_validation"]

    assert validation["errors"] == 0
    assert validation["status"] == "VALID"


def test_libya_boundary_publication_remains_pending():
    candidate = load_candidate()

    assert candidate["publication_status"] == "BLOCKED"

    derived = candidate["derived_dataset"]

    assert derived["feature_count"] == 1
    assert len(derived["shp_sha256"]) == 64
    assert len(derived["dbf_sha256"]) == 64
    assert len(derived["prj_sha256"]) == 64
    assert len(derived["shx_sha256"]) == 64
