import json

from scripts import ingest_governed_gis as ingestion
from scripts import world_heritage_governed_layer as layer


def test_artifact_is_deterministic_and_fail_closed():
    artifact = layer.validate()
    assert artifact["layer_code"] == "WORLD_HERITAGE"
    assert artifact["publication_approved"] is False
    assert len(artifact["features"]) == 4
    assert artifact["excluded_sites"] == [{
        "site": "cyrene",
        "reason": "REVIEW_REQUIRED_AGGREGATE_NO_REVIEWED_CANONICAL_SITE_ANCHOR",
    }]


def test_only_reviewed_kml_anchors_are_included():
    artifact = layer.validate()
    assert [item["properties"]["feature_code"] for item in artifact["features"]] == [
        "world-heritage-leptis-magna",
        "world-heritage-sabratha",
        "world-heritage-acacus",
        "world-heritage-old-city-ghadames",
    ]
    assert all(item["geometry"]["type"] == "Point" for item in artifact["features"])
    assert all(
        item["properties"]["source_metadata"]["artifact_status"]
        == "REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"
        for item in artifact["features"]
    )


def test_artifact_passes_pr112_ingestion_contract(tmp_path):
    path = tmp_path / "world-heritage.geojson"
    path.write_text(json.dumps(layer.build(), ensure_ascii=False), encoding="utf-8")
    validated = ingestion.validate_geojson(path, "WORLD_HERITAGE")
    assert len(validated.features) == 4
    assert {feature.geometry_type for feature in validated.features} == {"POINT"}
