"""CRUD operations for Service model."""

import re
from typing import Sequence

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.service import Service, ServiceStatus, ServiceTier
from app.db.models.anomaly import Anomaly
from app.schemas.service import ServiceCreate, ServiceUpdate


def slugify(name: str) -> str:
    """Convert a name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


class ServiceCRUD:
    """CRUD operations for Service model."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        service_id: str,
        include_relations: bool = True,
    ) -> Service | None:
        """Get a service by ID."""
        query = select(Service).where(Service.id == service_id)

        if include_relations:
            query = query.options(
                selectinload(Service.team),
                selectinload(Service.template),
                selectinload(Service.anomalies),
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(
        db: AsyncSession,
        slug: str,
        include_relations: bool = True,
    ) -> Service | None:
        """Get a service by slug."""
        query = select(Service).where(Service.slug == slug)

        if include_relations:
            query = query.options(
                selectinload(Service.team),
                selectinload(Service.template),
                selectinload(Service.anomalies),
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: ServiceStatus | None = None,
        tier: ServiceTier | None = None,
        team_id: str | None = None,
        search: str | None = None,
        include_relations: bool = True,
    ) -> Sequence[Service]:
        """Get all services with optional filtering."""
        query = select(Service)

        # Apply filters
        if status:
            query = query.where(Service.status == status)
        if tier:
            query = query.where(Service.tier == tier)
        if team_id:
            query = query.where(Service.team_id == team_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Service.name.ilike(search_pattern))
                | (Service.description.ilike(search_pattern))
            )

        if include_relations:
            query = query.options(
                selectinload(Service.team),
                selectinload(Service.template),
                selectinload(Service.anomalies),
            )

        query = query.offset(skip).limit(limit).order_by(Service.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def count(
        db: AsyncSession,
        status: ServiceStatus | None = None,
        tier: ServiceTier | None = None,
        team_id: str | None = None,
        search: str | None = None,
    ) -> int:
        """Count services with optional filtering."""
        query = select(func.count(Service.id))

        if status:
            query = query.where(Service.status == status)
        if tier:
            query = query.where(Service.tier == tier)
        if team_id:
            query = query.where(Service.team_id == team_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Service.name.ilike(search_pattern))
                | (Service.description.ilike(search_pattern))
            )

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def create(db: AsyncSession, data: ServiceCreate) -> Service:
        """Create a new service."""
        service = Service(
            name=data.name,
            slug=slugify(data.name),
            description=data.description,
            team_id=data.team_id,
            template_id=data.template_id,
            tier=data.tier,
            status=ServiceStatus.PROVISIONING,
            repository_url=data.repository_url,
            repository_branch=data.repository_branch,
            namespace=data.namespace,
            tags=data.tags,
            metadata=data.metadata,
            documentation_url=data.documentation_url,
            dashboard_url=data.dashboard_url,
            runbook_url=data.runbook_url,
        )

        db.add(service)
        await db.commit()
        await db.refresh(service)

        # Reload with relations
        return await ServiceCRUD.get_by_id(db, service.id)

    @staticmethod
    async def update(
        db: AsyncSession,
        service: Service,
        data: ServiceUpdate,
    ) -> Service:
        """Update an existing service."""
        update_data = data.model_dump(exclude_unset=True)

        # Update slug if name changes
        if "name" in update_data:
            update_data["slug"] = slugify(update_data["name"])

        for field, value in update_data.items():
            setattr(service, field, value)

        await db.commit()
        await db.refresh(service)

        # Reload with relations
        return await ServiceCRUD.get_by_id(db, service.id)

    @staticmethod
    async def delete(db: AsyncSession, service: Service) -> None:
        """Delete a service."""
        await db.delete(service)
        await db.commit()

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """Get service statistics for dashboard."""
        # Total count
        total_result = await db.execute(select(func.count(Service.id)))
        total = total_result.scalar_one()

        # Count by status
        status_result = await db.execute(
            select(Service.status, func.count(Service.id)).group_by(Service.status)
        )
        by_status = {str(row[0].value): row[1] for row in status_result.all()}

        # Count by tier
        tier_result = await db.execute(
            select(Service.tier, func.count(Service.id)).group_by(Service.tier)
        )
        by_tier = {str(row[0].value): row[1] for row in tier_result.all()}

        # Active anomalies
        anomaly_result = await db.execute(
            select(func.count(Anomaly.id)).where(Anomaly.is_active == True)
        )
        active_anomalies = anomaly_result.scalar_one()

        # Total deploys today
        deploys_result = await db.execute(select(func.sum(Service.deploys_today)))
        deploys_today = deploys_result.scalar_one() or 0

        # Total rollbacks this week
        rollbacks_result = await db.execute(
            select(func.sum(Service.rollbacks_this_week))
        )
        rollbacks_this_week = rollbacks_result.scalar_one() or 0

        return {
            "total_services": total,
            "by_status": by_status,
            "by_tier": by_tier,
            "active_anomalies": active_anomalies,
            "deploys_today": deploys_today,
            "rollbacks_this_week": rollbacks_this_week,
        }
