from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings
from .db_url import backend_local_db_url, normalize_sqlite_url


class Base(DeclarativeBase):
    pass


def _engine_kwargs(database_url: str) -> dict:
    kwargs = {"pool_pre_ping": True, "pool_timeout": 10}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # Set connect_timeout for PostgreSQL to avoid hanging on unreachable DB
        kwargs["connect_args"] = {"connect_timeout": 10}
    return kwargs


def _create_engine_with_local_fallback():
    primary_url = normalize_sqlite_url(settings.database_url)
    primary_engine = create_engine(primary_url, **_engine_kwargs(primary_url))
    is_local_dev = settings.app_env.lower() == "dev"
    if is_local_dev and not primary_url.startswith("sqlite"):
        try:
            with primary_engine.connect():
                pass
        except SQLAlchemyError:
            fallback_url = backend_local_db_url()
            return create_engine(fallback_url, **_engine_kwargs(fallback_url))
    return primary_engine


engine = _create_engine_with_local_fallback()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
