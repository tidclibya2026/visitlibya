import json

from scripts import old_cities_governed_layer as layer
from scripts import ingest_governed_gis as ingestion


def test_old_cities_accounting():
    imported, blocked = layer.validate()

    assert imported["source_feature_count"] == 27

    assert (
        len(imported["features"])
        + len(blocked["records"])
        == 27
    )

    assert imported["publication_approved"] is False
    assert imported["canonical_identity_approved"] is False
    assert imported["authoritative_boundary_claimed"] is False


def test_safe_old_cities_are_unique_points():
    imported, _ = layer.validate()

    assert all(
        feature["geometry"]["type"] == "Point"
        for feature in imported["features"]
    )

    codes = [
        feature["properties"]["feature_code"]
        for feature in imported["features"]
    ]

    assert len(codes) == len(set(codes))


def test_existing_authorities_are_not_recreated():
    _, blocked = layer.validate()

    classifications = {
        record["review_classification"]
        for record in blocked["records"]
    }

    assert (
        "CROSS_LAYER_REFERENCE_WORLD_HERITAGE"
        in classifications
    )


def test_old_cities_ingestion_contract(tmp_path):
    imported, _ = layer.build()

    if not imported["features"]:
        return

    path = tmp_path / "old-cities.geojson"

    path.write_text(
        json.dumps(
            imported,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    validated = ingestion.validate_geojson(
        path,
        "OLD_CITIES",
    )

    assert len(validated.features) == len(
        imported["features"]
    )

    assert {
        feature.geometry_type
        for feature
        in validated.features
    } == {"POINT"}
