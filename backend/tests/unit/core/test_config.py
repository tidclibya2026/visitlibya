import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.db.session import engine_options


def test_pool_configuration_is_validated() -> None:
    configured = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://test:test@localhost/test_database",
        jwt_secret_key="x" * 32,
        db_pool_size=4,
        db_max_overflow=2,
        db_pool_timeout=15,
        db_pool_recycle=900,
        db_pool_pre_ping=False,
    )
    assert configured.db_pool_size == 4
    assert configured.db_max_overflow == 2
    assert configured.db_pool_pre_ping is False

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://test:test@localhost/test_database",
            jwt_secret_key="x" * 32,
            db_pool_size=0,
        )


def test_engine_options_skip_sqlite_and_apply_postgresql_pool_settings() -> None:
    assert engine_options("sqlite+pysqlite:///:memory:") == {}
    options = engine_options("postgresql+psycopg://test:test@localhost/test_database")
    assert options == {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": settings.db_pool_pre_ping,
    }
