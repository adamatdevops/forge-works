"""
Generic Job Spec and result models.

The Job Spec is the universal format that ForgeWorks uses to describe
work to be done. Adapters translate it into control-plane-specific resources
(K8s Jobs, Argo Workflows, etc).
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class JobSpec(BaseModel):
    """Generic Job Specification — translated by adapters to native resources."""

    job_id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}")
    correlation_id: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Source insight that triggered this job
    insight_id: str = ""
    pattern_id: str = ""
    pattern_name: str = ""
    severity: str = ""
    group_key: str = ""

    # Adapter selection
    adapter: str = "kubernetes-job"

    # Task definition
    task_type: str = ""  # e.g., "create-github-issue", "send-slack-alert", "run-scan"
    task_image: str = ""

    # Input data for the task
    input_data: dict = Field(default_factory=dict)

    # Resource requirements
    cpu: str = "250m"
    memory: str = "256Mi"
    timeout_seconds: int = 300

    # Labels for tracking
    labels: dict = Field(default_factory=dict)


class JobResult(BaseModel):
    """Result of a dispatched job."""

    job_id: str
    correlation_id: str = ""
    status: JobStatus
    adapter: str = ""
    exit_code: int | None = None
    output: str | None = None
    duration_ms: int = 0
    error: str | None = None
    completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Insight(BaseModel):
    """Input model — matches the Insight schema from Insight Generator."""

    insight_id: str = ""
    pattern_id: str = ""
    pattern_name: str = ""
    severity: str = ""
    message: str = ""
    timestamp: str = ""
    source: str = ""
    group_key: str = ""
    recommendations: list[str] = Field(default_factory=list)
    alert_count: int = 0
    model_score: float | None = None
    trigger_event_ids: list[str] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
