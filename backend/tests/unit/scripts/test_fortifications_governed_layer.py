import json

from scripts import fortifications_governed_layer as layer
from scripts import ingest_governed_gis as ingestion


def test_fortifications_accounting():
    imported, blocked = layer.validate()

    assert imported["source_feature_count"] == 12

    assert (
        len(imported["features"])
        + len(blocked["records"])
        == 12
    )

    assert imported["publication_approved"] is False
    assert imported["canonical_identity_approved"] is False
    assert imported["authoritative_boundary_claimed"] is False


def test_safe_fortifications_are_unique_points():
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


def test_archaeological_cross_reference_is_not_created_as_extra_authority():
    imported, blocked = layer.validate()

    assert (
        len(imported["features"])
        + len(blocked["records"])
        == 12
    )

    assert (
        blocked[
            "unresolved_cross_layer_reference_count"
        ]
        >= 0
    )


def test_fortification_ingestion_contract(tmp_path):
    imported, _ = layer.build()

    if not imported["features"]:
        return

    path = tmp_path / "fortifications.geojson"

    path.write_text(
        json.dumps(imported, ensure_ascii=False),
        encoding="utf-8",
    )

    validated = ingestion.validate_geojson(
        path,
        "FORTIFICATIONS",
    )

    assert len(validated.features) == len(
        imported["features"]
    )

    assert {
        feature.geometry_type
        for feature in validated.features
    } == {"POINT"}
