import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "backend/scripts/tourism_investment_areas_governed_layer.py"
SPEC = importlib.util.spec_from_file_location("tourism_investment_areas_governed_layer", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


@pytest.fixture(scope="module")
def artifacts():
    return MODULE.validate()


def test_source_preserves_exact_corrected_authorities(artifacts):
    source, *_ = artifacts
    assert source["source_feature_count"] == 177
    assert source["excel_record_count"] == 141
    assert source["gdb_area_record_count"] == 36
    assert source["excluded_deprecated_gdb_project_count"] == 10
    assert MODULE.DEPRECATED_GDB_LAYER not in {
        feature["properties"]["source_layer"] for feature in source["features"]
    }
    assert all(
        feature["properties"].get("source_database") != "المشاريع وفرص الاستثمار السياحي.kml"
        for feature in source["features"]
    )


def test_workbook_inventory_is_exact(artifacts):
    _, reconciliation, *_ = artifacts
    quality = reconciliation["workbook_quality"]
    assert quality["sheet_names"] == ["Sheet1"]
    assert quality["column_names"] == MODULE.EXPECTED_COLUMNS
    assert quality["unique_area_name_count"] == 140
    assert quality["missing_name_count"] == 1
    assert quality["duplicate_name_group_count"] == 0
    assert quality["fid_coverage_count"] == 133
    assert quality["fid_missing_count"] == 8
    assert quality["xy_coverage_count"] == 141
    assert quality["area_hectare_coverage_count"] == 141
    assert quality["calculated_square_kilometre_coverage_count"] == 141
    assert quality["area_value_inconsistency_count"] == 10
    assert quality["source_values_repaired"] is False


def test_reconciliation_accounting_is_complete(artifacts):
    _, reconciliation, governed_import, governed_blocked, _ = artifacts
    assert reconciliation["matched_count"] == 31
    assert reconciliation["excel_only_count"] == 110
    assert reconciliation["gdb_only_count"] == 5
    assert reconciliation["matched_count"] + reconciliation["excel_only_count"] == 141
    assert reconciliation["matched_count"] + reconciliation["gdb_only_count"] == 36
    assert len(governed_import["features"]) + len(governed_blocked["records"]) == 146


def test_fid_and_coordinates_are_not_used_as_identity_matches(artifacts):
    _, reconciliation, *_ = artifacts
    assert reconciliation["matching_policy"]["fid"] == "NOT_USED_INCOMPATIBLE_SOURCE_NAMESPACES"
    assert reconciliation["matching_policy"]["coordinates"] == "CORROBORATING_EVIDENCE_ONLY_NOT_A_MATCH_KEY_OR_BOUNDARY"
    assert reconciliation["matching_policy"]["approximate_name_matching"] is False
    assert all(match["fid_match_used"] is False for match in reconciliation["matches"])
    assert all(record["nearest_excel_coordinate_candidate"]["match_created"] is False for record in reconciliation["gdb_only"])


def test_gdb_geometry_is_preserved_without_boundary_claim(artifacts):
    source, reconciliation, governed_import, governed_blocked, _ = artifacts
    assert reconciliation["gdb_geometry_inventory"] == {
        "Point": 36,
        "Polygon": 0,
        "authoritative_boundary_claimed_count": 0,
        "valid_wgs84_reference_point_count": 36,
    }
    source_gdb = {
        feature["properties"]["source_feature_id"]: feature["geometry"]
        for feature in source["features"]
        if feature["properties"].get("source_layer") == MODULE.GDB_AREA_LAYER
    }
    for feature in governed_import["features"]:
        assert feature["geometry"] == source_gdb[feature["properties"]["source_feature_id"]]
        assert feature["properties"]["source_metadata"]["authoritative_boundary_claimed"] is False
    assert all(record.get("representative_coordinate_boundary_claimed") is False for record in governed_blocked["records"] if "representative_coordinate_boundary_claimed" in record)


def test_safe_and_blocked_classifications_are_deterministic(artifacts):
    _, _, governed_import, governed_blocked, _ = artifacts
    assert len(governed_import["features"]) == 29
    assert len(governed_blocked["records"]) == 117
    assert governed_import["classification_counts"] == {
        "EXCEL_ONLY_NO_AUTHORITATIVE_GDB_GEOMETRY_REVIEW": 109,
        "GDB_ONLY_IDENTITY_RECONCILIATION_REVIEW": 5,
        "MISSING_IDENTITY_REVIEW": 1,
        "SAFE_INVESTMENT_AREA_REFERENCE_POINT": 29,
        "SAME_GEOMETRY_DIFFERENT_IDENTITY_REVIEW": 2,
    }


def test_all_artifacts_remain_unapproved_and_unpublished(artifacts):
    source, reconciliation, governed_import, governed_blocked, cross = artifacts
    for artifact in (source, reconciliation, governed_import, governed_blocked, cross):
        assert artifact["publication_approved"] is False
        assert artifact["canonical_identity_approved"] is False
        assert artifact["authoritative_boundary_claimed"] is False
    assert all(feature["properties"]["source_metadata"]["publication_approved"] is False for feature in governed_import["features"])


def test_cross_layer_review_never_infers_containment(artifacts):
    *_, cross = artifacts
    assert cross["comparison_layers"] == ["HOTELS", "TOURISM_RESORTS", "PARKS"]
    assert cross["polygon_containment_relationship_count"] == 0
    assert cross["polygon_containment_reason"] == "SOURCE_GDB_AREA_LAYER_CONTAINS_POINTS_ONLY"
    assert all(record["relationship"] == "CROSS_LAYER_REFERENCE" for record in cross["records"])
