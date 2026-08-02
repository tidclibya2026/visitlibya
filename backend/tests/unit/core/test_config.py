import pytest
from pydantic import ValidationError
from app.core.config import Settings, settings
from app.db.session import engine_options

BASE = {"_env_file": None, "database_url": "postgresql+psycopg://test:test@localhost/test_database",
        "jwt_secret_key": "x" * 32}


def test_pool_configuration_is_validated() -> None:
    configured = Settings(**BASE, database_pool_size=4, database_max_overflow=2,
                          database_pool_timeout=15, database_pool_recycle=900,
                          database_pool_pre_ping=False)
    assert configured.database_pool_size == 4
    assert configured.database_max_overflow == 2
    with pytest.raises(ValidationError): Settings(**BASE, database_pool_size=0)


def test_engine_options_skip_sqlite_and_apply_postgresql_settings() -> None:
    assert engine_options("sqlite+pysqlite:///:memory:") == {}
    options = engine_options("postgresql+psycopg://test:test@localhost/test_database")
    assert options["pool_size"] == settings.database_pool_size
    assert options["pool_pre_ping"] is settings.database_pool_pre_ping
    assert options["connect_args"]["connect_timeout"] == settings.database_connect_timeout
    assert options["echo"] is False


def production_settings(**overrides: object) -> Settings:
    values = {
        "_env_file": None, "app_env": "production", "debug": False,
        "database_url": "postgresql+psycopg://user:password@db.example.test/visitlibya",
        "jwt_secret_key": "A9!bC2@dE3#fG4$hI5%jK6^lM7&nO8*pQ9(rS0)tU1+vW2=xY",
        "cors_origins": ["https://tidclibya2026.github.io"],
        "trusted_hosts": ["api.example.test"], "forwarded_allow_ips": ["10.0.0.10"],
    }
    values.update(overrides)
    return Settings(**values)


def test_production_defaults_disable_docs_and_debug() -> None:
    configured = production_settings()
    assert configured.debug is False
    assert configured.enable_docs is False
    assert configured.enable_redoc is False
    assert configured.enable_openapi is False
    assert "jwt_secret_key=" not in repr(configured)
    assert "database_url" not in repr(configured).lower()


@pytest.mark.parametrize("overrides", [
    {"debug": True}, {"database_url": "postgresql+psycopg://u:p@localhost/db"},
    {"database_url": "sqlite:///bad.db"}, {"cors_origins": ["*"]},
    {"cors_origins": ["https://tidclibya2026.github.io/visitlibya/"]},
    {"trusted_hosts": ["*"]}, {"forwarded_allow_ips": ["*"]},
    {"trusted_hosts": ["https://api.example.test"]},
    {"forwarded_allow_ips": ["proxy.example.test"]},
    {"jwt_secret_key": "placeholder-secret-that-is-definitely-not-production-safe"},
])
def test_unsafe_production_configuration_is_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError): production_settings(**overrides)


def test_missing_production_database_and_secret_are_rejected() -> None:
    values = {"_env_file": None, "app_env": "production",
              "cors_origins": ["https://tidclibya2026.github.io"],
              "trusted_hosts": ["api.example.test"], "forwarded_allow_ips": ["10.0.0.10"]}
    with pytest.raises(ValidationError): Settings(**values)


@pytest.mark.parametrize("missing", ["debug", "cors_origins", "trusted_hosts"])
def test_production_requires_explicit_security_settings(missing: str) -> None:
    values = {
        "_env_file": None, "app_env": "production", "debug": False,
        "database_url": "postgresql+psycopg://u:p@db.example.test/db",
        "jwt_secret_key": "A9!bC2@dE3#fG4$hI5%jK6^lM7&nO8*pQ9(rS0)tU1+vW2=xY",
        "cors_origins": ["https://tidclibya2026.github.io"],
        "trusted_hosts": ["api.example.test"], "forwarded_allow_ips": ["10.0.0.10"],
    }
    del values[missing]
    with pytest.raises(ValidationError): Settings(**values)
