import json

from scripts import ingest_governed_gis as ingestion
from scripts import old_tripoli_governed_layer as layer


def test_reconciliation_fingerprint_is_line_ending_independent():
    lf = b'{\n  "records": [1, 2],\n  "status": "review"\n}\n'
    crlf = lf.replace(b"\n", b"\r\n")
    assert layer.reconciliation_fingerprint(lf) == layer.reconciliation_fingerprint(crlf)


def test_artifacts_are_deterministic_complete_and_fail_closed():
    imported, blocked = layer.validate()
    assert imported["evidence_count"] == 430
    assert len(imported["features"]) + len(blocked["records"]) == 430
    assert imported["publication_approved"] is False
    assert imported["authoritative_boundary_claimed"] is False
    assert imported["historic_or_visitor_route_claimed"] is False
    assert sum(imported["category_counts"].values()) == 430


def test_only_safe_unconflicted_points_are_ingestible():
    imported, blocked = layer.validate()
    assert imported["features"]
    assert {item["geometry"]["type"] for item in imported["features"]} == {"Point"}
    assert all(len(item["geometry"]["coordinates"]) == 2 for item in imported["features"])
    assert all(item["properties"]["source_metadata"]["source_geometry"] for item in imported["features"])
    assert {item["properties"]["review_classification"] for item in imported["features"]} == {"SAFE_POINT_CANDIDATE"}
    assert all(item["review_classification"] != "SAFE_POINT_CANDIDATE" for item in blocked["records"])


def test_blocked_inventory_preserves_all_non_ingested_geometry_and_provenance():
    imported, blocked = layer.validate()
    assert len({item["source_ordinal"] for item in blocked["records"]}) == len(blocked["records"])
    assert all(item["geometry"] and item["source_metadata"]["source_reference"] for item in blocked["records"])
    assert imported["category_counts"]["CONTEXTUAL_LINE"] == 236
    assert imported["category_counts"]["UNRESOLVED_ROUTE_SEMANTICS"] >= 1
    assert imported["category_counts"]["UNRESOLVED_POLYGON"] >= 1
    assert imported["category_counts"]["NON_AUTHORITATIVE_BOUNDARY"] >= 1


def test_import_passes_governed_ingestion_contract(tmp_path):
    imported, _ = layer.build()
    path = tmp_path / "old-tripoli.geojson"
    path.write_text(json.dumps(imported, ensure_ascii=False), encoding="utf-8")
    validated = ingestion.validate_geojson(path, "OLD_TRIPOLI")
    assert len(validated.features) == len(imported["features"])
    assert {feature.geometry_type for feature in validated.features} == {"POINT"}
