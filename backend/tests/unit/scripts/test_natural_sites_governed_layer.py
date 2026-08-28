import json

from scripts import ingest_governed_gis as ingestion
from scripts import natural_sites_governed_layer as layer


def test_artifacts_are_deterministic_complete_and_fail_closed():
    imported, blocked = layer.validate()
    assert imported["evidence_count"] == 945
    assert len(imported["features"]) + len(blocked["records"]) == 945
    assert sum(imported["category_counts"].values()) == 945
    assert imported["publication_approved"] is False
    assert imported["authoritative_protected_area_boundary_claimed"] is False
    assert imported["lake_wadi_or_hydrological_extent_claimed"] is False
    assert imported["tourism_zone_trail_or_route_claimed"] is False


def test_only_safe_valid_source_points_are_ingestible():
    imported, blocked = layer.validate()
    safe = {"SAFE_POINT_CANDIDATE", "SAFE_NAMED_GEOMETRY_CANDIDATE"}
    assert imported["features"]
    assert {feature["geometry"]["type"] for feature in imported["features"]} == {"Point"}
    assert {feature["properties"]["review_classification"] for feature in imported["features"]} == safe
    assert all(record["review_classification"] not in safe for record in blocked["records"])
    assert all(feature["properties"]["source_metadata"]["preserved_properties"] for feature in imported["features"])


def test_boundaries_duplicates_context_and_exclusions_remain_blocked():
    imported, blocked = layer.validate()
    counts = imported["category_counts"]
    for category in layer.CATEGORIES:
        assert counts[category] >= 1
    blocked_categories = {record["review_classification"] for record in blocked["records"]}
    assert "BOUNDARY_SEMANTICS_UNRESOLVED" in blocked_categories
    assert "DUPLICATE_OR_IDENTITY_REVIEW" in blocked_categories
    assert "EXCLUDED_FROM_INGESTION" in blocked_categories
    assert all(record["geometry"] and record["source_metadata"]["source_reference"] for record in blocked["records"])


def test_import_passes_governed_ingestion_contract(tmp_path):
    imported, _ = layer.build()
    path = tmp_path / "natural-sites.geojson"
    path.write_text(json.dumps(imported, ensure_ascii=False), encoding="utf-8")
    validated = ingestion.validate_geojson(path, "NATURAL_SITES")
    assert len(validated.features) == len(imported["features"])
    assert {feature.geometry_type for feature in validated.features} == {"POINT"}
