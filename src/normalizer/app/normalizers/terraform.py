"""
Terraform event → NormalizedConfig normalizer.

Consumes Terraform plan/state JSON shapes (resource entries, not the full plan
envelope) and converts them to canonical numeric units.

Unit conversion:
  ECS cpu (AWS units, 1024 = 1 vCPU)  → cpu_millicores  (1024 → 1000)
  ECS memory (already MiB)            → memory_mib      (passthrough)
  K8s-via-TF "250m"  → 250 millicores
  K8s-via-TF "1"     → 1000 millicores
  K8s-via-TF "512Mi" → 512 MiB
  K8s-via-TF "2Gi"   → 2048 MiB

Supported resource types:
  Workloads: aws_ecs_task_definition, aws_ecs_service,
             kubernetes_deployment, kubernetes_deployment_v1,
             kubernetes_stateful_set, kubernetes_stateful_set_v1
  Services:  aws_lb, aws_lb_listener, aws_lb_target_group,
             kubernetes_service, kubernetes_service_v1
"""

import json
import logging
import re

from app.normalizers.base import ConfigNormalizer
from app.schemas import NormalizedConfig, Resources, Service, Workload

logger = logging.getLogger(__name__)


_WORKLOAD_TYPES = {
    "aws_ecs_task_definition",
    "aws_ecs_service",
    "kubernetes_deployment",
    "kubernetes_deployment_v1",
    "kubernetes_stateful_set",
    "kubernetes_stateful_set_v1",
    "kubernetes_daemonset",
    "kubernetes_daemonset_v1",
}

_SERVICE_TYPES = {
    "aws_lb",
    "aws_lb_listener",
    "aws_lb_target_group",
    "kubernetes_service",
    "kubernetes_service_v1",
}


def parse_cpu_millicores(cpu_value) -> int:
    """Convert a Terraform CPU value to millicores.

    Accepts:
      - int/float in AWS ECS CPU units (1024 = 1 vCPU = 1000 millicores)
      - K8s-style strings: "250m", "1", "1.5"
    """
    if cpu_value is None or cpu_value == "":
        return 0
    if isinstance(cpu_value, (int, float)):
        return int(round(float(cpu_value) * 1000 / 1024))
    s = str(cpu_value).strip()
    if s.endswith("m"):
        try:
            return int(s[:-1])
        except ValueError:
            return 0
    try:
        f = float(s)
    except ValueError:
        return 0
    if f >= 16:
        return int(round(f * 1000 / 1024))
    return int(round(f * 1000))


