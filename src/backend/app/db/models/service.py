"""Service model - core entity in the service catalog."""

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.anomaly import Anomaly
    from app.db.models.team import Team
    from app.db.models.template import Template


class ServiceStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    PROVISIONING = "provisioning"


class ServiceTier(str, Enum):
    """Service criticality tier."""

    CRITICAL = "critical"  # Tier 1 - business critical
    STANDARD = "standard"  # Tier 2 - important
    INTERNAL = "internal"  # Tier 3 - internal tools
    EXPERIMENTAL = "experimental"  # Tier 4 - experiments


class Service(Base):
    """Service entity - represents a deployed microservice in the catalog."""

    __tablename__ = "services"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Service identity
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Ownership
    team_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("teams.id"),
        nullable=False,
    )

    # Template used
    template_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("templates.id"),
        nullable=True,
    )

    # Status
    status: Mapped[ServiceStatus] = mapped_column(
        ENUM(ServiceStatus, name="service_status", create_type=False),
        default=ServiceStatus.UNKNOWN,
        nullable=False,
    )
    tier: Mapped[ServiceTier] = mapped_column(
        ENUM(ServiceTier, name="service_tier", create_type=False),
        default=ServiceTier.STANDARD,
        nullable=False,
    )

    # Repository info
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repository_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)

    # Deployment info
    namespace: Mapped[str | None] = mapped_column(String(100), nullable=True)
    argocd_app_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Metrics (for demo/anomaly detection)
    deploys_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rollbacks_this_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_deploy_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Tags and metadata
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Links
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dashboard_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    runbook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
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
    team: Mapped["Team"] = relationship("Team", back_populates="services")
    template: Mapped["Template | None"] = relationship("Template", back_populates="services")
    anomalies: Mapped[list["Anomaly"]] = relationship(
        "Anomaly",
        back_populates="service",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name={self.name}, status={self.status})>"
