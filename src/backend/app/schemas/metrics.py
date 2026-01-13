"""Pydantic schemas for Metrics API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DeploymentMetrics(BaseModel):
    """Deployment-related metrics."""

    total_deploys: int = Field(0, description="Total deployments")
    successful_deploys: int = Field(0, description="Successful deployments")
    failed_deploys: int = Field(0, description="Failed deployments")
    deploy_success_rate: float = Field(0.0, description="Deployment success rate (0-100)")
    deploys_today: int = Field(0, description="Deployments today")
    deploys_this_week: int = Field(0, description="Deployments this week")
    avg_deploys_per_day: float = Field(0.0, description="Average deploys per day")
    rollbacks_this_week: int = Field(0, description="Rollbacks this week")


class PipelineMetrics(BaseModel):
    """CI/CD Pipeline metrics."""

    total_runs: int = Field(0, description="Total pipeline runs")
    successful_runs: int = Field(0, description="Successful runs")
    failed_runs: int = Field(0, description="Failed runs")
    pending_runs: int = Field(0, description="Pending runs")
    running_now: int = Field(0, description="Currently running")
    success_rate: float = Field(0.0, description="Pipeline success rate (0-100)")
    avg_duration_seconds: int = Field(0, description="Average pipeline duration")
    p95_duration_seconds: int = Field(0, description="95th percentile duration")


class ServiceHealthMetrics(BaseModel):
    """Service health overview metrics."""

    total_services: int = Field(0, description="Total services")
    healthy_services: int = Field(0, description="Healthy services")
    degraded_services: int = Field(0, description="Degraded services")
    unhealthy_services: int = Field(0, description="Unhealthy services")
    provisioning_services: int = Field(0, description="Services being provisioned")
    health_score: float = Field(0.0, description="Overall health score (0-100)")


class DORAMetrics(BaseModel):
    """DORA (DevOps Research and Assessment) metrics."""

    deployment_frequency: str = Field("Unknown", description="How often deploys occur")
    deployment_frequency_score: float = Field(0.0, description="Score 0-100")
    lead_time_for_changes: str = Field("Unknown", description="Time from commit to deploy")
    lead_time_minutes: int = Field(0, description="Lead time in minutes")
    change_failure_rate: float = Field(0.0, description="Percentage of failed changes")
    mean_time_to_recovery: str = Field("Unknown", description="MTTR description")
    mttr_minutes: int = Field(0, description="MTTR in minutes")
    overall_score: str = Field("Unknown", description="Elite/High/Medium/Low")


class TemplateMetrics(BaseModel):
    """Template adoption metrics."""

    total_templates: int = Field(0, description="Total templates available")
    active_templates: int = Field(0, description="Templates in use")
    most_popular: str | None = Field(None, description="Most used template")
    adoption_rate: float = Field(0.0, description="Template adoption rate (0-100)")
    services_without_template: int = Field(0, description="Services not using templates")


class AnomalyMetrics(BaseModel):
    """Anomaly detection metrics."""

    total_anomalies: int = Field(0, description="Total anomalies")
    active_anomalies: int = Field(0, description="Active anomalies")
    critical_anomalies: int = Field(0, description="Critical severity")
    warning_anomalies: int = Field(0, description="Warning severity")
    resolved_today: int = Field(0, description="Resolved today")
    avg_resolution_time_hours: float = Field(0.0, description="Average resolution time")


class TeamMetrics(BaseModel):
    """Team activity metrics."""

    total_teams: int = Field(0, description="Total teams")
    active_teams: int = Field(0, description="Teams with activity this week")
    services_per_team_avg: float = Field(0.0, description="Average services per team")
    most_active_team: str | None = Field(None, description="Most active team")


class TimeSeriesPoint(BaseModel):
    """Single point in time series data."""

    timestamp: datetime
    value: float
    label: str | None = None


class TimeSeries(BaseModel):
    """Time series data for charts."""

    name: str
    data: list[TimeSeriesPoint]
    unit: str = ""


class MetricsDashboard(BaseModel):
    """Complete metrics dashboard response."""

    # Core metrics
    deployment: DeploymentMetrics
    pipeline: PipelineMetrics
    service_health: ServiceHealthMetrics
    dora: DORAMetrics
    template: TemplateMetrics
    anomaly: AnomalyMetrics
    team: TeamMetrics

    # Time series for charts
    deploy_trend: TimeSeries | None = None
    error_trend: TimeSeries | None = None

    # Metadata
    generated_at: datetime
    data_freshness: str = "real-time"


class MetricsQuery(BaseModel):
    """Query parameters for metrics."""

    service_id: str | None = Field(None, description="Filter by service")
    team_id: str | None = Field(None, description="Filter by team")
    time_range: str = Field("7d", description="Time range: 24h, 7d, 30d, 90d")
    include_trends: bool = Field(False, description="Include time series data")
