"""Kubernetes adapter for cluster management and monitoring."""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from app.adapters.base import AdapterHealth, AdapterMode, BaseAdapter

logger = logging.getLogger(__name__)

# Optional kubernetes client - only required for live mode
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    logger.info("Kubernetes client not installed - live mode unavailable")


class PodPhase(str, Enum):
    """Kubernetes pod phase."""

    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class DeploymentCondition(str, Enum):
    """Kubernetes deployment condition type."""

    AVAILABLE = "Available"
    PROGRESSING = "Progressing"
    REPLICA_FAILURE = "ReplicaFailure"


class ContainerState(str, Enum):
    """Container state."""

    WAITING = "waiting"
    RUNNING = "running"
    TERMINATED = "terminated"


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""

    cpu_cores: float  # CPU cores used
    cpu_percent: float  # CPU usage percentage
    memory_bytes: int  # Memory bytes used
    memory_percent: float  # Memory usage percentage

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_cores": round(self.cpu_cores, 3),
            "cpu_percent": round(self.cpu_percent, 1),
            "memory_bytes": self.memory_bytes,
            "memory_mb": round(self.memory_bytes / (1024 * 1024), 1),
            "memory_percent": round(self.memory_percent, 1),
        }


@dataclass
class Container:
    """Kubernetes container representation."""

    name: str
    image: str
    state: ContainerState
    ready: bool
    restart_count: int
    started_at: datetime | None = None
    reason: str | None = None  # For waiting/terminated states

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "image": self.image,
            "state": self.state.value,
            "ready": self.ready,
            "restart_count": self.restart_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "reason": self.reason,
        }


@dataclass
class Pod:
    """Kubernetes pod representation."""

    name: str
    namespace: str
    phase: PodPhase
    node_name: str | None
    ip: str | None
    containers: list[Container]
    created_at: datetime
    labels: dict[str, str] = field(default_factory=dict)
    metrics: ResourceMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "namespace": self.namespace,
            "phase": self.phase.value,
            "node_name": self.node_name,
            "ip": self.ip,
            "containers": [c.to_dict() for c in self.containers],
            "created_at": self.created_at.isoformat(),
            "labels": self.labels,
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "ready": all(c.ready for c in self.containers),
            "restart_count": sum(c.restart_count for c in self.containers),
        }


@dataclass
class Deployment:
    """Kubernetes deployment representation."""

    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    unavailable_replicas: int
    updated_replicas: int
    strategy: str
    created_at: datetime
    labels: dict[str, str] = field(default_factory=dict)
    conditions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "namespace": self.namespace,
            "replicas": self.replicas,
            "ready_replicas": self.ready_replicas,
            "available_replicas": self.available_replicas,
            "unavailable_replicas": self.unavailable_replicas,
            "updated_replicas": self.updated_replicas,
            "strategy": self.strategy,
            "created_at": self.created_at.isoformat(),
            "labels": self.labels,
            "conditions": self.conditions,
            "healthy": self.ready_replicas == self.replicas and self.unavailable_replicas == 0,
            "progress_percent": round((self.ready_replicas / max(self.replicas, 1)) * 100, 1),
        }


@dataclass
class Namespace:
    """Kubernetes namespace representation."""

    name: str
    phase: str  # "Active" or "Terminating"
    created_at: datetime
    labels: dict[str, str] = field(default_factory=dict)
    pod_count: int = 0
    deployment_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "phase": self.phase,
            "created_at": self.created_at.isoformat(),
            "labels": self.labels,
            "pod_count": self.pod_count,
            "deployment_count": self.deployment_count,
        }


@dataclass
class Node:
    """Kubernetes node representation."""

    name: str
    status: str  # "Ready", "NotReady", etc.
    roles: list[str]
    kubernetes_version: str
    os_image: str
    container_runtime: str
    created_at: datetime
    capacity: dict[str, Any] = field(default_factory=dict)
    allocatable: dict[str, Any] = field(default_factory=dict)
    conditions: list[dict[str, Any]] = field(default_factory=list)
    metrics: ResourceMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "roles": self.roles,
            "kubernetes_version": self.kubernetes_version,
            "os_image": self.os_image,
            "container_runtime": self.container_runtime,
            "created_at": self.created_at.isoformat(),
            "capacity": self.capacity,
            "allocatable": self.allocatable,
            "conditions": self.conditions,
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }


