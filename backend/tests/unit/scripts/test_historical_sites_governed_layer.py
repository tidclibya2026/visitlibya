import json

from scripts import historical_sites_governed_layer as layer
from scripts import ingest_governed_gis as ingestion


def test_historical_sites_accounting():
    imported, blocked = layer.validate()

    assert imported["source_feature_count"] == 136

    assert (
        len(imported["features"])
        + len(blocked["records"])
        == 136
    )

    assert imported["publication_approved"] is False
    assert imported["canonical_identity_approved"] is False
    assert imported["authoritative_boundary_claimed"] is False


def test_safe_historical_sites_are_unique_points():
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


def test_historical_subtypes_are_preserved():
    imported, blocked = layer.validate()

    values = {
        feature["properties"]["historical_subtype"]
        for feature in imported["features"]
    }

    values.update(
        record["historical_subtype"]
        for record in blocked["records"]
    )

    assert values == {
        "church",
        "historic_farm",
        "theatre",
        "palace",
        "shrine",
    }


def test_historical_ingestion_contract(tmp_path):
    imported, _ = layer.build()

    if not imported["features"]:
        return

    path = tmp_path / "historical-sites.geojson"

    path.write_text(
        json.dumps(imported, ensure_ascii=False),
        encoding="utf-8",
    )

    validated = ingestion.validate_geojson(
        path,
        "HISTORICAL_SITES",
    )

    assert len(validated.features) == len(
        imported["features"]
    )

    assert {
        feature.geometry_type
        for feature in validated.features
    } == {"POINT"}
