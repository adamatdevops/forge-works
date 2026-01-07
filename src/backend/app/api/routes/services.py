"""Service catalog API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.service import ServiceCRUD
from app.crud.team import TeamCRUD
from app.crud.template import TemplateCRUD
from app.db.base import get_db
from app.db.models.service import ServiceStatus, ServiceTier
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
    ServiceStatsResponse,
)

router = APIRouter()

# Type alias for database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=ServiceListResponse)
async def list_services(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: ServiceStatus | None = Query(None, description="Filter by status"),
    tier: ServiceTier | None = Query(None, description="Filter by tier"),
    team_id: str | None = Query(None, description="Filter by team ID"),
    search: str | None = Query(None, description="Search by name or description"),
) -> ServiceListResponse:
    """
    List all services in the catalog.

    Supports pagination, filtering by status/tier/team, and search.
    """
    skip = (page - 1) * page_size

    services = await ServiceCRUD.get_all(
        db,
        skip=skip,
        limit=page_size,
        status=status,
        tier=tier,
        team_id=team_id,
        search=search,
    )

    total = await ServiceCRUD.count(
        db,
        status=status,
        tier=tier,
        team_id=team_id,
        search=search,
    )

    pages = (total + page_size - 1) // page_size

    return ServiceListResponse(
        services=[ServiceResponse.model_validate(s) for s in services],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/stats", response_model=ServiceStatsResponse)
async def get_service_stats(db: DbSession) -> ServiceStatsResponse:
    """
    Get service catalog statistics for dashboard.

    Returns counts by status, tier, and activity metrics.
    """
    stats = await ServiceCRUD.get_stats(db)
    return ServiceStatsResponse(**stats)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(db: DbSession, service_id: str) -> ServiceResponse:
    """
    Get a service by ID.

    Returns full service details including team, template, and anomalies.
    """
    service = await ServiceCRUD.get_by_id(db, service_id)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID '{service_id}' not found",
        )

    return ServiceResponse.model_validate(service)


@router.get("/slug/{slug}", response_model=ServiceResponse)
async def get_service_by_slug(db: DbSession, slug: str) -> ServiceResponse:
    """
    Get a service by slug.

    Returns full service details including team, template, and anomalies.
    """
    service = await ServiceCRUD.get_by_slug(db, slug)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with slug '{slug}' not found",
        )

    return ServiceResponse.model_validate(service)


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(db: DbSession, data: ServiceCreate) -> ServiceResponse:
    """
    Create a new service in the catalog.

    Requires a valid team_id. Template_id is optional but recommended.
    """
    # Validate team exists
    team_exists = await TeamCRUD.exists(db, data.team_id)
    if not team_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team with ID '{data.team_id}' not found",
        )

    # Validate template exists if provided
    if data.template_id:
        template_exists = await TemplateCRUD.exists(db, data.template_id)
        if not template_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template with ID '{data.template_id}' not found",
            )

        # Increment template usage
        template = await TemplateCRUD.get_by_id(db, data.template_id)
        if template:
            await TemplateCRUD.increment_usage(db, template)

    # Check for duplicate name
    existing = await ServiceCRUD.get_by_slug(
        db, data.name.lower().replace(" ", "-"), include_relations=False
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service with name '{data.name}' already exists",
        )

    service = await ServiceCRUD.create(db, data)
    return ServiceResponse.model_validate(service)


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    db: DbSession,
    service_id: str,
    data: ServiceUpdate,
) -> ServiceResponse:
    """
    Update an existing service.

    Only provided fields will be updated.
    """
    service = await ServiceCRUD.get_by_id(db, service_id, include_relations=False)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID '{service_id}' not found",
        )

    # Validate team if changing
    if data.team_id and data.team_id != service.team_id:
        team_exists = await TeamCRUD.exists(db, data.team_id)
        if not team_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Team with ID '{data.team_id}' not found",
            )

    # Validate template if changing
    if data.template_id and data.template_id != service.template_id:
        template_exists = await TemplateCRUD.exists(db, data.template_id)
        if not template_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template with ID '{data.template_id}' not found",
            )

    updated_service = await ServiceCRUD.update(db, service, data)
    return ServiceResponse.model_validate(updated_service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(db: DbSession, service_id: str) -> None:
    """
    Delete a service from the catalog.

    This is a soft delete in production (would mark as deleted).
    For demo purposes, this performs a hard delete.
    """
    service = await ServiceCRUD.get_by_id(db, service_id, include_relations=False)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID '{service_id}' not found",
        )

    await ServiceCRUD.delete(db, service)
