"""Anomaly detection API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.anomaly import AnomalyCRUD
from app.crud.service import ServiceCRUD
from app.db.base import get_db
from app.db.models.anomaly import AnomalySeverity, AnomalyType
from app.schemas.anomaly import (
    AnomalyAcknowledge,
    AnomalyCreate,
    AnomalyListResponse,
    AnomalyResolve,
    AnomalyResponse,
    AnomalyStatsResponse,
    AnomalyUpdate,
)

router = APIRouter()

# Type alias for database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=AnomalyListResponse)
async def list_anomalies(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service_id: str | None = Query(None, description="Filter by service ID"),
    severity: AnomalySeverity | None = Query(None, description="Filter by severity"),
    type: AnomalyType | None = Query(None, alias="type", description="Filter by anomaly type"),
    active: bool | None = Query(None, description="Filter by active status"),
    resolved: bool | None = Query(None, description="Filter by resolved status"),
) -> AnomalyListResponse:
    """
    List all anomalies with filtering and pagination.

    Returns anomalies sorted by severity (critical first) then by detection time.
    """
    skip = (page - 1) * page_size

    anomalies = await AnomalyCRUD.get_all(
        db,
        skip=skip,
        limit=page_size,
        service_id=service_id,
        severity=severity,
        anomaly_type=type,
        is_active=active,
        is_resolved=resolved,
    )

    total = await AnomalyCRUD.count(
        db,
        service_id=service_id,
        severity=severity,
        anomaly_type=type,
        is_active=active,
        is_resolved=resolved,
    )

    pages = (total + page_size - 1) // page_size

    return AnomalyListResponse(
        items=[AnomalyResponse.model_validate(a) for a in anomalies],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/stats", response_model=AnomalyStatsResponse)
async def get_anomaly_stats(db: DbSession) -> AnomalyStatsResponse:
    """
    Get anomaly statistics for the dashboard.

    Returns counts by severity, type, and status.
    """
    stats = await AnomalyCRUD.get_stats(db)
    return AnomalyStatsResponse(**stats)


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(db: DbSession, anomaly_id: str) -> AnomalyResponse:
    """
    Get an anomaly by ID.

    Returns full anomaly details including related service.
    """
    anomaly = await AnomalyCRUD.get_by_id(db, anomaly_id)

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    return AnomalyResponse.model_validate(anomaly)


@router.post("", response_model=AnomalyResponse, status_code=status.HTTP_201_CREATED)
async def create_anomaly(db: DbSession, data: AnomalyCreate) -> AnomalyResponse:
    """
    Create a new anomaly.

    Typically called by detection systems when an anomaly is identified.
    """
    # Validate service exists
    service_exists = await ServiceCRUD.get_by_id(db, data.service_id, include_relations=False)
    if not service_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service with ID '{data.service_id}' not found",
        )

    anomaly = await AnomalyCRUD.create(db, data)
    return AnomalyResponse.model_validate(anomaly)


@router.patch("/{anomaly_id}", response_model=AnomalyResponse)
async def update_anomaly(
    db: DbSession,
    anomaly_id: str,
    data: AnomalyUpdate,
) -> AnomalyResponse:
    """
    Update an existing anomaly.

    Only provided fields will be updated.
    """
    anomaly = await AnomalyCRUD.get_by_id(db, anomaly_id, include_service=False)

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    updated_anomaly = await AnomalyCRUD.update(db, anomaly, data)
    return AnomalyResponse.model_validate(updated_anomaly)


@router.post("/{anomaly_id}/acknowledge", response_model=AnomalyResponse)
async def acknowledge_anomaly(
    db: DbSession,
    anomaly_id: str,
    data: AnomalyAcknowledge,
) -> AnomalyResponse:
    """
    Acknowledge an anomaly.

    Marks the anomaly as seen by a user to prevent duplicate alerts.
    """
    anomaly = await AnomalyCRUD.get_by_id(db, anomaly_id, include_service=False)

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    if anomaly.is_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anomaly is already acknowledged",
        )

    acknowledged_anomaly = await AnomalyCRUD.acknowledge(db, anomaly, data.acknowledged_by)
    return AnomalyResponse.model_validate(acknowledged_anomaly)


@router.post("/{anomaly_id}/resolve", response_model=AnomalyResponse)
async def resolve_anomaly(
    db: DbSession,
    anomaly_id: str,
    data: AnomalyResolve | None = None,
) -> AnomalyResponse:
    """
    Mark an anomaly as resolved.

    Sets is_resolved=True and is_active=False.
    """
    anomaly = await AnomalyCRUD.get_by_id(db, anomaly_id, include_service=False)

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    if anomaly.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anomaly is already resolved",
        )

    resolution_note = data.resolution_note if data else None
    resolved_anomaly = await AnomalyCRUD.resolve(db, anomaly, resolution_note)
    return AnomalyResponse.model_validate(resolved_anomaly)


@router.delete("/{anomaly_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_anomaly(db: DbSession, anomaly_id: str) -> None:
    """
    Delete an anomaly.

    Typically used to clean up false positives or outdated anomalies.
    """
    anomaly = await AnomalyCRUD.get_by_id(db, anomaly_id, include_service=False)

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    await AnomalyCRUD.delete(db, anomaly)
