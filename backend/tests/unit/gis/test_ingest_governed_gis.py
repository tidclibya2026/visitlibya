import json
from pathlib import Path

import pytest

from app.models.governed_gis_feature import GovernedGISFeature
from scripts import ingest_governed_gis as ingestion


def feature(*, geometry=None, code="site-1", institutional_id="institution-1"):
    return {
        "type": "Feature",
        "properties": {
            "feature_code": code,
            "institutional_id": institutional_id,
            "source_feature_id": "source-1",
            "name_en": "Synthetic Site",
        },
        "geometry": geometry or {"type": "Point", "coordinates": [13, 32]},
    }


def write_geojson(path: Path, features: list[dict]) -> Path:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )
    return path


class Rows:
    def __init__(self, rows): self.rows = rows
    def all(self): return self.rows


class FakeSession:
    def __init__(self, rows=()):
        self.rows = list(rows); self.added = []; self.commits = 0; self.rollbacks = 0
    def scalars(self, _statement): return Rows(self.rows)
    def add(self, entity): self.added.append(entity)
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1
    def close(self): pass


def test_invalid_geometry_type_for_layer(tmp_path: Path):
    path = write_geojson(
        tmp_path / "input.geojson",
        [
            feature(
                geometry={
                    "type": "LineString",
                    "coordinates": [[13, 32], [14, 33]],
                }
            )
        ],
    )
    with pytest.raises(ingestion.GovernedGISIngestionError, match="not allowed"):
        ingestion.validate_geojson(path, "WORLD_HERITAGE")


def test_specialized_layer_rejects_generic_ingestion(tmp_path: Path):
    path = write_geojson(tmp_path / "input.geojson", [feature()])
    with pytest.raises(ingestion.GovernedGISIngestionError, match="specialized"):
        ingestion.validate_geojson(path, "LIBYA_BOUNDARY")


def test_invalid_coordinates_fail(tmp_path: Path):
    path = write_geojson(
        tmp_path / "input.geojson",
        [feature(geometry={"type": "Point", "coordinates": [181, 32]})],
    )
    with pytest.raises(ingestion.GovernedGISIngestionError, match="WGS84"):
        ingestion.validate_geojson(path, "NATURAL_SITES")


def test_duplicate_feature_identity_fails(tmp_path: Path):
    path = write_geojson(tmp_path / "input.geojson", [feature(), feature()])
    with pytest.raises(ingestion.GovernedGISIngestionError, match="Duplicate"):
        ingestion.validate_geojson(path, "NATURAL_SITES")


def test_dry_run_does_not_open_database(tmp_path: Path):
    path = write_geojson(tmp_path / "input.geojson", [feature()])
    def forbidden(): raise AssertionError("database opened")
    result = ingestion.ingest(
        geojson_path=path, layer_code="NATURAL_SITES",
        source_layer="synthetic-test", dry_run=True, session_factory=forbidden,
    )
    assert len(result.features) == 1


def test_default_ingestion_is_validated_but_unapproved_and_unpublished(tmp_path: Path):
    path = write_geojson(tmp_path / "input.geojson", [feature()])
    session = FakeSession()
    ingestion.ingest(
        geojson_path=path, layer_code="NATURAL_SITES",
        source_layer="synthetic-test", session_factory=lambda: session,
    )
    entity = session.added[0]
    assert entity.is_validated is True
    assert entity.is_published is False
    assert entity.authority_status.value == "unapproved"
    assert session.commits == 1


def test_institutionally_approved_ingestion_remains_unpublished(tmp_path: Path):
    approved = feature()
    approved["properties"].update({
        "authority_status": "APPROVED",
        "review_status": "APPROVED",
        "canonical_identity_approved": True,
        "publication_approved": False,
        "is_published": False,
    })
    path = write_geojson(tmp_path / "approved.geojson", [approved])
    session = FakeSession()
    ingestion.ingest(
        geojson_path=path,
        layer_code="NATURAL_SITES",
        source_layer="approved-synthetic-test",
        institutionally_approved=True,
        session_factory=lambda: session,
    )
    entity = session.added[0]
    assert entity.review_status.value == "approved"
    assert entity.authority_status.value == "approved"
    assert entity.is_validated is True
    assert entity.is_published is False
    assert session.commits == 1


def test_approved_ingestion_fails_closed_without_exact_governance_fields(tmp_path: Path):
    path = write_geojson(tmp_path / "not-approved.geojson", [feature()])
    with pytest.raises(
        ingestion.GovernedGISIngestionError,
        match="Institutionally approved ingestion requires",
    ):
        ingestion.ingest(
            geojson_path=path,
            layer_code="NATURAL_SITES",
            source_layer="synthetic-test",
            institutionally_approved=True,
        )


def test_idempotent_update_does_not_duplicate(tmp_path: Path):
    path = write_geojson(tmp_path / "input.geojson", [feature()])
    existing = GovernedGISFeature(
        feature_code="site-1", institutional_id="institution-1", is_published=False
    )
    session = FakeSession([existing])
    ingestion.ingest(
        geojson_path=path, layer_code="NATURAL_SITES",
        source_layer="synthetic-test", session_factory=lambda: session,
    )
    assert not session.added
    assert existing.is_published is False
    assert session.commits == 1


def test_published_record_cannot_be_overwritten(tmp_path: Path):
    path = write_geojson(tmp_path / "input.geojson", [feature()])
    existing = GovernedGISFeature(
        feature_code="site-1", institutional_id="institution-1", is_published=True
    )
    session = FakeSession([existing])
    with pytest.raises(ingestion.GovernedGISIngestionError, match="Published"):
        ingestion.ingest(
            geojson_path=path, layer_code="NATURAL_SITES",
            source_layer="synthetic-test", session_factory=lambda: session,
        )
    assert session.rollbacks == 1
