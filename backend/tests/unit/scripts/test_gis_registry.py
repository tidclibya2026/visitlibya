import json
from pathlib import Path

import pytest

from scripts.audit_institutional_gis import main
from scripts.canonical_gis_review import build_canonical_review
from scripts.destination_import import ImportDataset
from scripts.gis_registry import (
    SourceSpec,
    SourceManifest,
    SourceAudit,
    audit_sources,
    build_candidates,
    canonical_destinations,
    natural_relationship,
    parse_geojson,
    parse_kml,
    parse_json_registry,
    safe_source_path,
    sha256_bytes,
)


def spec(format="kml", source_id="test-source", filename="source.kml") -> SourceSpec:
    return SourceSpec(source_id=source_id, expected_filename=filename, format=format, title="Test", dataset_role="test", source_scope="test")


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def kml(placemarks: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>{placemarks}</Document></kml>'


def canonical(slug="site", name_en="Site", name_ar="موقع") -> list[dict]:
    dataset = ImportDataset.model_validate({
        "schema_version": 1, "dataset": "test",
        "categories": [{"code": "heritage", "name_ar": "تراث", "name_en": "Heritage"}],
        "records": [{"slug": slug, "category": "heritage", "status": "published", "is_active": True,
                     "translations": [{"language_code": "ar", "name": name_ar}, {"language_code": "en", "name": name_en}]}],
    })
    return canonical_destinations(dataset)


def test_kml_point_coordinate_order(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"
    write(path, kml('<Placemark id="p1"><name>موقع</name><Point><coordinates>14.3,32.6,10</coordinates></Point></Placemark>'))
    features, audit = parse_kml(spec(), path)
    assert (features[0].longitude, features[0].latitude) == (14.3, 32.6)
    assert audit.coordinate_dimensions == {"3": 1}


def test_kml_rejects_entities(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"
    write(path, '<!DOCTYPE kml [<!ENTITY x SYSTEM "file:///secret">]><kml>&x;</kml>')
    with pytest.raises(ValueError, match="forbidden"): parse_kml(spec(), path)


def test_non_point_geometry_never_produces_destination_coordinates(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"
    write(path, kml('<Placemark><name>Area</name><Polygon><outerBoundaryIs><LinearRing><coordinates>14,32 15,32 14,32</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>'))
    features, audit = parse_kml(spec(), path)
    assert features[0].latitude is None and features[0].longitude is None
    assert audit.geometry_types == {"Polygon": 1}


def test_invalid_kml_coordinate_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"
    write(path, kml('<Placemark><Point><coordinates>181,95</coordinates></Point></Placemark>'))
    features, audit = parse_kml(spec(), path)
    assert features[0].latitude is None and audit.invalid_coordinates == 1


def test_geojson_point_order(tmp_path: Path) -> None:
    path = tmp_path / "source.geojson"
    write(path, json.dumps({"type":"FeatureCollection","features":[{"type":"Feature","id":"g1","properties":{"name_ar":"موقع"},"geometry":{"type":"Point","coordinates":[14.3,32.6]}}]}, ensure_ascii=False))
    features, audit = parse_geojson(spec("geojson", filename="source.geojson"), path)
    assert (features[0].longitude, features[0].latitude) == (14.3, 32.6)
    assert audit.geometry_types == {"Point": 1}


def test_natural_atlas_region_is_preserved_as_regional_context(tmp_path: Path) -> None:
    path = tmp_path / "natural.geojson"
    write(path, json.dumps({"type": "FeatureCollection", "features": [{
        "type": "Feature", "properties": {"id": 124, "name": "جسر وادي الكوف القديم", "region_ar": "الجبل الأخضر"},
        "geometry": {"type": "Point", "coordinates": [21.57, 32.69]},
    }]}, ensure_ascii=False))
    source = spec("geojson", "natural-atlas-media", "natural.geojson")
    features, audit = parse_geojson(source, path)
    review = build_canonical_review(canonical("green-mountain", "Green Mountain", "الجبل الأخضر"), features, {source.source_id: source}, {source.source_id: audit})
    candidate = review["destinations"][0]["candidates"][0]
    assert features[0].region == "الجبل الأخضر"
    assert candidate["semantic_scope"] == "REGIONAL_CONTEXT"
    assert review["destinations"][0]["review_status"] == "REVIEW_REQUIRED_AGGREGATE"


def test_invalid_geojson_structure(tmp_path: Path) -> None:
    path = tmp_path / "source.geojson"; write(path, '{"type":"Feature"}')
    with pytest.raises(ValueError, match="FeatureCollection"): parse_geojson(spec("geojson", filename="source.geojson"), path)


def test_duplicate_native_id_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"
    write(path, kml('<Placemark id="same"><name>A</name><Point><coordinates>14,32</coordinates></Point></Placemark><Placemark id="same"><name>B</name><Point><coordinates>15,33</coordinates></Point></Placemark>'))
    _, audit = parse_kml(spec(), path)
    assert audit.duplicate_feature_ids == 1


def test_source_hash_is_raw_sha256() -> None:
    assert sha256_bytes(b"institutional") == "9abeba97a0ceffd5b8cbb5c30966ff60b7984d4ab2b1426883ef0621f5544085"


def test_exact_slug_property_candidate(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"
    write(path, kml('<Placemark><name>Different</name><ExtendedData><Data name="destination_slug"><value>site</value></Data></ExtendedData><Point><coordinates>14,32</coordinates></Point></Placemark>'))
    features, _ = parse_kml(spec(), path)
    candidates, unresolved = build_candidates(canonical(), features, {"test-source": spec()})
    assert candidates[0]["review_status"] == "EXACT_ID" and not unresolved


def test_exact_name_still_requires_review(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"
    write(path, kml('<Placemark><name>Site</name><Point><coordinates>14,32</coordinates></Point></Placemark>'))
    features, _ = parse_kml(spec(), path)
    candidates, _ = build_candidates(canonical(), features, {"test-source": spec()})
    assert candidates[0]["review_status"] == "REVIEW_REQUIRED"


def test_unknown_destination_is_unresolved(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"; write(path, kml('<Placemark><name>Other</name><Point><coordinates>14,32</coordinates></Point></Placemark>'))
    features, _ = parse_kml(spec(), path)
    candidates, unresolved = build_candidates(canonical(), features, {"test-source": spec()})
    assert not candidates and unresolved == {"site": "NO_MATCH"}


def test_aggregate_name_match_requires_aggregate_review(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"; write(path, kml('<Placemark><name>Tadrart Acacus</name><Point><coordinates>10,25</coordinates></Point></Placemark>'))
    features, _ = parse_kml(spec(), path)
    candidates, _ = build_candidates(canonical("acacus", "Tadrart Acacus", "تادرارت أكاكوس"), features, {"test-source": spec()})
    assert candidates[0]["review_status"] == "REVIEW_REQUIRED_AGGREGATE"


def test_natural_base_media_relationship_requires_same_native_ids(tmp_path: Path) -> None:
    base_path = tmp_path / "base.geojson"; media_path = tmp_path / "media.geojson"
    base = {"type":"FeatureCollection","features":[{"type":"Feature","id":"n1","properties":{"name":"Lake"},"geometry":{"type":"Point","coordinates":[14,32]}}]}
    enriched = json.loads(json.dumps(base)); enriched["features"][0]["properties"]["images"] = ["local.jpg"]
    write(base_path, json.dumps(base)); write(media_path, json.dumps(enriched))
    base_features, _ = parse_geojson(spec("geojson", "natural-atlas-base", "base.geojson"), base_path)
    media_features, _ = parse_geojson(spec("geojson", "natural-atlas-media", "media.geojson"), media_path)
    assert natural_relationship(base_features, media_features)["status"] == "PROVEN_SAME_NATIVE_IDS"


def test_geojson_shared_id_precedes_enrichment_id(tmp_path: Path) -> None:
    path = tmp_path / "media.geojson"
    payload = {"type":"FeatureCollection","features":[{"type":"Feature","properties":{"id":667,"attraction_id":"LTA-FEAT-017","name":"خليج بمبة"},"geometry":{"type":"Point","coordinates":[23.2,32.3]}}]}
    write(path, json.dumps(payload, ensure_ascii=False))
    features, _ = parse_geojson(spec("geojson", "natural-atlas-media", "media.geojson"), path)
    assert features[0].source_feature_id == "667"


def test_preview_writes_nothing_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "source.kml"; write(source, kml('<Placemark><name>Site</name><Point><coordinates>14,32</coordinates></Point></Placemark>'))
    manifest = tmp_path / "manifest.json"
    write(manifest, json.dumps({"schema_version":1,"organization":"Center","sources":[spec().model_dump()]}, ensure_ascii=False))
    dataset = tmp_path / "destinations.json"
    write(dataset, json.dumps({"schema_version":1,"dataset":"test","categories":[{"code":"heritage","name_ar":"تراث","name_en":"Heritage"}],"records":[{"slug":"site","category":"heritage","status":"published","is_active":True,"translations":[{"language_code":"ar","name":"موقع"},{"language_code":"en","name":"Site"}]}]}, ensure_ascii=False))
    output = tmp_path / "reports"; before = source.read_bytes()
    assert main(["--source-dir",str(tmp_path),"--manifest",str(manifest),"--dataset",str(dataset),"--output-dir",str(output)]) == 0
    assert source.read_bytes() == before and not output.exists()


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes"): safe_source_path(tmp_path, "../outside.kml")


def test_malformed_source_still_records_hash(tmp_path: Path) -> None:
    path = tmp_path / "source.kml"; write(path, "<kml><broken></kml>")
    manifest = SourceManifest(schema_version=1, organization="Center", sources=[spec()])
    _, audits = audit_sources(manifest, tmp_path)
    assert audits[0].parse_status == "malformed" and len(audits[0].sha256 or "") == 64


def test_supplementary_json_is_audited_without_geographic_features(tmp_path: Path) -> None:
    path = tmp_path / "decisions.json"
    write(path, json.dumps([{"runtime_id":"HOT-1","review_status":"VISUALLY_APPROVED"}]))
    features, audit = parse_json_registry(spec("json", "qa-decisions", "decisions.json"), path)
    assert features == [] and audit.record_count == 1 and audit.feature_count == 0


def test_leptis_site_feature_is_approval_ready_for_human_review(tmp_path: Path) -> None:
    path = tmp_path / "unesco.kml"
    write(path, kml('<Placemark><name>موقع لبدة الأثري (لبتس ماغنا) (لبدة الكبرى)</name><Point><coordinates>14.28,32.63</coordinates></Point></Placemark>'))
    source = spec("kml", "unesco-five-sites-ly", "unesco.kml")
    features, audit = parse_kml(source, path)
    review = build_canonical_review(canonical("leptis-magna", "Leptis Magna", "لبدة الكبرى"), features, {source.source_id: source}, {source.source_id: audit})
    assert review["destinations"][0]["review_status"] == "APPROVAL_READY"
    assert review["destinations"][0]["candidates"][0]["source_sha256"] == audit.sha256


def test_explicit_acacus_destination_feature_is_approval_ready_for_human_review(tmp_path: Path) -> None:
    path = tmp_path / "acacus.kml"
    write(path, kml('<Placemark><name>مواقع تادرارت أكاكوس الصخرية</name><Point><coordinates>10.56,24.81</coordinates></Point></Placemark>'))
    source = spec("kml", "unesco-five-sites-ly", "acacus.kml")
    features, audit = parse_kml(source, path)
    review = build_canonical_review(canonical("acacus", "Tadrart Acacus", "تادرارت أكاكوس"), features, {source.source_id: source}, {source.source_id: audit})
    destination = review["destinations"][0]
    assert destination["review_status"] == "APPROVAL_READY"
    assert destination["best_candidate"]["semantic_scope"] == "DESTINATION_LEVEL_FEATURE"
    assert destination["representation_findings"]["explicit_destination_level_feature"] is True


def test_top_level_ghadames_heritage_identity_is_preserved_and_prioritized(tmp_path: Path) -> None:
    path = tmp_path / "unesco.kml"
    write(path, '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>مواقع التراث العالمي الخمسة_LY</name>'
        '<Folder><name>مواقع التراث العالمي الخمسة</name><Placemark><name>مدينة غدامس القديمة</name><description>النص المؤسسي</description><Point><coordinates>9.496486,30.133674</coordinates></Point></Placemark></Folder>'
        '<Folder><name>غدامس</name><Placemark><name>مدينة غدامس القديمة</name><description>سجل ثانوي</description><Point><coordinates>9.4972408,30.1323647</coordinates></Point></Placemark></Folder>'
        '</Document></kml>')
    source = spec("kml", "unesco-five-sites-ly", "unesco.kml")
    features, audit = parse_kml(source, path)
    review = build_canonical_review(canonical("ghadames", "Ghadames", "غدامس"), features, {source.source_id: source}, {source.source_id: audit})
    destination = review["destinations"][0]
    assert destination["review_status"] == "APPROVAL_READY"
    assert destination["best_candidate"]["source_name"] == "مدينة غدامس القديمة"
    assert destination["candidates"][0]["institutional_semantic_identity"] == "مدينة غدامس القديمة"
    assert destination["candidates"][0]["source_description"] == "النص المؤسسي"
    assert destination["candidates"][1]["semantic_scope"] == "SUB_FEATURE"


def test_aggregate_sub_feature_remains_review_required(tmp_path: Path) -> None:
    path = tmp_path / "acacus.kml"
    write(path, kml('<Placemark><name>وادي أكاكوس</name><Point><coordinates>10.56,24.81</coordinates></Point></Placemark>'))
    source = spec("kml", "acacus-features", "acacus.kml")
    features, audit = parse_kml(source, path)
    review = build_canonical_review(canonical("acacus", "Tadrart Acacus", "تادرارت أكاكوس"), features, {source.source_id: source}, {source.source_id: audit})
    assert review["destinations"][0]["review_status"] == "REVIEW_REQUIRED_AGGREGATE"
    assert review["destinations"][0]["candidates"][0]["semantic_scope"] == "SUB_FEATURE"


def test_no_semantic_candidate_is_no_match() -> None:
    source = spec()
    review = build_canonical_review(canonical(), [], {source.source_id: source}, {source.source_id: SourceAudit(source.source_id, source.expected_filename, "kml", "parsed")})
    assert review["destinations"][0]["review_status"] == "NO_MATCH"
