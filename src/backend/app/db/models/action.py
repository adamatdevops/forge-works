"""Action model - audit log for all platform actions."""

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActionType(str, Enum):
    """Types of actions that can be performed."""

    # Service actions
    SERVICE_CREATED = "service_created"
    SERVICE_UPDATED = "service_updated"
    SERVICE_DELETED = "service_deleted"
    SERVICE_DEPLOYED = "service_deployed"
    SERVICE_ROLLED_BACK = "service_rolled_back"

    # Template actions
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DEPRECATED = "template_deprecated"

    # Recommendation actions
    RECOMMENDATION_REQUESTED = "recommendation_requested"
    RECOMMENDATION_ACCEPTED = "recommendation_accepted"
    RECOMMENDATION_OVERRIDDEN = "recommendation_overridden"

    # Anomaly actions
    ANOMALY_DETECTED = "anomaly_detected"
    ANOMALY_ACKNOWLEDGED = "anomaly_acknowledged"
    ANOMALY_RESOLVED = "anomaly_resolved"

    # Team actions
    TEAM_CREATED = "team_created"
    TEAM_UPDATED = "team_updated"


class ActionStatus(str, Enum):
    """Status of an action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Action(Base):
    """Action audit log - tracks all platform activities."""

    __tablename__ = "actions"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Action type and status
    type: Mapped[ActionType] = mapped_column(
        ENUM(ActionType, name="action_type", create_type=False),
        nullable=False,
    )
    status: Mapped[ActionStatus] = mapped_column(
        ENUM(ActionStatus, name="action_status", create_type=False),
        default=ActionStatus.COMPLETED,
        nullable=False,
    )

    # Description
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Actor
    actor: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # User or system identifier
    actor_type: Mapped[str] = mapped_column(
        String(50), default="user", nullable=False
    )  # user, system, automation

    # Target entity
    target_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # service, template, team, etc.
    target_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    target_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Related entities
    team_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("teams.id"),
        nullable=True,
    )
    service_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("services.id"),
        nullable=True,
    )

    # Change details
    before_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Error info (if failed)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Action(id={self.id}, type={self.type}, status={self.status})>"
