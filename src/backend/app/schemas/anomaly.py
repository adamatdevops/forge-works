"""Pydantic schemas for Anomaly API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.anomaly import AnomalySeverity, AnomalyType


class AnomalyBase(BaseModel):
    """Base schema for Anomaly."""

    service_id: str = Field(..., description="Related service ID")
    type: AnomalyType = Field(..., description="Type of anomaly")
    severity: AnomalySeverity = Field(..., description="Severity level")
    title: str = Field(..., min_length=1, max_length=200, description="Anomaly title")
    description: str = Field(..., description="Detailed description")
    suggestion: str | None = Field(None, description="Suggested action")
    detected_value: str | None = Field(None, max_length=100, description="Detected value")
    expected_value: str | None = Field(None, max_length=100, description="Expected value")
    detection_rule: str | None = Field(None, max_length=200, description="Rule that triggered")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class AnomalyCreate(AnomalyBase):
    """Schema for creating an anomaly."""

    pass


class AnomalyUpdate(BaseModel):
    """Schema for updating an anomaly (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    suggestion: str | None = None
    severity: AnomalySeverity | None = None
    is_active: bool | None = None
    context: dict[str, Any] | None = None


class AnomalyAcknowledge(BaseModel):
    """Schema for acknowledging an anomaly."""

    acknowledged_by: str = Field(..., max_length=100, description="User who acknowledged")


class AnomalyResolve(BaseModel):
    """Schema for resolving an anomaly."""

    resolution_note: str | None = Field(None, description="Resolution notes")


class ServiceSummary(BaseModel):
    """Minimal service info for anomaly response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    status: str


class AnomalyResponse(BaseModel):
    """Full anomaly response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    service_id: str
    type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    suggestion: str | None
    detected_value: str | None
    expected_value: str | None
    detection_rule: str | None
    context: dict[str, Any]
    is_active: bool
    is_acknowledged: bool
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    is_resolved: bool
    resolved_at: datetime | None
    resolution_note: str | None
    detected_at: datetime
    created_at: datetime
    updated_at: datetime

    # Related entity
    service: ServiceSummary | None = None


class AnomalyListResponse(BaseModel):
    """Paginated list of anomalies."""

    items: list[AnomalyResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AnomalyStatsResponse(BaseModel):
    """Anomaly statistics for dashboard."""

    total: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    active: int
    acknowledged: int
    unresolved: int
