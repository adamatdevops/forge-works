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


class NormalizedConfig(BaseModel):
    """Wrapper with metadata — the output of normalization."""
    config_id: str = Field(default_factory=lambda: f"cfg_{uuid.uuid4().hex[:12]}")
    resource_ref: str  # join key: "{source}:{namespace}/{name}"
    schema_version: int = 1
    observed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str
    resource_type: str  # "workload", "service", "pipeline", "deployment"
    resource: dict = Field(default_factory=dict)
    raw_hash: str = ""

    @staticmethod
    def compute_hash(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()[:16]
