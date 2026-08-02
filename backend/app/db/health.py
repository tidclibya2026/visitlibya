from pathlib import Path
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def check_database_connection(db_engine: Engine = engine) -> bool:
    try:
        with db_engine.connect() as connection:
            if connection.dialect.name == "postgresql":
                connection.execute(text("SET statement_timeout = '3000ms'"))
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def check_postgis(db_engine: Engine = engine) -> bool:
    try:
        with db_engine.connect() as connection:
            if connection.dialect.name != "postgresql":
                return False
            return connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')")) is True
    except SQLAlchemyError:
        return False


def migration_is_current(db_engine: Engine = engine) -> bool:
    try:
        config = Config(str(BACKEND_ROOT / "alembic.ini"))
        scripts = ScriptDirectory.from_config(config)
        heads = set(scripts.get_heads())
        with db_engine.connect() as connection:
            current = set(MigrationContext.configure(connection).get_current_heads())
        return bool(heads) and current == heads
    except Exception:
        return False
