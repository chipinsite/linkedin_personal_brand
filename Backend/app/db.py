from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(database_url: str) -> dict:
    kwargs = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


def _create_engine_with_local_fallback():
    primary_url = settings.database_url
    primary_engine = create_engine(primary_url, **_engine_kwargs(primary_url))
    is_local_dev = settings.app_env.lower() == "dev"
    if is_local_dev and not primary_url.startswith("sqlite"):
        try:
            with primary_engine.connect():
                pass
        except SQLAlchemyError:
            fallback_url = "sqlite+pysqlite:///./local_dev.db"
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
