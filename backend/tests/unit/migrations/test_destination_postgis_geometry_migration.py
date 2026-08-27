from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[3]
VERSIONS_DIR = BACKEND_DIR / "alembic" / "versions"

INITIAL_MIGRATION = (
    VERSIONS_DIR / "24ed546b1ce8_create_core_tourism_tables.py"
)

BACKFILL_MIGRATION = (
    VERSIONS_DIR / "3ce91b819d4a_add_destination_postgis_geometry.py"
)


def _initial_source() -> str:
    return INITIAL_MIGRATION.read_text(encoding="utf-8")


def _backfill_source() -> str:
    return BACKFILL_MIGRATION.read_text(encoding="utf-8")


def test_initial_schema_owns_postgis_extension() -> None:
    source = _initial_source()

    assert "CREATE EXTENSION IF NOT EXISTS postgis" in source


def test_initial_schema_owns_destination_point_geometry() -> None:
    source = _initial_source()

    assert "sa.Column('geometry'" in source
    assert "geometry_type='POINT'" in source
    assert "srid=4326" in source


def test_initial_schema_owns_destination_gist_index() -> None:
    source = _initial_source()

    assert "'idx_destinations_geometry'" in source
    assert "postgresql_using='gist'" in source


def test_backfill_migration_follows_current_head() -> None:
    source = _backfill_source()

    assert 'down_revision: str | None = "16af7df9200c"' in source


def test_backfill_populates_geometry_from_valid_coordinates() -> None:
    source = _backfill_source()

    assert "ST_MakePoint(longitude, latitude)" in source
    assert "ST_SetSRID" in source
    assert "longitude BETWEEN -180 AND 180" in source
    assert "latitude BETWEEN -90 AND 90" in source
    assert "geometry IS NULL" in source


def test_backfill_does_not_recreate_spatial_schema() -> None:
    source = _backfill_source()

    assert "op.add_column" not in source
    assert "op.create_index" not in source
    assert "CREATE EXTENSION" not in source


def test_backfill_downgrade_preserves_original_spatial_schema() -> None:
    source = _backfill_source()

    assert "op.drop_column" not in source
    assert "op.drop_index" not in source
    assert "DROP EXTENSION" not in source
