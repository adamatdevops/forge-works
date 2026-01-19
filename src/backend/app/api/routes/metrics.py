"""Metrics API endpoints - Platform engineering dashboard metrics."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models.anomaly import Anomaly, AnomalySeverity
from app.db.models.service import Service
from app.db.models.team import Team
from app.db.models.template import Template
from app.schemas.metrics import (
    AnomalyMetrics,
    DeploymentMetrics,
    DORAMetrics,
    MetricsDashboard,
    PipelineMetrics,
    ServiceHealthMetrics,
    TeamMetrics,
    TemplateMetrics,
    TimeSeries,
    TimeSeriesPoint,
)

router = APIRouter()

# Type alias for database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_deployment_metrics(
    db: AsyncSession, service_id: str | None = None
) -> DeploymentMetrics:
    """Calculate deployment metrics."""
    query = select(Service)
    if service_id:
        query = query.where(Service.id == service_id)

    result = await db.execute(query)
    services = result.scalars().all()

    if not services:
        return DeploymentMetrics()

    total_deploys = sum(s.deploys_today * 7 for s in services)  # Estimate
    deploys_today = sum(s.deploys_today for s in services)
    rollbacks = sum(s.rollbacks_this_week for s in services)

    # Estimate success rate (assumes rollbacks are failures)
    weekly_deploys = deploys_today * 7
    success_rate = (
        ((weekly_deploys - rollbacks) / weekly_deploys * 100) if weekly_deploys > 0 else 100
    )

    return DeploymentMetrics(
        total_deploys=total_deploys,
        successful_deploys=total_deploys - rollbacks,
        failed_deploys=rollbacks,
        deploy_success_rate=round(success_rate, 1),
        deploys_today=deploys_today,
        deploys_this_week=weekly_deploys,
        avg_deploys_per_day=round(deploys_today / len(services), 1) if services else 0,
        rollbacks_this_week=rollbacks,
    )


async def get_pipeline_metrics(db: AsyncSession) -> PipelineMetrics:
    """Calculate pipeline metrics (mock data for now)."""
    # In real implementation, this would query CI/CD system
    return PipelineMetrics(
        total_runs=156,
        successful_runs=142,
        failed_runs=14,
        pending_runs=3,
        running_now=2,
        success_rate=91.0,
        avg_duration_seconds=340,
        p95_duration_seconds=720,
    )


async def get_service_health_metrics(
    db: AsyncSession, service_id: str | None = None
) -> ServiceHealthMetrics:
    """Calculate service health metrics."""
    query = select(Service.status, func.count(Service.id)).group_by(Service.status)
    if service_id:
        query = query.where(Service.id == service_id)

    result = await db.execute(query)
    status_counts = {str(row[0].value): row[1] for row in result.all()}

    total = sum(status_counts.values())
    healthy = status_counts.get("healthy", 0)
    degraded = status_counts.get("degraded", 0)
    unhealthy = status_counts.get("unhealthy", 0)
    provisioning = status_counts.get("provisioning", 0)

    # Health score: healthy=100%, degraded=50%, unhealthy=0%
    health_score = 0.0
    if total > 0:
        health_score = ((healthy * 100) + (degraded * 50)) / total

    return ServiceHealthMetrics(
        total_services=total,
        healthy_services=healthy,
        degraded_services=degraded,
        unhealthy_services=unhealthy,
        provisioning_services=provisioning,
        health_score=round(health_score, 1),
    )


async def get_dora_metrics(db: AsyncSession) -> DORAMetrics:
    """Calculate DORA metrics."""
    # Get deployment frequency
    deploy_result = await db.execute(select(func.sum(Service.deploys_today)))
    deploys_today = deploy_result.scalar_one() or 0

    # Categorize deployment frequency
    if deploys_today > 10:
        freq = "Multiple per day"
        freq_score = 100.0
    elif deploys_today > 0:
        freq = "Daily"
        freq_score = 75.0
    else:
        freq = "Weekly"
        freq_score = 50.0

    # Get change failure rate from rollbacks
    rollback_result = await db.execute(select(func.sum(Service.rollbacks_this_week)))
    rollbacks = rollback_result.scalar_one() or 0
    weekly_deploys = deploys_today * 7
    cfr = (rollbacks / weekly_deploys * 100) if weekly_deploys > 0 else 0

    # Mock lead time and MTTR (would come from actual CI/CD data)
    lead_time_minutes = 45  # 45 minutes from commit to production
    mttr_minutes = 30  # 30 minutes to recover

    # Determine overall DORA score
    if freq_score >= 75 and cfr < 15 and lead_time_minutes < 60 and mttr_minutes < 60:
        overall = "Elite"
    elif freq_score >= 50 and cfr < 30 and lead_time_minutes < 120:
        overall = "High"
    elif cfr < 45:
        overall = "Medium"
    else:
        overall = "Low"

    return DORAMetrics(
        deployment_frequency=freq,
        deployment_frequency_score=freq_score,
        lead_time_for_changes="< 1 hour",
        lead_time_minutes=lead_time_minutes,
        change_failure_rate=round(cfr, 1),
        mean_time_to_recovery="< 1 hour",
        mttr_minutes=mttr_minutes,
        overall_score=overall,
    )


async def get_template_metrics(db: AsyncSession) -> TemplateMetrics:
    """Calculate template adoption metrics."""
    # Total templates
    total_result = await db.execute(select(func.count(Template.id)))
    total = total_result.scalar_one()

    # Active templates (usage_count > 0)
    active_result = await db.execute(
        select(func.count(Template.id)).where(Template.usage_count > 0)
    )
    active = active_result.scalar_one()

    # Most popular template
    popular_result = await db.execute(
        select(Template.name).order_by(Template.usage_count.desc()).limit(1)
    )
    most_popular = popular_result.scalar_one_or_none()

    # Services without templates
    no_template_result = await db.execute(
        select(func.count(Service.id)).where(Service.template_id.is_(None))
    )
    without_template = no_template_result.scalar_one()

    # Total services
    total_services_result = await db.execute(select(func.count(Service.id)))
    total_services = total_services_result.scalar_one()

    adoption_rate = (
        ((total_services - without_template) / total_services * 100) if total_services > 0 else 0
    )

    return TemplateMetrics(
        total_templates=total,
        active_templates=active,
        most_popular=most_popular,
        adoption_rate=round(adoption_rate, 1),
        services_without_template=without_template,
    )


async def get_anomaly_metrics(db: AsyncSession, service_id: str | None = None) -> AnomalyMetrics:
    """Calculate anomaly metrics."""
    # Base filter for service_id
    service_filter = Anomaly.service_id == service_id if service_id else True

    # Total anomalies
    total_result = await db.execute(select(func.count(Anomaly.id)).where(service_filter))
    total = total_result.scalar_one()

    # Active anomalies
    active_result = await db.execute(
        select(func.count(Anomaly.id)).where(service_filter, Anomaly.is_active.is_(True))
    )
    active = active_result.scalar_one()

    # By severity
    critical_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            service_filter,
            Anomaly.is_active.is_(True),
            Anomaly.severity == AnomalySeverity.CRITICAL,
        )
    )
    critical = critical_result.scalar_one()

    warning_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            service_filter, Anomaly.is_active.is_(True), Anomaly.severity == AnomalySeverity.WARNING
        )
    )
    warning = warning_result.scalar_one()

    # Resolved today (would need resolved_at date comparison)
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    resolved_today_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            service_filter, Anomaly.is_resolved.is_(True), Anomaly.resolved_at >= today
        )
    )
    resolved_today = resolved_today_result.scalar_one()

    return AnomalyMetrics(
        total_anomalies=total,
        active_anomalies=active,
        critical_anomalies=critical,
        warning_anomalies=warning,
        resolved_today=resolved_today,
        avg_resolution_time_hours=2.5,  # Mock for now
    )


async def get_team_metrics(db: AsyncSession) -> TeamMetrics:
    """Calculate team metrics."""
    # Total teams
    total_result = await db.execute(select(func.count(Team.id)))
    total = total_result.scalar_one()

    # Active teams (those with services)
    active_result = await db.execute(select(func.count(func.distinct(Service.team_id))))
    active = active_result.scalar_one()

    # Services per team
    total_services_result = await db.execute(select(func.count(Service.id)))
    total_services = total_services_result.scalar_one()
    services_per_team = total_services / total if total > 0 else 0

    # Most active team (by service count)
    most_active_result = await db.execute(
        select(Team.name)
        .join(Service, Service.team_id == Team.id)
        .group_by(Team.id, Team.name)
        .order_by(func.count(Service.id).desc())
        .limit(1)
    )
    most_active = most_active_result.scalar_one_or_none()

    return TeamMetrics(
        total_teams=total,
        active_teams=active,
        services_per_team_avg=round(services_per_team, 1),
        most_active_team=most_active,
    )


def generate_deploy_trend() -> TimeSeries:
    """Generate sample deploy trend data."""
    now = datetime.now(UTC)
    data = []
    for i in range(7, 0, -1):
        day = now - timedelta(days=i)
        # Sample values with some variation
        value = 5 + (i % 3) * 2
        data.append(
            TimeSeriesPoint(
                timestamp=day,
                value=value,
                label=day.strftime("%a"),
            )
        )
    return TimeSeries(name="Deployments", data=data, unit="deploys")


@router.get("", response_model=MetricsDashboard)
async def get_metrics(
    db: DbSession,
    service_id: str | None = Query(None, description="Filter by service ID"),
    team_id: str | None = Query(None, description="Filter by team ID"),
    time_range: str = Query("7d", description="Time range"),
    include_trends: bool = Query(False, description="Include time series"),
) -> MetricsDashboard:
    """
    Get comprehensive metrics dashboard data.

    Returns deployment, pipeline, service health, DORA, and team metrics.
    """
    deployment = await get_deployment_metrics(db, service_id)
    pipeline = await get_pipeline_metrics(db)
    service_health = await get_service_health_metrics(db, service_id)
    dora = await get_dora_metrics(db)
    template = await get_template_metrics(db)
    anomaly = await get_anomaly_metrics(db, service_id)
    team = await get_team_metrics(db)

    return MetricsDashboard(
        deployment=deployment,
        pipeline=pipeline,
        service_health=service_health,
        dora=dora,
        template=template,
        anomaly=anomaly,
        team=team,
        deploy_trend=generate_deploy_trend() if include_trends else None,
        generated_at=datetime.now(UTC),
    )


@router.get("/dora", response_model=DORAMetrics)
async def get_dora(db: DbSession) -> DORAMetrics:
    """
    Get DORA metrics only.

    Returns deployment frequency, lead time, change failure rate, and MTTR.
    """
    return await get_dora_metrics(db)


@router.get("/health", response_model=ServiceHealthMetrics)
async def get_health(
    db: DbSession,
    service_id: str | None = Query(None, description="Filter by service ID"),
) -> ServiceHealthMetrics:
    """
    Get service health metrics.

    Returns counts of healthy, degraded, and unhealthy services.
    """
    return await get_service_health_metrics(db, service_id)


@router.get("/deployment", response_model=DeploymentMetrics)
async def get_deployment(
    db: DbSession,
    service_id: str | None = Query(None, description="Filter by service ID"),
) -> DeploymentMetrics:
    """
    Get deployment metrics.

    Returns deployment counts, success rates, and rollback statistics.
    """
    return await get_deployment_metrics(db, service_id)
