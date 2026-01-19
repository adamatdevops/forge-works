"""Golden Path Template model."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.service import Service


class Template(Base):
    """Golden Path Template - production-ready service blueprints."""

    __tablename__ = "templates"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Template identity
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    # Classification (for ML recommendation)
    workload_type: Mapped[str] = mapped_column(String(50), nullable=False)  # api, batch, stream, ml
    language: Mapped[str] = mapped_column(String(50), nullable=False)  # python, go, typescript
    capabilities: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list, nullable=False
    )  # e.g., ["api", "crud", "async"]
    ideal_for: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list, nullable=False
    )  # e.g., ["low_latency", "rest_api"]

    # Tech stack details
    stack: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )  # {"framework": "fastapi", "db": "postgresql", ...}

    # Template content
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Included components
    includes_ci: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    includes_cd: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    includes_monitoring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    includes_tests: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_recommended: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Show in recommendations

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
    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="template",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name={self.name}, workload={self.workload_type})>"
