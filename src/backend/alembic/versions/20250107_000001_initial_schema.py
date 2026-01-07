"""Initial schema - ForgeWorks IDP

Revision ID: 20250107_000001
Revises:
Create Date: 2025-01-07

Creates all initial tables:
- teams
- templates
- services
- anomalies
- recommendations
- actions
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20250107_000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create ENUM types
    service_status = postgresql.ENUM(
        "healthy",
        "degraded",
        "unhealthy",
        "unknown",
        "provisioning",
        name="service_status",
        create_type=True,
    )
    service_status.create(op.get_bind(), checkfirst=True)

    service_tier = postgresql.ENUM(
        "critical",
        "standard",
        "internal",
        "experimental",
        name="service_tier",
        create_type=True,
    )
    service_tier.create(op.get_bind(), checkfirst=True)

    anomaly_type = postgresql.ENUM(
        "high_deploy_frequency",
        "consecutive_rollbacks",
        "pipeline_failing",
        "health_degraded",
        "unusual_error_rate",
        "resource_spike",
        "drift_detected",
        name="anomaly_type",
        create_type=True,
    )
    anomaly_type.create(op.get_bind(), checkfirst=True)

    anomaly_severity = postgresql.ENUM(
        "critical",
        "warning",
        "info",
        name="anomaly_severity",
        create_type=True,
    )
    anomaly_severity.create(op.get_bind(), checkfirst=True)

    action_type = postgresql.ENUM(
        "service_created",
        "service_updated",
        "service_deleted",
        "service_deployed",
        "service_rolled_back",
        "template_created",
        "template_updated",
        "template_deprecated",
        "recommendation_requested",
        "recommendation_accepted",
        "recommendation_overridden",
        "anomaly_detected",
        "anomaly_acknowledged",
        "anomaly_resolved",
        "team_created",
        "team_updated",
        name="action_type",
        create_type=True,
    )
    action_type.create(op.get_bind(), checkfirst=True)

    action_status = postgresql.ENUM(
        "pending",
        "in_progress",
        "completed",
        "failed",
        name="action_status",
        create_type=True,
    )
    action_status.create(op.get_bind(), checkfirst=True)

    # Create teams table
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("slack_channel", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create templates table
    op.create_table(
        "templates",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("workload_type", sa.String(50), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("capabilities", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("ideal_for", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("stack", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("repository_url", sa.String(500), nullable=True),
        sa.Column("documentation_url", sa.String(500), nullable=True),
        sa.Column("includes_ci", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("includes_cd", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("includes_monitoring", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("includes_tests", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_recommended", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create services table
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "team_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("teams.id"), nullable=False
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("templates.id"),
            nullable=True,
        ),
        sa.Column("status", service_status, nullable=False, server_default="unknown"),
        sa.Column("tier", service_tier, nullable=False, server_default="standard"),
        sa.Column("repository_url", sa.String(500), nullable=True),
        sa.Column("repository_branch", sa.String(100), nullable=False, server_default="main"),
        sa.Column("namespace", sa.String(100), nullable=True),
        sa.Column("argocd_app_name", sa.String(100), nullable=True),
        sa.Column("deploys_today", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rollbacks_this_week", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_deploy_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("documentation_url", sa.String(500), nullable=True),
        sa.Column("dashboard_url", sa.String(500), nullable=True),
        sa.Column("runbook_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create anomalies table
    op.create_table(
        "anomalies",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "service_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("services.id"),
            nullable=False,
        ),
        sa.Column("type", anomaly_type, nullable=False),
        sa.Column("severity", anomaly_severity, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("suggestion", sa.Text, nullable=True),
        sa.Column("detected_value", sa.String(100), nullable=True),
        sa.Column("expected_value", sa.String(100), nullable=True),
        sa.Column("detection_rule", sa.String(200), nullable=True),
        sa.Column("context", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_acknowledged", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("acknowledged_by", sa.String(100), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text, nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create recommendations table
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column(
            "team_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("teams.id"), nullable=True
        ),
        sa.Column("workload_type", sa.String(50), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("requirements", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("additional_context", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("recommendations", postgresql.JSONB, nullable=False),
        sa.Column(
            "top_template_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("templates.id"),
            nullable=False,
        ),
        sa.Column("top_score", sa.Float, nullable=False),
        sa.Column(
            "selected_template_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("templates.id"),
            nullable=True,
        ),
        sa.Column("was_override", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("override_reason", sa.String(500), nullable=True),
        sa.Column("warnings", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("model_version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("inference_time_ms", sa.Float, nullable=True),
        sa.Column("was_successful", sa.Boolean, nullable=True),
        sa.Column("feedback_score", sa.Float, nullable=True),
        sa.Column("feedback_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create actions table
    op.create_table(
        "actions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("type", action_type, nullable=False),
        sa.Column("status", action_status, nullable=False, server_default="completed"),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False, server_default="user"),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("target_name", sa.String(100), nullable=True),
        sa.Column(
            "team_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("teams.id"), nullable=True
        ),
        sa.Column(
            "service_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("services.id"),
            nullable=True,
        ),
        sa.Column("before_state", postgresql.JSONB, nullable=True),
        sa.Column("after_state", postgresql.JSONB, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index("ix_services_team_id", "services", ["team_id"])
    op.create_index("ix_services_template_id", "services", ["template_id"])
    op.create_index("ix_services_status", "services", ["status"])
    op.create_index("ix_anomalies_service_id", "anomalies", ["service_id"])
    op.create_index("ix_anomalies_severity", "anomalies", ["severity"])
    op.create_index("ix_anomalies_is_active", "anomalies", ["is_active"])
    op.create_index("ix_recommendations_team_id", "recommendations", ["team_id"])
    op.create_index("ix_recommendations_workload_type", "recommendations", ["workload_type"])
    op.create_index("ix_actions_type", "actions", ["type"])
    op.create_index("ix_actions_target_id", "actions", ["target_id"])
    op.create_index("ix_actions_created_at", "actions", ["created_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_actions_created_at")
    op.drop_index("ix_actions_target_id")
    op.drop_index("ix_actions_type")
    op.drop_index("ix_recommendations_workload_type")
    op.drop_index("ix_recommendations_team_id")
    op.drop_index("ix_anomalies_is_active")
    op.drop_index("ix_anomalies_severity")
    op.drop_index("ix_anomalies_service_id")
    op.drop_index("ix_services_status")
    op.drop_index("ix_services_template_id")
    op.drop_index("ix_services_team_id")

    # Drop tables
    op.drop_table("actions")
    op.drop_table("recommendations")
    op.drop_table("anomalies")
    op.drop_table("services")
    op.drop_table("templates")
    op.drop_table("teams")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS action_status")
    op.execute("DROP TYPE IF EXISTS action_type")
    op.execute("DROP TYPE IF EXISTS anomaly_severity")
    op.execute("DROP TYPE IF EXISTS anomaly_type")
    op.execute("DROP TYPE IF EXISTS service_tier")
    op.execute("DROP TYPE IF EXISTS service_status")
