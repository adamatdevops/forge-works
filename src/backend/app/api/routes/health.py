"""Health check endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime


class DetailedHealthResponse(HealthResponse):
    """Detailed health check with component status."""

    components: dict[str, str]


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
    # TODO: Implement actual component checks
    components = {
        "database": "healthy",  # TODO: Check PostgreSQL connection
        "cache": "healthy",  # TODO: Check Redis connection
        "ml_model": "healthy",  # TODO: Check model loaded
    }

    return DetailedHealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        components=components,
    )
