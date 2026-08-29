from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "alembic" / "versions" / "8d4e2c7a1f60_create_governed_gis_features.py"
APPROVED_REVIEW_MIGRATION = (
    ROOT / "alembic" / "versions" / "b71d38f204aa_add_approved_gis_review_status.py"
)


def test_governed_gis_migration_is_single_head():
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert scripts.get_heads() == ["b71d38f204aa"]


def test_governed_gis_migration_has_spatial_and_publication_guards():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'geometry_type="GEOMETRY"' in source
    assert 'srid=4326' in source
    assert 'postgresql_using="gist"' in source
    assert "ST_IsValid(geometry)" in source
    assert "NOT is_published OR" in source
    assert "uq_governed_gis_layer_feature" in source


def test_approved_review_status_migration_is_scoped_and_reversible():
    source = APPROVED_REVIEW_MIGRATION.read_text(encoding="utf-8")
    assert "8d4e2c7a1f60" in source
    assert "'draft', 'under_review', 'reviewed', 'approved'" in source
    assert "WHERE review_status = 'approved'" in source

