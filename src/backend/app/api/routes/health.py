"""Health check endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.adapters import get_argocd_adapter, get_github_adapter
from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime


class AdapterHealthResponse(BaseModel):
    """Individual adapter health status."""

    name: str
    healthy: bool
    mode: str
    latency_ms: float | None = None
    error: str | None = None


class DetailedHealthResponse(HealthResponse):
    """Detailed health check with component status."""

    components: dict[str, str]
    adapters: list[AdapterHealthResponse] | None = None


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns basic application health status.",
)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="Returns detailed health status including component checks.",
)
async def detailed_health_check() -> DetailedHealthResponse:
    """Detailed health check with component status."""
    # Core component checks
    components = {
        "database": "healthy",  # TODO: Check PostgreSQL connection
        "cache": "healthy",  # TODO: Check Redis connection
        "ml_model": "healthy",  # TODO: Check model loaded
    }

    # Adapter health checks
    github = get_github_adapter()
    argocd = get_argocd_adapter()

    github_health = await github.health_check()
    argocd_health = await argocd.health_check()

    adapters = [
        AdapterHealthResponse(
            name=github_health.name,
            healthy=github_health.healthy,
            mode=github_health.mode.value,
            latency_ms=github_health.latency_ms,
            error=github_health.error,
        ),
        AdapterHealthResponse(
            name=argocd_health.name,
            healthy=argocd_health.healthy,
            mode=argocd_health.mode.value,
            latency_ms=argocd_health.latency_ms,
            error=argocd_health.error,
        ),
    ]

    # Update components with adapter status
    components["github_adapter"] = "healthy" if github_health.healthy else "unhealthy"
    components["argocd_adapter"] = "healthy" if argocd_health.healthy else "unhealthy"

    # Determine overall status
    all_healthy = all(a.healthy for a in adapters) and all(
        v == "healthy" for v in components.values()
    )

    return DetailedHealthResponse(
        status="healthy" if all_healthy else "degraded",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        components=components,
        adapters=adapters,
    )
