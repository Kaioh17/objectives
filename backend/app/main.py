import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.core.logging_config import setup_logging
from app.router import api_router, health

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

OPENAPI_TAGS = [
    {"name": "health", "description": "Service liveness."},
    {"name": "auth", "description": "Registration, login, logout and Google sign-in."},
    {"name": "users", "description": "The signed-in user's own profile."},
    {"name": "objectives", "description": "Objectives and their Google Calendar events."},
    {"name": "calendar", "description": "Google Calendar connection and schedule."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Started %s v%s [%s]", settings.app_name, settings.app_version, settings.environment
    )
    yield
    engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Objectives API: cookie sessions, Google sign-in and Google Calendar.",
        debug=settings.debug,
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )

    # Origins come from the CORS env var
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    app.include_router(health.router)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
