from fastapi import FastAPI

from .config import settings
from .db import Base, engine
from .routes import admin, comments, drafts, engagement, health, learning, posts, reports, sources


def create_app() -> FastAPI:
    app = FastAPI(title="LinkedIn Personal Brand Autoposter")

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
