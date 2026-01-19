"""ForgeWorks FastAPI Application - Platform Orchestrator."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    anomalies,
    auth,
    demo,
    forges,
    health,
    kubernetes,
    metrics,
    ml,
    services,
    templates,
    websocket,
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize Forges - the bidirectional bridges
    from app.forges.github_forge import get_github_forge
    from app.forges.github_k8s_bridge import get_github_kubernetes_bridge
    from app.forges.webhook_router import register_forge

    github_forge = get_github_forge()
    bridge = get_github_kubernetes_bridge()

    # Register forges to receive webhooks
    register_forge("github", github_forge)
    register_forge("github", bridge)  # Bridge also listens to GitHub
    register_forge("kubernetes", bridge)  # Bridge listens to K8s

    print(f"  → Forges initialized: {github_forge.forge_name}, {bridge.forge_name}")

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
        description="Internal Developer Platform - Platform Orchestrator",
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
        auth.router,
        prefix=f"{settings.api_v1_prefix}/auth",
        tags=["Authentication"],
    )
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
    app.include_router(
        ml.router,
        prefix=f"{settings.api_v1_prefix}/ml",
        tags=["ML Recommendations"],
    )
    app.include_router(
        demo.router,
        prefix=f"{settings.api_v1_prefix}/demo",
        tags=["Demo"],
    )
    app.include_router(
        forges.router,
        prefix=f"{settings.api_v1_prefix}/forges",
        tags=["Forges"],
    )

    return app


app = create_app()
