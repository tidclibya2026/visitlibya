import json
from pathlib import Path

from app.gis.layer_registry import require_layer
from scripts.ingest_governed_gis import validate_geojson


ROOT = Path(__file__).resolve().parents[4]

APPROVED = (
    ROOT
    / "backend"
    / "data"
    / "gis"
    / "rock-art-akakus-approved-23.review.geojson"
)

DUPLICATES = (
    ROOT
    / "backend"
    / "data"
    / "gis"
    / "rock-art-akakus-duplicate-review.json"
)

SOURCE_SHA256 = (
    "9A245F4F60E6DDCB425D04D7875BFB382DF337A56D48892F12ED3B300CE55832"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_approved_artifact_counts_and_source_identity():
    data = load(APPROVED)

    assert data["layer_code"] == "ROCK_ART"
    assert data["source_file"] == "اكاكوس.kml"
    assert data["source_sha256"] == SOURCE_SHA256

    assert data["source_placemark_count"] == 430
    assert data["rock_art_candidate_count"] == 46
    assert data["approved_unique_count"] == 23
    assert data["duplicate_source_copy_count"] == 23

    assert len(data["features"]) == 23


def test_all_approved_features_are_unique_points():
    data = load(APPROVED)
    features = data["features"]

    assert {f["geometry"]["type"] for f in features} == {"Point"}

    institutional_ids = [
        f["properties"]["institutional_id"]
        for f in features
    ]

    feature_codes = [
        f["properties"]["feature_code"]
        for f in features
    ]

    source_feature_ids = [
        f["properties"]["source_feature_id"]
        for f in features
    ]

    assert len(institutional_ids) == len(set(institutional_ids)) == 23
    assert len(feature_codes) == len(set(feature_codes)) == 23
    assert len(source_feature_ids) == len(set(source_feature_ids)) == 23


def test_governance_status_is_approved_but_unpublished():
    data = load(APPROVED)

    assert data["publication_approved"] is False

    for feature in data["features"]:
        props = feature["properties"]

        assert props["layer_code"] == "ROCK_ART"
        assert props["category"] == "rock_art"

        assert props["authority_status"] == "APPROVED"
        assert props["review_status"] == "APPROVED"
        assert props["canonical_identity_approved"] is True

        assert props["publication_approved"] is False
        assert props["is_published"] is False


def test_duplicate_review_contains_exactly_23_source_copies():
    review = load(DUPLICATES)

    assert review["layer_code"] == "ROCK_ART"
    assert review["source_file"] == "اكاكوس.kml"
    assert review["source_sha256"] == SOURCE_SHA256

    assert review["rock_art_candidate_count"] == 46
    assert review["canonical_unique_count"] == 23
    assert review["duplicate_count"] == 23

    assert len(review["records"]) == 23

    for record in review["records"]:
        assert record["classification"] == "NEAR_DUPLICATE_SOURCE_COPY"
        assert record["distance_metres"] <= 2.0


def test_registry_supports_rock_art_points_without_forcing_point_only():
    layer = require_layer("ROCK_ART")

    assert layer.layer_code == "ROCK_ART"
    assert layer.name_ar == "الفنون الصخرية"
    assert layer.category == "rock_art"

    assert "POINT" in layer.allowed_geometry_types
    assert layer.default_is_published is False


def test_governed_ingestion_contract_accepts_all_23():
    validated = validate_geojson(APPROVED, "ROCK_ART")

    assert len(validated.features) == 23
    assert {
        feature.geometry_type
        for feature in validated.features
    } == {"POINT"}

