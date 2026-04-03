"""
K8s event → NormalizedConfig normalizer.

Extracts workload and service definitions from K8s webhook events
and converts them to canonical numeric units.

Unit conversion:
  K8s "250m"  → 250 millicores
  K8s "1"     → 1000 millicores
  K8s "512Mi" → 512 MiB
  K8s "2Gi"   → 2048 MiB
"""

import json
import logging
import re

from app.normalizers.base import ConfigNormalizer
from app.schemas import NormalizedConfig, Resources, Service, Workload

logger = logging.getLogger(__name__)


def parse_cpu_millicores(cpu_str: str) -> int:
    """Convert K8s CPU string to millicores."""
    if not cpu_str:
        return 0
    cpu_str = str(cpu_str).strip()
    if cpu_str.endswith("m"):
        return int(cpu_str[:-1])
    try:
        return int(float(cpu_str) * 1000)
    except (ValueError, TypeError):
        return 0


def parse_memory_mib(mem_str: str) -> int:
    """Convert K8s memory string to MiB."""
    if not mem_str:
        return 0
    mem_str = str(mem_str).strip()
    match = re.match(r"^(\d+)(Ki|Mi|Gi|Ti|k|M|G|T)?$", mem_str)
    if not match:
        return 0
    value = int(match.group(1))
    unit = match.group(2) or ""
    multipliers = {
        "": 1 / (1024 * 1024),  # bytes → MiB
        "Ki": 1 / 1024,
        "Mi": 1,
        "Gi": 1024,
        "Ti": 1024 * 1024,
        "k": 1 / 1024,
        "M": 1,
        "G": 1024,
        "T": 1024 * 1024,
    }
    return int(value * multipliers.get(unit, 1))


class KubernetesNormalizer(ConfigNormalizer):

    @property
    def source(self) -> str:
        return "kubernetes"

    def normalize(self, event: dict) -> NormalizedConfig | None:
        """Normalize a K8s event into a config representation."""
        payload = event.get("payload", {})
        metadata = event.get("metadata", {})

        # Determine resource type from the event
        kind = payload.get("kind", "").lower()
        if not kind:
            kind = self._infer_kind(event)

        if kind in ("deployment", "statefulset", "daemonset", "replicaset"):
            return self._normalize_workload(event, payload, metadata)
        elif kind == "service":
            return self._normalize_service(event, payload, metadata)

        # For generic K8s events (pod crashes, etc), extract what we can
        if metadata.get("namespace") and metadata.get("name"):
            return self._normalize_generic(event, metadata)

        return None

    def _normalize_workload(self, event: dict, payload: dict, metadata: dict) -> NormalizedConfig:
        spec = payload.get("spec", {})
        template = spec.get("template", {}).get("spec", {})
        containers = template.get("containers", [])
        container = containers[0] if containers else {}

        resources = container.get("resources", {})
        requests = resources.get("requests", {})
        limits = resources.get("limits", {})

        # Use requests if available, fall back to limits
        cpu_str = requests.get("cpu", limits.get("cpu", "0"))
        mem_str = requests.get("memory", limits.get("memory", "0"))

        # Check probes
        has_liveness = "livenessProbe" in container
        has_readiness = "readinessProbe" in container

        # Check HPA (if present in event)
        hpa = None
        hpa_spec = payload.get("hpa", {})
        if hpa_spec:
            hpa = {
                "minReplicas": hpa_spec.get("minReplicas", 1),
                "maxReplicas": hpa_spec.get("maxReplicas", 1),
                "targetCPU": hpa_spec.get("targetCPUUtilizationPercentage", 80),
            }

        ns = metadata.get("namespace", payload.get("metadata", {}).get("namespace", "default"))
        name = metadata.get("name", payload.get("metadata", {}).get("name", "unknown"))

        workload = Workload(
            name=name,
            namespace=ns,
            replicas=spec.get("replicas", 1),
            image=container.get("image", ""),
            resources=Resources(
                cpu_millicores=parse_cpu_millicores(cpu_str),
                memory_mib=parse_memory_mib(mem_str),
            ),
            labels=payload.get("metadata", {}).get("labels", {}),
            source="kubernetes",
            has_liveness_probe=has_liveness,
            has_readiness_probe=has_readiness,
            hpa=hpa,
        )

        raw_bytes = json.dumps(payload, sort_keys=True).encode()
        return NormalizedConfig(
            resource_ref=f"kubernetes:{ns}/{name}",
            source="kubernetes",
            resource_type="workload",
            resource=workload.model_dump(),
            raw_hash=NormalizedConfig.compute_hash(raw_bytes),
        )

    def _normalize_service(self, event: dict, payload: dict, metadata: dict) -> NormalizedConfig:
        spec = payload.get("spec", {})
        ports = spec.get("ports", [])
        port = ports[0].get("port", 0) if ports else 0
        protocol = ports[0].get("protocol", "TCP") if ports else "TCP"

        ns = metadata.get("namespace", payload.get("metadata", {}).get("namespace", "default"))
        name = metadata.get("name", payload.get("metadata", {}).get("name", "unknown"))

        service = Service(
            name=name,
            namespace=ns,
            port=port,
            protocol=protocol,
            type=spec.get("type", "ClusterIP"),
            selector=spec.get("selector", {}),
            source="kubernetes",
        )

        raw_bytes = json.dumps(payload, sort_keys=True).encode()
        return NormalizedConfig(
            resource_ref=f"kubernetes:{ns}/{name}",
            source="kubernetes",
            resource_type="service",
            resource=service.model_dump(),
            raw_hash=NormalizedConfig.compute_hash(raw_bytes),
        )

    def _normalize_generic(self, event: dict, metadata: dict) -> NormalizedConfig:
        """Minimal normalization for events without full resource spec."""
        ns = metadata.get("namespace", "default")
        name = metadata.get("name", "unknown")

        return NormalizedConfig(
            resource_ref=f"kubernetes:{ns}/{name}",
            source="kubernetes",
            resource_type="workload",
            resource={
                "name": name,
                "namespace": ns,
                "source": "kubernetes",
            },
            raw_hash="",
        )

    def _infer_kind(self, event: dict) -> str:
        """Infer K8s resource kind from event type."""
        event_type = event.get("type", "")
        if "deploy" in event_type:
            return "deployment"
        if "service" in event_type:
            return "service"
        if "pod" in event_type:
            return "deployment"  # pods belong to workloads
        return ""
