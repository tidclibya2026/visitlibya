from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import Settings, settings


def engine_options(database_url: str, config: Settings = settings) -> dict[str, object]:
    if make_url(database_url).get_backend_name() == "sqlite": return {}
    connect_args: dict[str, object] = {"connect_timeout": config.database_connect_timeout}
    if config.database_ssl_mode: connect_args["sslmode"] = config.database_ssl_mode
    return {"pool_size": config.database_pool_size, "max_overflow": config.database_max_overflow,
            "pool_timeout": config.database_pool_timeout, "pool_recycle": config.database_pool_recycle,
            "pool_pre_ping": config.database_pool_pre_ping, "pool_use_lifo": True,
            "connect_args": connect_args, "echo": False}


def create_database_engine(config: Settings = settings) -> Engine:
    return create_engine(config.database_url, **engine_options(config.database_url, config))


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try: yield db
    finally: db.close()


def dispose_engine() -> None: engine.dispose()