def parse_memory_mib(mem_value) -> int:
    """Convert a Terraform memory value to MiB.

    Accepts:
      - int/float in MiB (ECS convention)
      - K8s-style strings: "512Mi", "2Gi", "1024"
    """
    if mem_value is None or mem_value == "":
        return 0
    if isinstance(mem_value, (int, float)):
        return int(mem_value)
    s = str(mem_value).strip()
    match = re.match(r"^(\d+)(Ki|Mi|Gi|Ti|k|M|G|T)?$", s)
    if not match:
        return 0
    value = int(match.group(1))
    unit = match.group(2) or "Mi"
    multipliers = {
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


class TerraformNormalizer(ConfigNormalizer):

    @property
    def source(self) -> str:
        return "terraform"

    def normalize(self, event: dict) -> NormalizedConfig | None:
        payload = event.get("payload", {}) or {}
        metadata = event.get("metadata", {}) or {}

        resource_type = (
            payload.get("type")
            or payload.get("resource_type")
            or metadata.get("resource_type")
            or ""
        ).lower()

        if resource_type in _WORKLOAD_TYPES:
            return self._normalize_workload(payload, metadata, resource_type)
        if resource_type in _SERVICE_TYPES:
            return self._normalize_service(payload, metadata, resource_type)

        logger.info("Skipping unsupported terraform resource_type=%s", resource_type)
        return None

    def _normalize_workload(self, payload: dict, metadata: dict, resource_type: str) -> NormalizedConfig:
        values = payload.get("values", payload.get("attributes", {})) or {}

        name = (
            values.get("name")
            or values.get("family")
            or self._extract_k8s_name(values)
            or payload.get("name")
            or metadata.get("name")
            or "unknown"
        )
        namespace = (
            values.get("namespace")
            or self._extract_k8s_namespace(values)
            or payload.get("namespace")
            or metadata.get("namespace")
            or "default"
        )

        cpu_str, mem_str, image, replicas = self._extract_compute(values, resource_type)
        labels = self._extract_labels(values)

        workload = Workload(
            name=name,
            namespace=namespace,
            replicas=replicas,
            image=image or "",
            resources=Resources(
                cpu_millicores=parse_cpu_millicores(cpu_str),
                memory_mib=parse_memory_mib(mem_str),
            ),
            labels=labels,
            source="terraform",
        )

        raw_bytes = json.dumps(payload, sort_keys=True).encode()
        return NormalizedConfig(
            resource_ref=f"terraform:{namespace}/{name}",
            source="terraform",
            resource_type="workload",
            resource=workload.model_dump(),
            raw_hash=NormalizedConfig.compute_hash(raw_bytes),
        )

    def _normalize_service(self, payload: dict, metadata: dict, resource_type: str) -> NormalizedConfig:
        values = payload.get("values", payload.get("attributes", {})) or {}

        name = (
            values.get("name")
            or self._extract_k8s_name(values)
            or payload.get("name")
            or metadata.get("name")
            or "unknown"
        )
        namespace = (
            values.get("namespace")
            or self._extract_k8s_namespace(values)
            or metadata.get("namespace")
            or "default"
        )

        port, protocol, svc_type = self._extract_network(values, resource_type)
        selector = values.get("selector") or self._extract_k8s_selector(values) or {}

        service = Service(
            name=name,
            namespace=namespace,
            port=port,
            protocol=protocol,
            type=svc_type,
            selector=selector,
            source="terraform",
        )

        raw_bytes = json.dumps(payload, sort_keys=True).encode()
        return NormalizedConfig(
            resource_ref=f"terraform:{namespace}/{name}",
            source="terraform",
            resource_type="service",
            resource=service.model_dump(),
            raw_hash=NormalizedConfig.compute_hash(raw_bytes),
        )

    def _extract_compute(self, values: dict, resource_type: str):
        """Return (cpu_str_or_num, mem_str_or_num, image, replicas)."""
        if resource_type in ("aws_ecs_task_definition", "aws_ecs_service"):
            cpu = values.get("cpu")
            mem = values.get("memory")
            image = ""
            container_defs = values.get("container_definitions")
            if isinstance(container_defs, str):
                try:
                    container_defs = json.loads(container_defs)
                except (ValueError, TypeError):
                    container_defs = []
            if isinstance(container_defs, list) and container_defs:
                first = container_defs[0]
                image = first.get("image", "")
                cpu = cpu or first.get("cpu")
                mem = mem or first.get("memory")
            replicas = values.get("desired_count", 1)
            return cpu, mem, image, replicas

        # K8s-via-Terraform
        spec = self._first(values.get("spec"))
        template = self._first((spec or {}).get("template"))
        pod_spec = self._first((template or {}).get("spec"))
        containers = (pod_spec or {}).get("container") or (pod_spec or {}).get("containers") or []
        if isinstance(containers, dict):
            containers = [containers]
        first_container = containers[0] if containers else {}

        image = first_container.get("image", "")
        resources = self._first(first_container.get("resources")) or {}
        requests = self._first(resources.get("requests")) or {}
        limits = self._first(resources.get("limits")) or {}
        cpu = requests.get("cpu", limits.get("cpu", 0))
        mem = requests.get("memory", limits.get("memory", 0))
        replicas = (spec or {}).get("replicas", 1)
        return cpu, mem, image, replicas

    def _extract_network(self, values: dict, resource_type: str):
        """Return (port, protocol, type)."""
        if resource_type == "aws_lb":
            return 80, "TCP", "LoadBalancer"
        if resource_type == "aws_lb_listener":
            return int(values.get("port", 0) or 0), str(values.get("protocol", "TCP")).upper(), "LoadBalancer"
        if resource_type == "aws_lb_target_group":
            return int(values.get("port", 0) or 0), str(values.get("protocol", "TCP")).upper(), "LoadBalancer"

        spec = self._first(values.get("spec")) or {}
        ports = spec.get("port") or spec.get("ports") or []
        if isinstance(ports, dict):
            ports = [ports]
        first_port = ports[0] if ports else {}
        port = int(first_port.get("port", 0) or 0)
        protocol = str(first_port.get("protocol", "TCP")).upper()
        svc_type = spec.get("type", "ClusterIP")
        return port, protocol, svc_type

    @staticmethod
    def _first(node):
        """Terraform K8s provider often wraps nested blocks in single-element lists."""
        if isinstance(node, list):
            return node[0] if node else None
        return node

    @staticmethod
    def _extract_k8s_namespace(values: dict) -> str | None:
        meta = TerraformNormalizer._first(values.get("metadata"))
        if meta and isinstance(meta, dict):
            return meta.get("namespace")
        return None

    @staticmethod
    def _extract_k8s_name(values: dict) -> str | None:
        meta = TerraformNormalizer._first(values.get("metadata"))
        if meta and isinstance(meta, dict):
            return meta.get("name")
        return None

    @staticmethod
    def _extract_labels(values: dict) -> dict[str, str]:
        meta = TerraformNormalizer._first(values.get("metadata"))
        if meta and isinstance(meta, dict):
            labels = meta.get("labels")
            if isinstance(labels, dict):
                return {str(k): str(v) for k, v in labels.items()}
        tags = values.get("tags")
        if isinstance(tags, dict):
            return {str(k): str(v) for k, v in tags.items()}
        return {}

    @staticmethod
    def _extract_k8s_selector(values: dict) -> dict[str, str]:
        spec = TerraformNormalizer._first(values.get("spec")) or {}
        selector = TerraformNormalizer._first(spec.get("selector")) or {}
        match_labels = TerraformNormalizer._first(selector.get("match_labels")) if isinstance(selector, dict) else None
        if isinstance(match_labels, dict):
            return {str(k): str(v) for k, v in match_labels.items()}
        if isinstance(selector, dict) and selector and not match_labels:
            flat = {k: v for k, v in selector.items() if isinstance(v, (str, int))}
            return {str(k): str(v) for k, v in flat.items()}
        return {}
