import json

from scripts import ingest_governed_gis as ingestion
from scripts import parks_governed_layer as layer


def test_parks_accounting_and_governance():
    imported, blocked, cross = layer.validate()
    assert imported["source_feature_count"] == 71
    assert len(imported["features"]) + len(blocked["records"]) == 71
    assert imported["publication_approved"] is False
    assert imported["canonical_identity_approved"] is False
    assert imported["authoritative_boundary_claimed"] is False
    assert cross["publication_approved"] is False


def test_source_layers_subtypes_and_point_geometry_are_preserved():
    imported, blocked, _ = layer.validate()
    records = [f["properties"] for f in imported["features"]] + blocked["records"]
    assert {r["source_metadata"]["source_layer"] for r in records} == {
        "منتزهات", "المنتزهات_الوطنية_1"
    }
    assert {r["source_metadata"]["source_subtype"] for r in records} == {
        "park", "national_park"
    }
    assert all((r.get("geometry") or r["source_metadata"].get("source_geometry", {})).get("type", "Point") == "Point"
               for r in records)


def test_safe_parks_are_unique_wgs84_points():
    imported, _, _ = layer.validate()
    coords = []
    for feature in imported["features"]:
        assert feature["geometry"]["type"] == "Point"
        x, y = feature["geometry"]["coordinates"]
        assert -180 <= x <= 180 and -90 <= y <= 90
        coords.append(tuple(feature["geometry"]["coordinates"]))
    codes = [f["properties"]["feature_code"] for f in imported["features"]]
    assert len(codes) == len(set(codes))


def test_parks_ingestion_contract(tmp_path):
    imported, _, _ = layer.build()
    path = tmp_path / "parks.geojson"
    path.write_text(json.dumps(imported, ensure_ascii=False), encoding="utf-8")
    validated = ingestion.validate_geojson(path, "PARKS")
    assert len(validated.features) == len(imported["features"])
    assert {feature.geometry_type for feature in validated.features} == {"POINT"}


def test_cross_layer_review_is_complete_and_non_authoritative():
    _, _, cross = layer.validate()
    assert cross["comparison_layers"] == [
        "NATURAL_SITES", "WORLD_HERITAGE", "OLD_CITIES",
        "HISTORICAL_SITES", "FORTIFICATIONS",
    ]
    assert cross["coordinate_review_excluded_count"] == 12
    assert len(cross["coordinate_review_excluded_records"]) == 12
    assert all(r["relationship"] == "CROSS_LAYER_REFERENCE" for r in cross["records"])
    assert all(r["authoritative_boundary_claimed"] is False for r in cross["records"])
