"""Pydantic schemas for Service API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.service import ServiceStatus, ServiceTier


class ServiceBase(BaseModel):
    """Base schema for Service."""

    name: str = Field(..., min_length=1, max_length=100, description="Service name")
    description: str | None = Field(None, description="Service description")
    team_id: str = Field(..., description="Owning team ID")
    template_id: str | None = Field(None, description="Golden Path template used")
    tier: ServiceTier = Field(default=ServiceTier.STANDARD, description="Service criticality tier")
    repository_url: str | None = Field(None, max_length=500, description="Git repository URL")
    repository_branch: str = Field(default="main", max_length=100, description="Default branch")
    namespace: str | None = Field(None, max_length=100, description="Kubernetes namespace")
    tags: list[str] = Field(default_factory=list, description="Service tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    documentation_url: str | None = Field(None, max_length=500, description="Documentation URL")
    dashboard_url: str | None = Field(None, max_length=500, description="Monitoring dashboard URL")
    runbook_url: str | None = Field(None, max_length=500, description="Runbook URL")


class ServiceCreate(ServiceBase):
    """Schema for creating a service."""

    pass


class ServiceUpdate(BaseModel):
    """Schema for updating a service (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    team_id: str | None = None
    template_id: str | None = None
    tier: ServiceTier | None = None
    status: ServiceStatus | None = None
    repository_url: str | None = None
    repository_branch: str | None = None
    namespace: str | None = None
    argocd_app_name: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    documentation_url: str | None = None
    dashboard_url: str | None = None
    runbook_url: str | None = None


class TeamSummary(BaseModel):
    """Minimal team info for service response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str


class TemplateSummary(BaseModel):
    """Minimal template info for service response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    workload_type: str
    language: str


class AnomalySummary(BaseModel):
    """Minimal anomaly info for service response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    severity: str
    title: str
    is_active: bool


class ServiceResponse(BaseModel):
    """Full service response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str | None
    team_id: str
    template_id: str | None
    status: ServiceStatus
    tier: ServiceTier
    repository_url: str | None
    repository_branch: str
    namespace: str | None
    argocd_app_name: str | None
    deploys_today: int
    rollbacks_this_week: int
    last_deploy_at: datetime | None
    tags: list[str]
    metadata: dict[str, Any]
    documentation_url: str | None
    dashboard_url: str | None
    runbook_url: str | None
    created_at: datetime
    updated_at: datetime

    # Related entities
    team: TeamSummary | None = None
    template: TemplateSummary | None = None
    anomalies: list[AnomalySummary] = Field(default_factory=list)


class ServiceListResponse(BaseModel):
    """Paginated list of services."""

    services: list[ServiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ServiceStatsResponse(BaseModel):
    """Service statistics for dashboard."""

    total_services: int
    by_status: dict[str, int]
    by_tier: dict[str, int]
    active_anomalies: int
    deploys_today: int
    rollbacks_this_week: int
