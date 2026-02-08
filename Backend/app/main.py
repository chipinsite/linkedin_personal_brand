import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routes import admin, comments, drafts, engagement, health, learning, posts, reports, sources
from .services.db_check import SchemaError, startup_schema_check

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="LinkedIn Personal Brand Autoposter")
    allowed_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(drafts.router)
    app.include_router(posts.router)
    app.include_router(comments.router)
    app.include_router(sources.router)
    app.include_router(engagement.router)
    app.include_router(learning.router)
    app.include_router(reports.router)
    app.include_router(admin.router)

    return app


app = create_app()


if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

# Startup schema validation: log clear error if tables are missing.
# In dev mode with auto_create_tables, skip check since tables were just created.
if not settings.auto_create_tables:
    try:
        startup_schema_check(engine)
    except SchemaError as exc:
        logger.warning("Startup schema check failed: %s — app will continue but requests may fail.", exc)
