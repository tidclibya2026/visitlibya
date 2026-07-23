from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def engine_options(database_url: str) -> dict[str, object]:
    """Return production pool options without breaking SQLite test engines."""
    if make_url(database_url).get_backend_name() == "sqlite":
        return {}
    # Approximate connection ceiling:
    # workers * containers * (pool_size + max_overflow).
    return {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": settings.db_pool_pre_ping,
    }


engine = create_engine(settings.database_url, **engine_options(settings.database_url))

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
