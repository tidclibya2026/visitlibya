import hashlib
import json
from pathlib import Path

import pytest
from shapely.geometry import MultiPolygon

from app.models.national_boundary import NationalBoundary
from scripts import ingest_libya_boundary as ingestion


def write_json(path: Path, geometry: dict | None) -> Path:
    feature = {"type": "Feature", "properties": {}, "geometry": geometry}
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def governed_source(tmp_path: Path, monkeypatch) -> Path:
    source = tmp_path / "libya_national_boundary.shp"
    source.write_bytes(b"governed institutional test geometry")
    digest = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(ingestion, "EXPECTED_SHP_SHA256", digest)
    return source


@pytest.fixture
def polygon() -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[10, 20], [11, 20], [11, 21], [10, 21], [10, 20]]],
    }


class ScalarRows:
    def __init__(self, rows): self.rows = rows
    def all(self): return self.rows


class FakeSession:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.added = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = False
    def scalars(self, _statement): return ScalarRows(self.rows)
    def add(self, value): self.added.append(value)
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1
    def close(self): self.closed = True


def test_governed_sha_matches_accepted_source(governed_source: Path):
    assert ingestion.validate_source_shapefile(governed_source) == ingestion.EXPECTED_SHP_SHA256


def test_sha_mismatch_fails(tmp_path: Path):
    source = tmp_path / "boundary.shp"
    source.write_bytes(b"not governed")
    with pytest.raises(ingestion.BoundaryGovernanceError, match="does not match"):
        ingestion.validate_source_shapefile(source)


def test_missing_source_shapefile_fails(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="shapefile"):
        ingestion.validate_source_shapefile(tmp_path / "missing.shp")


def test_missing_geojson_fails(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="GeoJSON"):
        ingestion.load_geojson_geometry(tmp_path / "missing.geojson")


@pytest.mark.parametrize("count", [0, 2])
def test_feature_collection_requires_exactly_one(tmp_path: Path, polygon: dict, count: int):
    path = tmp_path / "boundary.geojson"
    feature = {"type": "Feature", "geometry": polygon}
    path.write_text(json.dumps({"type": "FeatureCollection", "features": [feature] * count}))
    with pytest.raises(ingestion.BoundaryGovernanceError, match="exactly one"):
        ingestion.load_geojson_geometry(path)


def test_null_geometry_fails(tmp_path: Path):
    with pytest.raises(ingestion.BoundaryGovernanceError, match="missing or null"):
        ingestion.load_geojson_geometry(write_json(tmp_path / "boundary.geojson", None))


def test_unsupported_geometry_fails(tmp_path: Path):
    path = write_json(tmp_path / "boundary.geojson", {"type": "Point", "coordinates": [10, 20]})
    with pytest.raises(ingestion.BoundaryGovernanceError, match="Polygon or MultiPolygon"):
        ingestion.load_geojson_geometry(path)


def test_invalid_geometry_fails(tmp_path: Path):
    bowtie = {"type": "Polygon", "coordinates": [[[0, 0], [2, 2], [0, 2], [2, 0], [0, 0]]]}
    with pytest.raises(ingestion.BoundaryGovernanceError, match="invalid"):
        ingestion.load_geojson_geometry(write_json(tmp_path / "boundary.geojson", bowtie))


def test_polygon_normalizes_to_multipolygon(tmp_path: Path, polygon: dict):
    result = ingestion.load_geojson_geometry(write_json(tmp_path / "boundary.geojson", polygon))
    assert result.original_geometry_type == "Polygon"
    assert isinstance(result.geometry, MultiPolygon)


def test_multipolygon_remains_multipolygon(tmp_path: Path, polygon: dict):
    geometry = {"type": "MultiPolygon", "coordinates": [polygon["coordinates"]]}
    result = ingestion.load_geojson_geometry(write_json(tmp_path / "boundary.geojson", geometry))
    assert result.original_geometry_type == "MultiPolygon"
    assert isinstance(result.geometry, MultiPolygon)


def test_coordinates_outside_global_wgs84_range_fail(tmp_path: Path):
    polygon = {
        "type": "Polygon",
        "coordinates": [[[181, 20], [182, 20], [182, 21], [181, 21], [181, 20]]],
    }
    with pytest.raises(ingestion.BoundaryGovernanceError, match="plausible WGS84"):
        ingestion.load_geojson_geometry(write_json(tmp_path / "boundary.geojson", polygon))


def test_dry_run_performs_no_database_write(tmp_path: Path, governed_source: Path, polygon: dict):
    def forbidden_session(): raise AssertionError("dry-run connected to the database")
    result = ingestion.ingest(
        geojson_path=write_json(tmp_path / "boundary.geojson", polygon),
        source_shp_path=governed_source,
        dry_run=True,
        session_factory=forbidden_session,
    )
    assert result.geometry.geometry.geom_type == "MultiPolygon"


def test_default_ingestion_state_is_validated_and_unpublished(tmp_path: Path, governed_source: Path, polygon: dict):
    session = FakeSession()
    ingestion.ingest(
        geojson_path=write_json(tmp_path / "boundary.geojson", polygon),
        source_shp_path=governed_source,
        session_factory=lambda: session,
    )
    assert len(session.added) == 1
    assert session.added[0].is_validated is True
    assert session.added[0].is_published is False
    assert session.commits == 1


def test_repeated_ingestion_updates_one_unpublished_row(tmp_path: Path, governed_source: Path, polygon: dict):
    boundary = NationalBoundary(name_en="Old", is_published=False)
    session = FakeSession([boundary])
    ingestion.ingest(
        geojson_path=write_json(tmp_path / "boundary.geojson", polygon),
        source_shp_path=governed_source,
        session_factory=lambda: session,
    )
    assert not session.added
    assert boundary.name_en == ingestion.NAME_EN
    assert boundary.is_validated is True
    assert boundary.is_published is False
    assert session.commits == 1


def test_duplicate_ly_database_rows_are_rejected(tmp_path: Path, governed_source: Path, polygon: dict):
    session = FakeSession([NationalBoundary(is_published=False), NationalBoundary(is_published=False)])
    with pytest.raises(ingestion.BoundaryGovernanceError, match="More than one"):
        ingestion.ingest(
            geojson_path=write_json(tmp_path / "boundary.geojson", polygon),
            source_shp_path=governed_source,
            session_factory=lambda: session,
        )
    assert session.commits == 0
    assert session.rollbacks == 1


def test_existing_published_ly_row_is_protected(tmp_path: Path, governed_source: Path, polygon: dict):
    boundary = NationalBoundary(name_en="Existing", is_published=True)
    session = FakeSession([boundary])
    with pytest.raises(ingestion.BoundaryGovernanceError, match="institutional review"):
        ingestion.ingest(
            geojson_path=write_json(tmp_path / "boundary.geojson", polygon),
            source_shp_path=governed_source,
            session_factory=lambda: session,
        )
    assert boundary.name_en == "Existing"
    assert session.rollbacks == 1
