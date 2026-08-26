from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_repository_has_one_linear_alembic_head() -> None:
    backend_root = Path(__file__).resolve().parents[3]
    scripts = ScriptDirectory.from_config(Config(str(backend_root / "alembic.ini")))
    heads = scripts.get_heads()
    assert len(heads) == 1
    assert scripts.get_revision(heads[0]) is not None
