"""Recommendation model - ML recommendation logging for platform learning."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recommendation(Base):
    """ML Recommendation log - tracks recommendations and outcomes for learning."""

    __tablename__ = "recommendations"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Request context
    session_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # To group related recommendations
    team_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("teams.id"),
        nullable=True,
    )

    # Input features (for ML training)
    workload_type: Mapped[str] = mapped_column(String(50), nullable=False)  # api, batch, stream, ml
    language: Mapped[str] = mapped_column(String(50), nullable=False)  # python, go, typescript
    requirements: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list, nullable=False
    )  # e.g., ["high_throughput", "low_latency"]
    additional_context: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )  # Any extra input features

    # Recommendations provided (ordered by score)
    recommendations: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # [{"template_id": ..., "score": 94, "reason": ...}, ...]

    # Top recommendation
    top_template_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("templates.id"),
        nullable=False,
    )
    top_score: Mapped[float] = mapped_column(Float, nullable=False)

    # User decision
    selected_template_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("templates.id"),
        nullable=True,
    )
    was_override: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # True if user picked different template
    override_reason: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # Why they overrode

    # Warnings issued
    warnings: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    # Model info
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    inference_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Outcome tracking (for feedback loop)
    was_successful: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )  # Did the service work well?
    feedback_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # User satisfaction 1-5
    feedback_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

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

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, workload={self.workload_type}, override={self.was_override})>"
