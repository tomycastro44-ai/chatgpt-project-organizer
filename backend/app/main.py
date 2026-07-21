from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import create_database_engine, initialize_database


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(settings.database_url)
        initialize_database(engine)
        app.state.database_engine = engine
        yield
        engine.dispose()

    application = FastAPI(
        title=settings.app_name,
        version="0.5.0",
        description="Functional import, deterministic evidence, semantic memory, reviewable proposals, simulated application, audit and Undo for ChatGPT Project Organizer.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    application.include_router(api_router, prefix=settings.api_prefix)

    @application.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"service": settings.app_name, "status": "ready"}

    return application


app = create_app()