@dataclass
class ClusterInfo:
    """Kubernetes cluster information."""

    version: str
    platform: str
    node_count: int
    namespace_count: int
    pod_count: int
    deployment_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "platform": self.platform,
            "node_count": self.node_count,
            "namespace_count": self.namespace_count,
            "pod_count": self.pod_count,
            "deployment_count": self.deployment_count,
        }


class KubernetesAdapter(BaseAdapter):
    """Kubernetes adapter for cluster management and monitoring.

    In mock mode, returns realistic data for IDP demonstrations.
    In live mode, connects to a Kubernetes cluster (in-cluster or kubeconfig).
    """

    def __init__(
        self,
        mode: AdapterMode = AdapterMode.MOCK,
        kubeconfig_path: str | None = None,
        context: str | None = None,
        in_cluster: bool = False,
    ) -> None:
        """Initialize Kubernetes adapter.

        Args:
            mode: MOCK or LIVE mode
            kubeconfig_path: Path to kubeconfig file (for live mode)
            context: Kubernetes context to use (for live mode)
            in_cluster: Whether running inside a Kubernetes cluster
        """
        super().__init__(mode)
        self.kubeconfig_path = kubeconfig_path
        self.context = context
        self.in_cluster = in_cluster
        self._initialized = False
        self._core_api: Any = None
        self._apps_api: Any = None
        self._mock_data = self._generate_mock_data()

    def _ensure_client(self) -> bool:
        """Ensure Kubernetes client is initialized for live mode."""
        if self.is_mock():
            return True

        if not K8S_AVAILABLE:
            logger.error("Kubernetes client not installed")
            return False

        if self._initialized:
            return True

        try:
            if self.in_cluster:
                config.load_incluster_config()
            elif self.kubeconfig_path:
                config.load_kube_config(
                    config_file=self.kubeconfig_path,
                    context=self.context,
                )
            else:
                config.load_kube_config(context=self.context)

            self._core_api = client.CoreV1Api()
            self._apps_api = client.AppsV1Api()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            return False

    @property
    def name(self) -> str:
        """Return adapter name."""
        return "kubernetes"

    async def health_check(self) -> AdapterHealth:
        """Check Kubernetes API connectivity."""
        self._last_health_check = datetime.now(UTC)

        if self.is_mock():
            await asyncio.sleep(0.01)
            return AdapterHealth(
                name=self.name,
                healthy=True,
                mode=self.mode,
                latency_ms=15.2,
                last_check=self._last_health_check,
            )

        if not self._ensure_client():
            return AdapterHealth(
                name=self.name,
                healthy=False,
                mode=self.mode,
                last_check=self._last_health_check,
                error="Failed to initialize Kubernetes client",
            )

        try:
            start = datetime.now(UTC)
            # Run synchronous k8s API call in thread pool
            await asyncio.to_thread(self._core_api.get_api_versions)
            latency = (datetime.now(UTC) - start).total_seconds() * 1000

            return AdapterHealth(
                name=self.name,
                healthy=True,
                mode=self.mode,
                latency_ms=latency,
                last_check=self._last_health_check,
            )
        except Exception as e:
            logger.error(f"Kubernetes health check failed: {e}")
            return AdapterHealth(
                name=self.name,
                healthy=False,
                mode=self.mode,
                last_check=self._last_health_check,
                error=str(e),
            )

    async def get_cluster_info(self) -> ClusterInfo:
        """Get cluster overview information."""
        if self.is_mock():
            return self._mock_data["cluster_info"]

        if not self._ensure_client():
            raise RuntimeError("Kubernetes client not initialized")

        try:
            # Get version info
            version_api = client.VersionApi()
            version_info = await asyncio.to_thread(version_api.get_code)

            # Get counts
            nodes = await asyncio.to_thread(self._core_api.list_node)
            namespaces = await asyncio.to_thread(self._core_api.list_namespace)
            pods = await asyncio.to_thread(self._core_api.list_pod_for_all_namespaces)
            deployments = await asyncio.to_thread(self._apps_api.list_deployment_for_all_namespaces)

            return ClusterInfo(
                version=f"{version_info.major}.{version_info.minor}",
                platform=version_info.platform,
                node_count=len(nodes.items),
                namespace_count=len(namespaces.items),
                pod_count=len(pods.items),
                deployment_count=len(deployments.items),
            )
        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            raise

    async def list_namespaces(self) -> list[Namespace]:
        """List all namespaces in the cluster."""
        if self.is_mock():
            return self._mock_data["namespaces"]

        if not self._ensure_client():
            raise RuntimeError("Kubernetes client not initialized")

        try:
            ns_list = await asyncio.to_thread(self._core_api.list_namespace)
            namespaces = []

            for ns in ns_list.items:
                # Get pod and deployment counts for each namespace
                pods = await asyncio.to_thread(
                    self._core_api.list_namespaced_pod,
                    ns.metadata.name,
                )
                deployments = await asyncio.to_thread(
                    self._apps_api.list_namespaced_deployment,
                    ns.metadata.name,
                )

                namespaces.append(
                    Namespace(
                        name=ns.metadata.name,
                        phase=ns.status.phase,
                        created_at=ns.metadata.creation_timestamp,
                        labels=ns.metadata.labels or {},
                        pod_count=len(pods.items),
                        deployment_count=len(deployments.items),
                    )
                )

            return namespaces
        except Exception as e:
            logger.error(f"Failed to list namespaces: {e}")
            raise

    async def list_nodes(self) -> list[Node]:
        """List all nodes in the cluster."""
        if self.is_mock():
            return self._mock_data["nodes"]

        if not self._ensure_client():
            raise RuntimeError("Kubernetes client not initialized")

        try:
            node_list = await asyncio.to_thread(self._core_api.list_node)
            nodes = []

            for n in node_list.items:
                # Determine node status from conditions
                status = "Unknown"
                conditions = []
                for cond in n.status.conditions or []:
                    conditions.append(
                        {
                            "type": cond.type,
                            "status": cond.status,
                            "reason": cond.reason,
                            "message": cond.message,
                        }
                    )
                    if cond.type == "Ready":
                        status = "Ready" if cond.status == "True" else "NotReady"

                # Extract roles from labels
                roles = []
                for label in n.metadata.labels or {}:
                    if label.startswith("node-role.kubernetes.io/"):
                        roles.append(label.split("/")[1])
                if not roles:
                    roles = ["worker"]

                nodes.append(
                    Node(
                        name=n.metadata.name,
                        status=status,
                        roles=roles,
                        kubernetes_version=n.status.node_info.kubelet_version,
                        os_image=n.status.node_info.os_image,
                        container_runtime=n.status.node_info.container_runtime_version,
                        created_at=n.metadata.creation_timestamp,
                        capacity={
                            "cpu": n.status.capacity.get("cpu"),
                            "memory": n.status.capacity.get("memory"),
                            "pods": n.status.capacity.get("pods"),
                        },
                        allocatable={
                            "cpu": n.status.allocatable.get("cpu"),
                            "memory": n.status.allocatable.get("memory"),
                            "pods": n.status.allocatable.get("pods"),
                        },
                        conditions=conditions,
                    )
                )

            return nodes
        except Exception as e:
            logger.error(f"Failed to list nodes: {e}")
            raise

    async def list_deployments(
        self,
        namespace: str | None = None,
        label_selector: str | None = None,
    ) -> list[Deployment]:
        """List deployments, optionally filtered by namespace."""
        if self.is_mock():
            deployments = self._mock_data["deployments"]
            if namespace:
                deployments = [d for d in deployments if d.namespace == namespace]
            return deployments

        if not self._ensure_client():
            raise RuntimeError("Kubernetes client not initialized")

        try:
            if namespace:
                dep_list = await asyncio.to_thread(
                    self._apps_api.list_namespaced_deployment,
                    namespace,
                    label_selector=label_selector,
                )
            else:
                dep_list = await asyncio.to_thread(
                    self._apps_api.list_deployment_for_all_namespaces,
                    label_selector=label_selector,
                )

            deployments = []
            for d in dep_list.items:
                conditions = []
                for cond in d.status.conditions or []:
                    conditions.append(
                        {
                            "type": cond.type,
                            "status": cond.status,
                            "reason": cond.reason,
                            "message": cond.message,
                            "last_update": cond.last_update_time.isoformat()
                            if cond.last_update_time
                            else None,
                        }
                    )

                deployments.append(
                    Deployment(
                        name=d.metadata.name,
                        namespace=d.metadata.namespace,
                        replicas=d.spec.replicas or 0,
                        ready_replicas=d.status.ready_replicas or 0,
                        available_replicas=d.status.available_replicas or 0,
                        unavailable_replicas=d.status.unavailable_replicas or 0,
                        updated_replicas=d.status.updated_replicas or 0,
                        strategy=d.spec.strategy.type if d.spec.strategy else "RollingUpdate",
                        created_at=d.metadata.creation_timestamp,
                        labels=d.metadata.labels or {},
                        conditions=conditions,
                    )
                )

            return deployments
        except Exception as e:
            logger.error(f"Failed to list deployments: {e}")
            raise

    async def get_deployment(self, name: str, namespace: str) -> Deployment | None:
        """Get a specific deployment by name and namespace."""
        if self.is_mock():
            for d in self._mock_data["deployments"]:
                if d.name == name and d.namespace == namespace:
                    return d
            return None

        if not self._ensure_client():
            raise RuntimeError("Kubernetes client not initialized")

        try:
            d = await asyncio.to_thread(
                self._apps_api.read_namespaced_deployment,
                name,
                namespace,
            )

            conditions = []
            for cond in d.status.conditions or []:
                conditions.append(
                    {
                        "type": cond.type,
                        "status": cond.status,
                        "reason": cond.reason,
                        "message": cond.message,
                    }
                )

            return Deployment(
                name=d.metadata.name,
                namespace=d.metadata.namespace,
                replicas=d.spec.replicas or 0,
                ready_replicas=d.status.ready_replicas or 0,
                available_replicas=d.status.available_replicas or 0,
                unavailable_replicas=d.status.unavailable_replicas or 0,
                updated_replicas=d.status.updated_replicas or 0,
                strategy=d.spec.strategy.type if d.spec.strategy else "RollingUpdate",
                created_at=d.metadata.creation_timestamp,
                labels=d.metadata.labels or {},
                conditions=conditions,
            )
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"Failed to get deployment {namespace}/{name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get deployment {namespace}/{name}: {e}")
            raise

    async def list_pods(
        self,
        namespace: str | None = None,
        label_selector: str | None = None,
    ) -> list[Pod]:
        """List pods, optionally filtered by namespace."""
        if self.is_mock():
            pods = self._mock_data["pods"]
            if namespace:
                pods = [p for p in pods if p.namespace == namespace]
            return pods

        if not self._ensure_client():
            raise RuntimeError("Kubernetes client not initialized")

        try:
            if namespace:
                pod_list = await asyncio.to_thread(
                    self._core_api.list_namespaced_pod,
                    namespace,
                    label_selector=label_selector,
                )
            else:
                pod_list = await asyncio.to_thread(
                    self._core_api.list_pod_for_all_namespaces,
                    label_selector=label_selector,
                )

            pods = []
            for p in pod_list.items:
                containers = []
                for cs in p.status.container_statuses or []:
                    state = ContainerState.WAITING
                    started_at = None
                    reason = None

                    if cs.state.running:
                        state = ContainerState.RUNNING
                        started_at = cs.state.running.started_at
                    elif cs.state.terminated:
                        state = ContainerState.TERMINATED
                        reason = cs.state.terminated.reason
                    elif cs.state.waiting:
                        state = ContainerState.WAITING
                        reason = cs.state.waiting.reason

                    containers.append(
                        Container(
                            name=cs.name,
                            image=cs.image,
                            state=state,
                            ready=cs.ready,
                            restart_count=cs.restart_count,
                            started_at=started_at,
                            reason=reason,
                        )
                    )

                pods.append(
                    Pod(
                        name=p.metadata.name,
                        namespace=p.metadata.namespace,
                        phase=PodPhase(p.status.phase) if p.status.phase else PodPhase.UNKNOWN,
                        node_name=p.spec.node_name,
                        ip=p.status.pod_ip,
                        containers=containers,
                        created_at=p.metadata.creation_timestamp,
                        labels=p.metadata.labels or {},
                    )
                )

            return pods
        except Exception as e:
            logger.error(f"Failed to list pods: {e}")
            raise

    async def get_pod_logs(
        self,
        name: str,
        namespace: str,
        container: str | None = None,
        tail_lines: int = 100,
    ) -> str:
        """Get logs from a pod."""
        if self.is_mock():
            return self._generate_mock_logs(name, tail_lines)

        if not self._ensure_client():
            raise RuntimeError("Kubernetes client not initialized")

        try:
            logs = await asyncio.to_thread(
                self._core_api.read_namespaced_pod_log,
                name,
                namespace,
                container=container,
                tail_lines=tail_lines,
            )
            return logs
        except Exception as e:
            logger.error(f"Failed to get logs for {namespace}/{name}: {e}")
            raise

    def _generate_mock_data(self) -> dict[str, Any]:
        """Generate mock Kubernetes data for demonstrations."""
        now = datetime.now(UTC)

        # Cluster info
        cluster_info = ClusterInfo(
            version="1.29",
            platform="linux/amd64",
            node_count=3,
            namespace_count=8,
            pod_count=24,
            deployment_count=12,
        )

        # Namespaces
        namespaces = [
            Namespace(
                name="default",
                phase="Active",
                created_at=now - timedelta(days=90),
                labels={"kubernetes.io/metadata.name": "default"},
                pod_count=2,
                deployment_count=1,
            ),
            Namespace(
                name="forge-platform",
                phase="Active",
                created_at=now - timedelta(days=60),
                labels={"app.kubernetes.io/part-of": "forge-works"},
                pod_count=6,
                deployment_count=3,
            ),
            Namespace(
                name="forge-services",
                phase="Active",
                created_at=now - timedelta(days=45),
                labels={"app.kubernetes.io/part-of": "forge-works"},
                pod_count=8,
                deployment_count=4,
            ),
            Namespace(
                name="monitoring",
                phase="Active",
                created_at=now - timedelta(days=80),
                labels={"app.kubernetes.io/component": "observability"},
                pod_count=4,
                deployment_count=2,
            ),
            Namespace(
                name="kube-system",
                phase="Active",
                created_at=now - timedelta(days=90),
                labels={"kubernetes.io/metadata.name": "kube-system"},
                pod_count=4,
                deployment_count=2,
            ),
        ]

        # Nodes
        nodes = [
            Node(
                name="forge-node-1",
                status="Ready",
                roles=["control-plane", "master"],
                kubernetes_version="v1.29.2",
                os_image="Ubuntu 22.04 LTS",
                container_runtime="containerd://1.7.2",
                created_at=now - timedelta(days=90),
                capacity={"cpu": "4", "memory": "16Gi", "pods": "110"},
                allocatable={"cpu": "3800m", "memory": "15Gi", "pods": "110"},
                conditions=[{"type": "Ready", "status": "True"}],
                metrics=ResourceMetrics(
                    cpu_cores=1.2,
                    cpu_percent=31.6,
                    memory_bytes=8 * 1024 * 1024 * 1024,
                    memory_percent=50.0,
                ),
            ),
            Node(
                name="forge-node-2",
                status="Ready",
                roles=["worker"],
                kubernetes_version="v1.29.2",
                os_image="Ubuntu 22.04 LTS",
                container_runtime="containerd://1.7.2",
                created_at=now - timedelta(days=90),
                capacity={"cpu": "8", "memory": "32Gi", "pods": "110"},
                allocatable={"cpu": "7800m", "memory": "31Gi", "pods": "110"},
                conditions=[{"type": "Ready", "status": "True"}],
                metrics=ResourceMetrics(
                    cpu_cores=3.5,
                    cpu_percent=43.8,
                    memory_bytes=18 * 1024 * 1024 * 1024,
                    memory_percent=56.3,
                ),
            ),
            Node(
                name="forge-node-3",
                status="Ready",
                roles=["worker"],
                kubernetes_version="v1.29.2",
                os_image="Ubuntu 22.04 LTS",
                container_runtime="containerd://1.7.2",
                created_at=now - timedelta(days=85),
                capacity={"cpu": "8", "memory": "32Gi", "pods": "110"},
                allocatable={"cpu": "7800m", "memory": "31Gi", "pods": "110"},
                conditions=[{"type": "Ready", "status": "True"}],
                metrics=ResourceMetrics(
                    cpu_cores=2.8,
                    cpu_percent=35.0,
                    memory_bytes=14 * 1024 * 1024 * 1024,
                    memory_percent=43.8,
                ),
            ),
        ]

        # Deployments
        deployments = [
            Deployment(
                name="forge-api",
                namespace="forge-platform",
                replicas=3,
                ready_replicas=3,
                available_replicas=3,
                unavailable_replicas=0,
                updated_replicas=3,
                strategy="RollingUpdate",
                created_at=now - timedelta(days=30),
                labels={"app": "forge-api", "tier": "backend"},
                conditions=[
                    {"type": "Available", "status": "True", "reason": "MinimumReplicasAvailable"},
                    {"type": "Progressing", "status": "True", "reason": "NewReplicaSetAvailable"},
                ],
            ),
            Deployment(
                name="forge-frontend",
                namespace="forge-platform",
                replicas=2,
                ready_replicas=2,
                available_replicas=2,
                unavailable_replicas=0,
                updated_replicas=2,
                strategy="RollingUpdate",
                created_at=now - timedelta(days=30),
                labels={"app": "forge-frontend", "tier": "frontend"},
                conditions=[
                    {"type": "Available", "status": "True", "reason": "MinimumReplicasAvailable"},
                ],
            ),
            Deployment(
                name="user-service",
                namespace="forge-services",
                replicas=3,
                ready_replicas=3,
                available_replicas=3,
                unavailable_replicas=0,
                updated_replicas=3,
                strategy="RollingUpdate",
                created_at=now - timedelta(days=25),
                labels={"app": "user-service", "team": "platform"},
                conditions=[
                    {"type": "Available", "status": "True", "reason": "MinimumReplicasAvailable"},
                ],
            ),
            Deployment(
                name="order-service",
                namespace="forge-services",
                replicas=3,
                ready_replicas=2,
                available_replicas=2,
                unavailable_replicas=1,
                updated_replicas=3,
                strategy="RollingUpdate",
                created_at=now - timedelta(days=20),
                labels={"app": "order-service", "team": "commerce"},
                conditions=[
                    {"type": "Available", "status": "True", "reason": "MinimumReplicasAvailable"},
                    {"type": "Progressing", "status": "True", "reason": "ReplicaSetUpdated"},
                ],
            ),
            Deployment(
                name="prometheus",
                namespace="monitoring",
                replicas=1,
                ready_replicas=1,
                available_replicas=1,
                unavailable_replicas=0,
                updated_replicas=1,
                strategy="Recreate",
                created_at=now - timedelta(days=60),
                labels={"app": "prometheus", "component": "monitoring"},
                conditions=[
                    {"type": "Available", "status": "True", "reason": "MinimumReplicasAvailable"},
                ],
            ),
            Deployment(
                name="grafana",
                namespace="monitoring",
                replicas=1,
                ready_replicas=1,
                available_replicas=1,
                unavailable_replicas=0,
                updated_replicas=1,
                strategy="RollingUpdate",
                created_at=now - timedelta(days=60),
                labels={"app": "grafana", "component": "monitoring"},
                conditions=[
                    {"type": "Available", "status": "True", "reason": "MinimumReplicasAvailable"},
                ],
            ),
        ]

        # Pods
        pods = []
        for dep in deployments:
            for i in range(dep.ready_replicas):
                pod_suffix = f"-{random.randint(10000, 99999)}"
                containers = [
                    Container(
                        name=dep.name,
                        image=f"forge-registry/{dep.name}:v1.2.{random.randint(0, 9)}",
                        state=ContainerState.RUNNING,
                        ready=True,
                        restart_count=random.randint(0, 2),
                        started_at=now - timedelta(hours=random.randint(1, 72)),
                    )
                ]

                pods.append(
                    Pod(
                        name=f"{dep.name}{pod_suffix}",
                        namespace=dep.namespace,
                        phase=PodPhase.RUNNING,
                        node_name=random.choice(["forge-node-2", "forge-node-3"]),
                        ip=f"10.244.{random.randint(1, 3)}.{random.randint(1, 254)}",
                        containers=containers,
                        created_at=now - timedelta(hours=random.randint(1, 72)),
                        labels=dep.labels,
                        metrics=ResourceMetrics(
                            cpu_cores=random.uniform(0.1, 0.8),
                            cpu_percent=random.uniform(5, 40),
                            memory_bytes=random.randint(100, 500) * 1024 * 1024,
                            memory_percent=random.uniform(10, 50),
                        ),
                    )
                )

            # Add unhealthy pod for order-service
            if dep.unavailable_replicas > 0:
                pods.append(
                    Pod(
                        name=f"{dep.name}-{random.randint(10000, 99999)}",
                        namespace=dep.namespace,
                        phase=PodPhase.PENDING,
                        node_name=None,
                        ip=None,
                        containers=[
                            Container(
                                name=dep.name,
                                image=f"forge-registry/{dep.name}:v1.2.5",
                                state=ContainerState.WAITING,
                                ready=False,
                                restart_count=3,
                                reason="ImagePullBackOff",
                            )
                        ],
                        created_at=now - timedelta(minutes=15),
                        labels=dep.labels,
                    )
                )

        return {
            "cluster_info": cluster_info,
            "namespaces": namespaces,
            "nodes": nodes,
            "deployments": deployments,
            "pods": pods,
        }

    def _generate_mock_logs(self, pod_name: str, tail_lines: int) -> str:
        """Generate mock pod logs."""
        log_templates = [
            "{timestamp} INFO  [main] Application started successfully",
            "{timestamp} INFO  [http] Listening on port 8080",
            "{timestamp} DEBUG [pool] Connection pool initialized with 10 connections",
            "{timestamp} INFO  [request] GET /health - 200 OK (2ms)",
            "{timestamp} INFO  [request] POST /api/v1/data - 201 Created (45ms)",
            "{timestamp} WARN  [cache] Cache miss for key: user_123",
            "{timestamp} INFO  [request] GET /api/v1/users/123 - 200 OK (12ms)",
            "{timestamp} DEBUG [db] Query executed in 3ms",
            "{timestamp} INFO  [metrics] Metrics exported successfully",
            "{timestamp} INFO  [request] GET /readiness - 200 OK (1ms)",
        ]

        lines = []
        now = datetime.now(UTC)

        for i in range(min(tail_lines, len(log_templates) * 3)):
            template = random.choice(log_templates)
            timestamp = (now - timedelta(seconds=tail_lines - i)).strftime("%Y-%m-%d %H:%M:%S.%f")[
                :-3
            ]
            lines.append(template.format(timestamp=timestamp))

        return "\n".join(lines)


