"""
Pydantic models matching the CUE schema definitions.

@schema: src/normalizer/cue/forgeworks.cue
"""

import hashlib
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Resources(BaseModel):
    """Canonical numeric resource units."""
    cpu_millicores: int = 0
    memory_mib: int = 0
    storage_gib: int | None = None


class Workload(BaseModel):
    """Unified compute definition — K8s Deployment, ECS Task, etc."""
    name: str
    namespace: str = "default"
    replicas: int = 1
    image: str = ""
    resources: Resources = Field(default_factory=Resources)
    labels: dict[str, str] = Field(default_factory=dict)
    source: str = "kubernetes"
    healthy: bool = True
    ready: bool = True
    crash_loops: int = 0
    has_liveness_probe: bool = False
    has_readiness_probe: bool = False
    hpa: dict | None = None


class Service(BaseModel):
    """Unified network exposure."""
    name: str
    namespace: str = "default"
    port: int
    protocol: str = "TCP"
    type: str = "ClusterIP"
    selector: dict[str, str] = Field(default_factory=dict)
    source: str = "kubernetes"


class Stage(BaseModel):
    """A single stage/job in a pipeline."""
    name: str
    image: str = ""
    steps: list[str] = Field(default_factory=list)
    depends: list[str] = Field(default_factory=list)
    status: str = ""        # queued | in_progress | completed
    conclusion: str = ""    # success | failure | cancelled | skipped | ""


class Pipeline(BaseModel):
    """Unified CI/CD definition — GitHub Actions, GitLab CI, Jenkins."""
    name: str
    repository: str
    trigger: list[str] = Field(default_factory=list)
    stages: list[Stage] = Field(default_factory=list)
    source: str = "github-actions"


class NormalizedConfig(BaseModel):
    """Wrapper with metadata — the output of normalization.

    @schema_version 2 — breaking rename of CUE camelCase fields to snake_case
    (crash_loops, has_liveness_probe, has_readiness_probe). resource_type is
    now a closed enum and codified in CUE.
    """
    config_id: str = Field(default_factory=lambda: f"cfg_{uuid.uuid4().hex[:12]}")
    resource_ref: str  # join key: "{source}:{namespace}/{name}"
    schema_version: int = 2
    observed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str
    resource_type: str  # "workload" | "service" | "pipeline" | "deployment"
    resource: dict = Field(default_factory=dict)
    raw_hash: str = ""

    @staticmethod
    def compute_hash(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()[:16]
