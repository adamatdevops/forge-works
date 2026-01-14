"""CRUD operations for Anomaly model."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.anomaly import Anomaly, AnomalySeverity, AnomalyType
from app.schemas.anomaly import AnomalyCreate, AnomalyUpdate


class AnomalyCRUD:
    """CRUD operations for Anomaly model."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        anomaly_id: str,
        include_service: bool = True,
    ) -> Anomaly | None:
        """Get an anomaly by ID."""
        query = select(Anomaly).where(Anomaly.id == anomaly_id)

        if include_service:
            query = query.options(selectinload(Anomaly.service))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        service_id: str | None = None,
        severity: AnomalySeverity | None = None,
        anomaly_type: AnomalyType | None = None,
        is_active: bool | None = None,
        is_resolved: bool | None = None,
        include_service: bool = True,
    ) -> Sequence[Anomaly]:
        """Get all anomalies with optional filtering."""
        query = select(Anomaly)

        # Apply filters
        if service_id:
            query = query.where(Anomaly.service_id == service_id)
        if severity:
            query = query.where(Anomaly.severity == severity)
        if anomaly_type:
            query = query.where(Anomaly.type == anomaly_type)
        if is_active is not None:
            query = query.where(Anomaly.is_active == is_active)
        if is_resolved is not None:
            query = query.where(Anomaly.is_resolved == is_resolved)

        if include_service:
            query = query.options(selectinload(Anomaly.service))

        # Order by severity (critical first) then by detected_at (newest first)
        query = query.order_by(
            Anomaly.severity.desc(),
            Anomaly.detected_at.desc(),
        ).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def count(
        db: AsyncSession,
        service_id: str | None = None,
        severity: AnomalySeverity | None = None,
        anomaly_type: AnomalyType | None = None,
        is_active: bool | None = None,
        is_resolved: bool | None = None,
    ) -> int:
        """Count anomalies with optional filtering."""
        query = select(func.count(Anomaly.id))

        if service_id:
            query = query.where(Anomaly.service_id == service_id)
        if severity:
            query = query.where(Anomaly.severity == severity)
        if anomaly_type:
            query = query.where(Anomaly.type == anomaly_type)
        if is_active is not None:
            query = query.where(Anomaly.is_active == is_active)
        if is_resolved is not None:
            query = query.where(Anomaly.is_resolved == is_resolved)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def create(db: AsyncSession, data: AnomalyCreate) -> Anomaly:
        """Create a new anomaly."""
        anomaly = Anomaly(
            service_id=data.service_id,
            type=data.type,
            severity=data.severity,
            title=data.title,
            description=data.description,
            suggestion=data.suggestion,
            detected_value=data.detected_value,
            expected_value=data.expected_value,
            detection_rule=data.detection_rule,
            context=data.context,
        )

        db.add(anomaly)
        await db.commit()
        await db.refresh(anomaly)

        # Reload with relations
        return await AnomalyCRUD.get_by_id(db, anomaly.id)

    @staticmethod
    async def update(
        db: AsyncSession,
        anomaly: Anomaly,
        data: AnomalyUpdate,
    ) -> Anomaly:
        """Update an existing anomaly."""
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(anomaly, field, value)

        await db.commit()
        await db.refresh(anomaly)

        # Reload with relations
        return await AnomalyCRUD.get_by_id(db, anomaly.id)

    @staticmethod
    async def acknowledge(
        db: AsyncSession,
        anomaly: Anomaly,
        acknowledged_by: str,
    ) -> Anomaly:
        """Mark an anomaly as acknowledged."""
        anomaly.is_acknowledged = True
        anomaly.acknowledged_by = acknowledged_by
        anomaly.acknowledged_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(anomaly)

        return await AnomalyCRUD.get_by_id(db, anomaly.id)

    @staticmethod
    async def resolve(
        db: AsyncSession,
        anomaly: Anomaly,
        resolution_note: str | None = None,
    ) -> Anomaly:
        """Mark an anomaly as resolved."""
        anomaly.is_resolved = True
        anomaly.is_active = False
        anomaly.resolved_at = datetime.now(UTC)
        if resolution_note:
            anomaly.resolution_note = resolution_note

        await db.commit()
        await db.refresh(anomaly)

        return await AnomalyCRUD.get_by_id(db, anomaly.id)

    @staticmethod
    async def delete(db: AsyncSession, anomaly: Anomaly) -> None:
        """Delete an anomaly."""
        await db.delete(anomaly)
        await db.commit()

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """Get anomaly statistics for dashboard."""
        # Total count
        total_result = await db.execute(select(func.count(Anomaly.id)))
        total = total_result.scalar_one()

        # Count by severity
        severity_result = await db.execute(
            select(Anomaly.severity, func.count(Anomaly.id)).group_by(Anomaly.severity)
        )
        by_severity = {str(row[0].value): row[1] for row in severity_result.all()}

        # Count by type
        type_result = await db.execute(
            select(Anomaly.type, func.count(Anomaly.id)).group_by(Anomaly.type)
        )
        by_type = {str(row[0].value): row[1] for row in type_result.all()}

        # Active count
        active_result = await db.execute(
            select(func.count(Anomaly.id)).where(Anomaly.is_active.is_(True))
        )
        active = active_result.scalar_one()

        # Acknowledged count
        acknowledged_result = await db.execute(
            select(func.count(Anomaly.id)).where(Anomaly.is_acknowledged.is_(True))
        )
        acknowledged = acknowledged_result.scalar_one()

        # Unresolved count
        unresolved_result = await db.execute(
            select(func.count(Anomaly.id)).where(Anomaly.is_resolved.is_(False))
        )
        unresolved = unresolved_result.scalar_one()

        return {
            "total": total,
            "by_severity": by_severity,
            "by_type": by_type,
            "active": active,
            "acknowledged": acknowledged,
            "unresolved": unresolved,
        }
