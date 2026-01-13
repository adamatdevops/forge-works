"""ForgeWorks FastAPI Application - Golden Path Orchestrator."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import anomalies, health, kubernetes, metrics, services, templates, websocket
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection
    # TODO: Load ML model
    yield
    # Shutdown
    print(f"Shutting down {settings.app_name}")
    # TODO: Close database connections
    # TODO: Close Redis connection


def create_app() -> FastAPI:
    """Application factory for ForgeWorks."""
    app = FastAPI(
        title=settings.app_name,
        description="Internal Developer Platform - Golden Path Orchestrator",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(
        services.router,
        prefix=f"{settings.api_v1_prefix}/services",
        tags=["Services"],
    )
    app.include_router(
        templates.router,
        prefix=f"{settings.api_v1_prefix}/templates",
        tags=["Templates"],
    )
    app.include_router(
        anomalies.router,
        prefix=f"{settings.api_v1_prefix}/anomalies",
        tags=["Anomalies"],
    )
    app.include_router(
        metrics.router,
        prefix=f"{settings.api_v1_prefix}/metrics",
        tags=["Metrics"],
    )
    app.include_router(
        kubernetes.router,
        prefix=f"{settings.api_v1_prefix}",
        tags=["Kubernetes"],
    )
    app.include_router(
        websocket.router,
        tags=["WebSocket"],
    )

    return app


app = create_app()
