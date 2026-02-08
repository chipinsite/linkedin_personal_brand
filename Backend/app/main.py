import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .logging_config import configure_logging
from .middleware.request_id import RequestIdMiddleware
from .routes import admin, comments, drafts, engagement, health, learning, posts, reports, sources
from .services.db_check import SchemaError, startup_schema_check

# Configure logging before anything else uses it.
# In prod, default to JSON format; in dev, use human-readable unless explicitly overridden.
_use_json = settings.log_json or settings.app_env == "prod"
configure_logging(level=settings.log_level, json_format=_use_json)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="LinkedIn Personal Brand Autoposter")

    # Request ID tracing — added before CORS so the ID is available to all middleware.
    app.add_middleware(RequestIdMiddleware)

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

logger.info(
    "App started: env=%s log_level=%s log_json=%s db=%s",
    settings.app_env,
    settings.log_level,
    _use_json,
    str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url),
)

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

# Startup schema validation: log clear error if tables are missing.
# In dev mode with auto_create_tables, skip check since tables were just created.
if not settings.auto_create_tables:
    try:
        startup_schema_check(engine)
    except SchemaError as exc:
        logger.warning("Startup schema check failed: %s — app will continue but requests may fail.", exc)