# Singleton instance for the application
_kubernetes_adapter: KubernetesAdapter | None = None


def get_kubernetes_adapter(
    mode: AdapterMode | None = None,
    kubeconfig_path: str | None = None,
    context: str | None = None,
    in_cluster: bool | None = None,
) -> KubernetesAdapter:
    """Get or create the Kubernetes adapter instance.

    If no arguments are provided, uses settings from config.
    """
    global _kubernetes_adapter

    if _kubernetes_adapter is None:
        from app.core.config import settings

        # Use provided values or fall back to settings
        adapter_mode = mode
        if adapter_mode is None:
            adapter_mode = (
                AdapterMode.LIVE
                if getattr(settings, "kubernetes_adapter_mode", "mock") == "live"
                else AdapterMode.MOCK
            )

        _kubernetes_adapter = KubernetesAdapter(
            mode=adapter_mode,
            kubeconfig_path=kubeconfig_path or getattr(settings, "kubernetes_kubeconfig", None),
            context=context or getattr(settings, "kubernetes_context", None),
            in_cluster=in_cluster
            if in_cluster is not None
            else getattr(settings, "kubernetes_in_cluster", False),
        )

    return _kubernetes_adapter


def reset_kubernetes_adapter() -> None:
    """Reset the Kubernetes adapter singleton (useful for testing)."""
    global _kubernetes_adapter
    _kubernetes_adapter = None
