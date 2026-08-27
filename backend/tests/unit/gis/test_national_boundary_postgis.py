from pathlib import Path

from geoalchemy2 import Geometry

from app.models.national_boundary import NationalBoundary


def test_national_boundary_model_uses_postgis_multipolygon():
    geometry = NationalBoundary.__table__.c.geometry.type

    assert isinstance(geometry, Geometry)
    assert geometry.geometry_type == "MULTIPOLYGON"
    assert geometry.srid == 4326


def test_national_boundary_country_code_is_unique():
    column = NationalBoundary.__table__.c.country_code

    assert column.unique is True


def test_national_boundary_publication_defaults_are_blocked():
    validated = NationalBoundary.__table__.c.is_validated
    published = NationalBoundary.__table__.c.is_published

    assert str(validated.server_default.arg) == "false"
    assert str(published.server_default.arg) == "false"


def test_national_boundary_migration_has_spatial_guards():
    root = Path(__file__).resolve().parents[3]

    migration = (
        root
        / "alembic"
        / "versions"
        / "7b5f24c91a10_create_national_boundaries.py"
    ).read_text(encoding="utf-8")

    assert "ST_IsValid(geometry)" in migration
    assert "ST_SRID(geometry) = 4326" in migration
    assert "MULTIPOLYGON" in migration
    assert "postgresql_using=\"gist\"" in migration
