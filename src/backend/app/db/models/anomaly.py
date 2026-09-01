"""Anomaly model - for anomaly detection and surfacing panel."""

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.service import Service


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""

    CRITICAL = "critical"  # 🔴 Immediate attention required
    WARNING = "warning"  # 🟡 Should investigate soon
    INFO = "info"  # 🔵 Informational, for awareness


class AnomalyType(str, Enum):
    """Types of anomalies detected."""

    HIGH_DEPLOY_FREQUENCY = "high_deploy_frequency"  # Too many deploys in short time
    CONSECUTIVE_ROLLBACKS = "consecutive_rollbacks"  # Multiple rollbacks
    PIPELINE_FAILING = "pipeline_failing"  # CI/CD pipeline stuck failing
    HEALTH_DEGRADED = "health_degraded"  # Service health declining
    UNUSUAL_ERROR_RATE = "unusual_error_rate"  # Error spike detected
    RESOURCE_SPIKE = "resource_spike"  # CPU/Memory spike
    DRIFT_DETECTED = "drift_detected"  # Configuration drift from template


class Anomaly(Base):
    """Anomaly entity - unusual activity detected in services."""

    __tablename__ = "anomalies"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Related service
    service_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("services.id"),
        nullable=False,
    )

    # Anomaly classification
    type: Mapped[AnomalyType] = mapped_column(
        ENUM(
            AnomalyType,
            name="anomaly_type",
            create_type=False,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    severity: Mapped[AnomalySeverity] = mapped_column(
        ENUM(
            AnomalySeverity,
            name="anomaly_severity",
            create_type=False,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # Description
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Detection details
    detected_value: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "12 deploys"
    expected_value: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "2 deploys"
    detection_rule: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # Rule that triggered

    # Context
    context: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )  # Additional context data

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Resolution
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service"] = relationship("Service", back_populates="anomalies")

    def __repr__(self) -> str:
        return f"<Anomaly(id={self.id}, type={self.type}, severity={self.severity})>"
