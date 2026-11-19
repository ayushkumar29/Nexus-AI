"""FastAPI main application setup and lifecycle configuration."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nexus_ai")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} (env: {settings.APP_ENV}, v{settings.APP_VERSION})")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application(settings: Settings | None = None) -> FastAPI:
    """Factory function for FastAPI application initialization."""
    current_settings = settings or get_settings()

    app = FastAPI(
        title=current_settings.APP_NAME,
        version=current_settings.APP_VERSION,
        description="Enterprise-grade AI Knowledge Assistant Backend API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    register_exception_handlers(app)

    # Mount API routers
    app.include_router(api_router, prefix="/api")

    return app


app = create_application()
