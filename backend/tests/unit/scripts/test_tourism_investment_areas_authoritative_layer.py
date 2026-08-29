from pathlib import Path

import pytest
from shapely.geometry import shape

from app.api.v1.endpoints.governed_gis import router as governed_gis_router
from app.gis.layer_registry import require_layer
from scripts import ingest_governed_gis as ingestion
from scripts import tourism_investment_areas_authoritative_layer as areas


@pytest.fixture(scope="module")
def artifacts():
    return areas.validate()


def feature_by_fid(collection: dict, fid: int) -> dict:
    return next(feature for feature in collection["features"] if feature["properties"]["fid"] == fid)


def test_corrected_source_hashes_and_accounting(artifacts):
    source, reconciliation, governed, _ = artifacts
    assert source["excel_sha256"] == areas.EXCEL_SHA256
    assert source["kml_sha256"] == areas.KML_SHA256
    assert source["excel_record_count"] == 141
    assert source["kml_record_count"] == 141
    assert source["matched_count"] == 141
    assert reconciliation["matched_count"] == 141
    assert reconciliation["approved_count"] == 141
    assert reconciliation["blocked_count"] == 0
    assert len(governed["features"]) == 141


def test_no_missing_or_duplicate_identity_or_geometry(artifacts):
    source, reconciliation, governed, _ = artifacts
    assert reconciliation["missing_identity_count"] == 0
    assert reconciliation["duplicate_identity_count"] == 0
    assert reconciliation["missing_geometry_count"] == 0
    ids = [feature["properties"]["institutional_id"] for feature in governed["features"]]
    assert len(ids) == len(set(ids)) == 141
    assert all(feature["geometry"] for feature in source["features"])


def test_raw_geometry_inventory_and_operational_inventory(artifacts):
    source, reconciliation, _, _ = artifacts
    assert source["raw_geometry_inventory"] == {"Polygon": 137, "MultiGeometry": 4}
    assert reconciliation["operational_geometry_inventory"] == {
        "MultiPolygon": 4,
        "Polygon": 137,
    }


def test_fid_82_identity_and_source_attributes_are_unchanged(artifacts):
    source, _, governed, _ = artifacts
    raw = feature_by_fid(source, 82)
    operational = feature_by_fid(governed, 82)
    assert raw["properties"]["name_ar"] == "ترية"
    assert raw["properties"]["source_attributes"]["المساحة (هكتار)"] == "79.23"
    assert operational["properties"]["name_ar"] == "ترية"
    assert operational["properties"]["area_hectares_source"] == "79.23"
    assert operational["properties"]["institutional_id"] == "atlas-investment-area-fid-0082"


def test_fid_82_invalid_raw_geometry_is_detected_and_preserved(artifacts):
    source, reconciliation, governed, _ = artifacts
    raw = feature_by_fid(source, 82)
    operational = feature_by_fid(governed, 82)
    assert shape(raw["geometry"]).is_valid is False
    assert "Self-intersection" in raw["properties"]["source_geometry_validity_reason"]
    repair = reconciliation["fid_82_geometry_repair"]
    assert repair["before"]["geojson"] == raw["geometry"]
    assert repair["before"]["geojson_sha256"] == raw["properties"]["source_geometry_geojson_sha256"]
    assert repair["raw_source_overwritten"] is False
    assert repair["after"]["geojson"] == operational["geometry"]


