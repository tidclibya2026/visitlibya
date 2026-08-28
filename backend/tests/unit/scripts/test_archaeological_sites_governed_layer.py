import json

from scripts import archaeological_sites_governed_layer as layer
from scripts import ingest_governed_gis as ingestion


def test_archaeological_accounting_is_exact():
    imported, blocked = layer.validate()

    assert imported["source_feature_count"] == 11
    assert len(imported["features"]) + len(blocked["records"]) == 11

    assert imported["publication_approved"] is False
    assert imported["canonical_identity_approved"] is False
    assert imported["authoritative_boundary_claimed"] is False
    assert imported["world_heritage_authority_duplicated"] is False


def test_governed_import_contains_only_safe_points():
    imported, blocked = layer.validate()

    assert all(
        feature["geometry"]["type"] == "Point"
        for feature in imported["features"]
    )

    assert all(
        feature["properties"]["review_classification"]
        == "SAFE_ARCHAEOLOGICAL_POINT"
        for feature in imported["features"]
    )

    assert all(
        record["review_classification"]
        != "SAFE_ARCHAEOLOGICAL_POINT"
        for record in blocked["records"]
    )


def test_no_duplicate_governed_identity():
    imported, _ = layer.validate()

    feature_codes = [
        feature["properties"]["feature_code"]
        for feature in imported["features"]
    ]

    institutional_ids = [
        feature["properties"]["institutional_id"]
        for feature in imported["features"]
    ]

    assert len(feature_codes) == len(set(feature_codes))
    assert len(institutional_ids) == len(set(institutional_ids))


def test_import_satisfies_governed_ingestion_contract(tmp_path):
    imported, blocked = layer.build()

    # A governed review layer may legitimately resolve to zero ingestible
    # features. In that case no PostGIS ingestion attempt must be made.
    if not imported["features"]:
        assert imported["source_feature_count"] == 11
        assert len(blocked["records"]) == 11
        assert imported["publication_approved"] is False
        return

    path = tmp_path / "archaeological-sites.geojson"

    path.write_text(
        json.dumps(imported, ensure_ascii=False),
        encoding="utf-8",
    )

    validated = ingestion.validate_geojson(
        path,
        "ARCHAEOLOGICAL_SITES",
    )

    assert len(validated.features) == len(imported["features"])

    assert {
        feature.geometry_type
        for feature in validated.features
    } == {"POINT"}