def test_fid_82_repair_is_valid_minimal_and_polygonal(artifacts):
    _, reconciliation, governed, _ = artifacts
    operational = feature_by_fid(governed, 82)
    repaired = shape(operational["geometry"])
    repair = reconciliation["fid_82_geometry_repair"]
    assert repaired.is_valid and not repaired.is_empty
    assert repaired.geom_type in {"Polygon", "MultiPolygon"}
    assert repair["accepted"] is True
    assert repair["source_geometry_status"] == "SOURCE_INVALID_TOPOLOGY"
    assert repair["operational_geometry_status"] == "VALIDATED_REPAIRED"
    assert repair["repair_approval_basis"] == areas.REPAIR_BASIS
    assert repair["before"]["vertex_count"] == 472
    assert repair["after"]["vertex_count"] == 471
    assert repair["before"]["bounds"] == repair["after"]["bounds"]
    assert abs(repair["area_delta_percent"]) <= 0.000001
    assert repair["centroid_shift_degrees"] <= 0.000000001
    assert repair["symmetric_difference_area_square_degrees"] <= 0.000000000001


def test_fid_103_correction_is_present(artifacts):
    source, _, governed, _ = artifacts
    raw = feature_by_fid(source, 103)
    operational = feature_by_fid(governed, 103)
    assert raw["properties"]["name_ar"] == "وادي الخبطة"
    assert raw["properties"]["source_attributes"]["المساحة (هكتار)"] == "11"
    assert raw["geometry"]["type"] == "Polygon"
    assert operational["properties"]["name_ar"] == "وادي الخبطة"


def test_all_governed_records_are_approved_but_not_published(artifacts):
    _, reconciliation, governed, _ = artifacts
    assert reconciliation["authority_status"] == "APPROVED"
    assert reconciliation["review_status"] == "APPROVED"
    assert reconciliation["canonical_identity_approved"] is True
    assert reconciliation["publication_approved"] is False
    for feature in governed["features"]:
        properties = feature["properties"]
        assert properties["authority_status"] == "APPROVED"
        assert properties["review_status"] == "APPROVED"
        assert properties["canonical_identity_approved"] is True
        assert properties["publication_approved"] is False
        assert properties["is_published"] is False
        assert properties["source_metadata"]["source_excel_identity"]["sha256"] == areas.EXCEL_SHA256
        assert properties["source_metadata"]["source_kml_identity"]["sha256"] == areas.KML_SHA256


def test_deprecated_project_and_mixed_sources_are_excluded(artifacts):
    source, *_ = artifacts
    assert source["deprecated_sources_used"] is False
    assert source["gdb_geometry_authority_used"] is False
    assert source["individual_investment_projects_included"] is False
    serialized = str(source)
    assert "المشاريع_السياحية_الاستثمارية" not in serialized
    assert "المشاريع وفرص الاستثمار السياحي" not in serialized


def test_ingestion_contract_accepts_all_141(artifacts):
    _, _, governed, _ = artifacts
    validated = ingestion.validate_geojson(areas.IMPORT, areas.LAYER_CODE)
    assert len(validated.features) == 141
    assert {feature.geometry_type for feature in validated.features} == {"POLYGON", "MULTIPOLYGON"}


def test_cross_layer_records_are_candidates_not_institutional_relationships(artifacts):
    *_, cross = artifacts
    assert cross["comparison_layers"] == ["HOTELS", "TOURISM_RESORTS", "PARKS"]
    assert cross["spatial_containment_candidate_count"] == len(cross["records"])
    assert cross["institutional_relationships_created"] == 0
    assert all(record["relationship"] == "SPATIAL_CONTAINMENT_CANDIDATE" for record in cross["records"])
    assert all(record["institutional_relationship_established"] is False for record in cross["records"])


def test_registry_and_api_contract_support_authoritative_polygons():
    layer = require_layer(areas.LAYER_CODE)
    assert layer.name_ar == areas.SEMANTIC_NAME_AR
    assert layer.name_en == areas.SEMANTIC_NAME_EN
    assert layer.allowed_geometry_types == frozenset({"POLYGON", "MULTIPOLYGON"})
    paths = {route.path for route in governed_gis_router.routes}
    assert "/gis/layers/{layer_code}/features" in paths
    assert "/gis/layers/{layer_code}/geojson" in paths
    assert "/gis/layers/{layer_code}/bbox" in paths
