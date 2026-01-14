"""ArgoCD adapter for GitOps deployment management."""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import httpx

from app.adapters.base import AdapterHealth, AdapterMode, BaseAdapter

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """ArgoCD application sync status."""

    SYNCED = "Synced"
    OUT_OF_SYNC = "OutOfSync"
    UNKNOWN = "Unknown"


class HealthStatus(str, Enum):
    """ArgoCD application health status."""

    HEALTHY = "Healthy"
    PROGRESSING = "Progressing"
    DEGRADED = "Degraded"
    SUSPENDED = "Suspended"
    MISSING = "Missing"
    UNKNOWN = "Unknown"


class OperationPhase(str, Enum):
    """ArgoCD operation phase."""

    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    ERROR = "Error"
    TERMINATING = "Terminating"


@dataclass
class ResourceStatus:
    """Status of a single Kubernetes resource."""

    group: str
    kind: str
    name: str
    namespace: str
    status: SyncStatus
    health: HealthStatus | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "group": self.group,
            "kind": self.kind,
            "name": self.name,
            "namespace": self.namespace,
            "status": self.status.value,
            "health": self.health.value if self.health else None,
            "message": self.message,
        }


@dataclass
class SyncResult:
    """Result of a sync operation."""

    revision: str
    started_at: datetime
    finished_at: datetime | None
    phase: OperationPhase
    message: str | None = None
    resources_synced: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "revision": self.revision,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "phase": self.phase.value,
            "message": self.message,
            "resources_synced": self.resources_synced,
        }


@dataclass
class Application:
    """ArgoCD application representation."""

    name: str
    namespace: str
    project: str
    repo_url: str
    target_revision: str
    path: str
    sync_status: SyncStatus
    health_status: HealthStatus
    created_at: datetime
    synced_at: datetime | None = None
    destination_server: str = "https://kubernetes.default.svc"
    destination_namespace: str = "default"
    auto_sync_enabled: bool = True
    resources: list[ResourceStatus] = field(default_factory=list)
    last_sync_result: SyncResult | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "namespace": self.namespace,
            "project": self.project,
            "repo_url": self.repo_url,
            "target_revision": self.target_revision,
            "path": self.path,
            "sync_status": self.sync_status.value,
            "health_status": self.health_status.value,
            "created_at": self.created_at.isoformat(),
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "destination_server": self.destination_server,
            "destination_namespace": self.destination_namespace,
            "auto_sync_enabled": self.auto_sync_enabled,
            "resources": [r.to_dict() for r in self.resources],
            "last_sync_result": self.last_sync_result.to_dict()
            if self.last_sync_result
            else None,
        }


@dataclass
class ApplicationSummary:
    """Summary view of an ArgoCD application."""

    name: str
    namespace: str
    sync_status: SyncStatus
    health_status: HealthStatus
    synced_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "namespace": self.namespace,
            "sync_status": self.sync_status.value,
            "health_status": self.health_status.value,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }


@dataclass
class SyncOperation:
    """An in-progress or completed sync operation."""

    app_name: str
    revision: str
    phase: OperationPhase
    started_at: datetime
    finished_at: datetime | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "app_name": self.app_name,
            "revision": self.revision,
            "phase": self.phase.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "message": self.message,
        }


class ArgoCDAdapter(BaseAdapter):
    """ArgoCD adapter for GitOps deployment management.

    In mock mode, returns realistic data for IDP demonstrations.
    In live mode, connects to ArgoCD API (requires server configuration).
    """

    def __init__(
        self,
        mode: AdapterMode = AdapterMode.MOCK,
        server_url: str | None = None,
        token: str | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize ArgoCD adapter."""
        super().__init__(mode)
        self.server_url = (server_url or "https://argocd.forge.internal").rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self._mock_apps = self._generate_mock_applications()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            self._client = httpx.AsyncClient(
                base_url=f"{self.server_url}/api/v1",
                headers=headers,
                timeout=30.0,
                verify=self.verify_ssl,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parse ISO datetime string from ArgoCD API."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _map_sync_status(self, status: str | None) -> SyncStatus:
        """Map ArgoCD sync status string to enum."""
        mapping = {
            "Synced": SyncStatus.SYNCED,
            "OutOfSync": SyncStatus.OUT_OF_SYNC,
        }
        return mapping.get(status or "", SyncStatus.UNKNOWN)

    def _map_health_status(self, status: str | None) -> HealthStatus:
        """Map ArgoCD health status string to enum."""
        mapping = {
            "Healthy": HealthStatus.HEALTHY,
            "Progressing": HealthStatus.PROGRESSING,
            "Degraded": HealthStatus.DEGRADED,
            "Suspended": HealthStatus.SUSPENDED,
            "Missing": HealthStatus.MISSING,
        }
        return mapping.get(status or "", HealthStatus.UNKNOWN)

    def _map_operation_phase(self, phase: str | None) -> OperationPhase:
        """Map ArgoCD operation phase string to enum."""
        mapping = {
            "Running": OperationPhase.RUNNING,
            "Succeeded": OperationPhase.SUCCEEDED,
            "Failed": OperationPhase.FAILED,
            "Error": OperationPhase.ERROR,
            "Terminating": OperationPhase.TERMINATING,
        }
        return mapping.get(phase or "", OperationPhase.FAILED)

    @property
    def name(self) -> str:
        """Return adapter name."""
        return "argocd"

    async def health_check(self) -> AdapterHealth:
        """Check ArgoCD API connectivity."""
        self._last_health_check = datetime.now(UTC)

        if self.is_mock():
            await asyncio.sleep(0.015)
            return AdapterHealth(
                name=self.name,
                healthy=True,
                mode=self.mode,
                latency_ms=15.2,
                last_check=self._last_health_check,
            )

        # Live mode - check ArgoCD version endpoint
        try:
            client = await self._get_client()
            start = datetime.now(UTC)
            response = await client.get("/version")
            latency = (datetime.now(UTC) - start).total_seconds() * 1000

            if response.status_code == 200:
                return AdapterHealth(
                    name=self.name,
                    healthy=True,
                    mode=self.mode,
                    latency_ms=latency,
                    last_check=self._last_health_check,
                )
            else:
                return AdapterHealth(
                    name=self.name,
                    healthy=False,
                    mode=self.mode,
                    latency_ms=latency,
                    last_check=self._last_health_check,
                    error=f"ArgoCD API returned {response.status_code}",
                )
        except httpx.HTTPError as e:
            logger.error(f"ArgoCD health check failed: {e}")
            return AdapterHealth(
                name=self.name,
                healthy=False,
                mode=self.mode,
                last_check=self._last_health_check,
                error=str(e),
            )

    def _parse_application(self, data: dict[str, Any]) -> Application:
        """Parse ArgoCD API application response to Application dataclass."""
        metadata = data.get("metadata", {})
        spec = data.get("spec", {})
        status = data.get("status", {})
        source = spec.get("source", {})
        destination = spec.get("destination", {})
        sync_status_data = status.get("sync", {})
        health_status_data = status.get("health", {})
        operation_state = status.get("operationState", {})

        # Parse resources
        resources = []
        for res in status.get("resources", []):
            resources.append(
                ResourceStatus(
                    group=res.get("group", ""),
                    kind=res.get("kind", ""),
                    name=res.get("name", ""),
                    namespace=res.get("namespace", ""),
                    status=self._map_sync_status(res.get("status")),
                    health=self._map_health_status(res.get("health", {}).get("status")),
                    message=res.get("health", {}).get("message"),
                )
            )

        # Parse last sync result
        last_sync = None
        sync_result = operation_state.get("syncResult", {})
        if sync_result:
            last_sync = SyncResult(
                revision=sync_result.get("revision", ""),
                started_at=self._parse_datetime(operation_state.get("startedAt")) or datetime.now(UTC),
                finished_at=self._parse_datetime(operation_state.get("finishedAt")),
                phase=self._map_operation_phase(operation_state.get("phase")),
                message=operation_state.get("message"),
                resources_synced=len(sync_result.get("resources", [])),
            )

        return Application(
            name=metadata.get("name", ""),
            namespace=metadata.get("namespace", "argocd"),
            project=spec.get("project", "default"),
            repo_url=source.get("repoURL", ""),
            target_revision=source.get("targetRevision", "HEAD"),
            path=source.get("path", ""),
            sync_status=self._map_sync_status(sync_status_data.get("status")),
            health_status=self._map_health_status(health_status_data.get("status")),
            created_at=self._parse_datetime(metadata.get("creationTimestamp")) or datetime.now(UTC),
            synced_at=self._parse_datetime(status.get("reconciledAt")),
            destination_server=destination.get("server", "https://kubernetes.default.svc"),
            destination_namespace=destination.get("namespace", "default"),
            auto_sync_enabled=spec.get("syncPolicy", {}).get("automated") is not None,
            resources=resources,
            last_sync_result=last_sync,
        )

    async def get_application(self, name: str) -> Application | None:
        """Get application details by name."""
        if self.is_mock():
            return self._mock_apps.get(name)

        try:
            client = await self._get_client()
            response = await client.get(f"/applications/{name}")

            if response.status_code == 404:
                return None
            response.raise_for_status()

            return self._parse_application(response.json())
        except httpx.HTTPError as e:
            logger.error(f"Failed to get application {name}: {e}")
            raise

    async def list_applications(
        self,
        project: str | None = None,
        health_status: HealthStatus | None = None,
        sync_status: SyncStatus | None = None,
    ) -> list[ApplicationSummary]:
        """List all applications with optional filtering."""
        if self.is_mock():
            apps = list(self._mock_apps.values())

            if project:
                apps = [a for a in apps if a.project == project]
            if health_status:
                apps = [a for a in apps if a.health_status == health_status]
            if sync_status:
                apps = [a for a in apps if a.sync_status == sync_status]

            return [
                ApplicationSummary(
                    name=a.name,
                    namespace=a.namespace,
                    sync_status=a.sync_status,
                    health_status=a.health_status,
                    synced_at=a.synced_at,
                )
                for a in apps
            ]

        try:
            client = await self._get_client()
            params: dict[str, str] = {}
            if project:
                params["project"] = project

            response = await client.get("/applications", params=params)
            response.raise_for_status()
            data = response.json()

            summaries = []
            for item in data.get("items", []):
                status = item.get("status", {})
                sync_data = status.get("sync", {})
                health_data = status.get("health", {})

                app_sync = self._map_sync_status(sync_data.get("status"))
                app_health = self._map_health_status(health_data.get("status"))

                # Apply filters
                if health_status and app_health != health_status:
                    continue
                if sync_status and app_sync != sync_status:
                    continue

                summaries.append(
                    ApplicationSummary(
                        name=item.get("metadata", {}).get("name", ""),
                        namespace=item.get("metadata", {}).get("namespace", "argocd"),
                        sync_status=app_sync,
                        health_status=app_health,
                        synced_at=self._parse_datetime(status.get("reconciledAt")),
                    )
                )

            return summaries
        except httpx.HTTPError as e:
            logger.error(f"Failed to list applications: {e}")
            raise

    async def sync_application(
        self,
        name: str,
        revision: str | None = None,
        prune: bool = False,
        dry_run: bool = False,
    ) -> SyncOperation:
        """Trigger a sync operation for an application."""
        if self.is_mock():
            app = self._mock_apps.get(name)
            if not app:
                raise ValueError(f"Application {name} not found")

            now = datetime.now(UTC)
            target_rev = revision or app.target_revision

            if dry_run:
                return SyncOperation(
                    app_name=name,
                    revision=target_rev,
                    phase=OperationPhase.SUCCEEDED,
                    started_at=now,
                    finished_at=now,
                    message="Dry run completed successfully",
                )

            # Simulate sync operation
            await asyncio.sleep(0.1)

            # Update application state
            app.sync_status = SyncStatus.SYNCED
            app.synced_at = now
            app.last_sync_result = SyncResult(
                revision=target_rev,
                started_at=now,
                finished_at=now,
                phase=OperationPhase.SUCCEEDED,
                resources_synced=len(app.resources),
            )

            return SyncOperation(
                app_name=name,
                revision=target_rev,
                phase=OperationPhase.SUCCEEDED,
                started_at=now,
                finished_at=now,
                message="Successfully synced",
            )

        try:
            client = await self._get_client()
            now = datetime.now(UTC)

            payload: dict[str, Any] = {
                "prune": prune,
                "dryRun": dry_run,
            }
            if revision:
                payload["revision"] = revision

            response = await client.post(f"/applications/{name}/sync", json=payload)
            response.raise_for_status()
            data = response.json()

            operation = data.get("status", {}).get("operationState", {})
            return SyncOperation(
                app_name=name,
                revision=revision or data.get("spec", {}).get("source", {}).get("targetRevision", "HEAD"),
                phase=self._map_operation_phase(operation.get("phase")),
                started_at=self._parse_datetime(operation.get("startedAt")) or now,
                finished_at=self._parse_datetime(operation.get("finishedAt")),
                message=operation.get("message"),
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to sync application {name}: {e}")
            raise

    async def get_application_resources(self, name: str) -> list[ResourceStatus]:
        """Get all resources for an application."""
        if self.is_mock():
            app = self._mock_apps.get(name)
            return app.resources if app else []

        try:
            client = await self._get_client()
            response = await client.get(f"/applications/{name}/resource-tree")
            response.raise_for_status()
            data = response.json()

            resources = []
            for node in data.get("nodes", []):
                resources.append(
                    ResourceStatus(
                        group=node.get("group", ""),
                        kind=node.get("kind", ""),
                        name=node.get("name", ""),
                        namespace=node.get("namespace", ""),
                        status=self._map_sync_status(node.get("status")),
                        health=self._map_health_status(node.get("health", {}).get("status")),
                        message=node.get("health", {}).get("message"),
                    )
                )
            return resources
        except httpx.HTTPError as e:
            logger.error(f"Failed to get resources for {name}: {e}")
            raise

    async def rollback_application(
        self,
        name: str,
        revision_id: int,
    ) -> SyncOperation:
        """Rollback an application to a previous revision."""
        if self.is_mock():
            app = self._mock_apps.get(name)
            if not app:
                raise ValueError(f"Application {name} not found")

            now = datetime.now(UTC)
            await asyncio.sleep(0.1)

            return SyncOperation(
                app_name=name,
                revision=f"rollback-{revision_id}",
                phase=OperationPhase.SUCCEEDED,
                started_at=now,
                finished_at=now,
                message=f"Rolled back to revision {revision_id}",
            )

        try:
            client = await self._get_client()
            now = datetime.now(UTC)

            response = await client.post(
                f"/applications/{name}/rollback",
                json={"id": revision_id},
            )
            response.raise_for_status()
            data = response.json()

            operation = data.get("status", {}).get("operationState", {})
            return SyncOperation(
                app_name=name,
                revision=f"rollback-{revision_id}",
                phase=self._map_operation_phase(operation.get("phase")),
                started_at=self._parse_datetime(operation.get("startedAt")) or now,
                finished_at=self._parse_datetime(operation.get("finishedAt")),
                message=operation.get("message") or f"Rolled back to revision {revision_id}",
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to rollback application {name}: {e}")
            raise

    async def get_sync_history(
        self,
        name: str,
        limit: int = 10,
    ) -> list[SyncResult]:
        """Get sync history for an application."""
        if self.is_mock():
            return self._generate_mock_sync_history(name, limit)

        try:
            client = await self._get_client()
            response = await client.get(f"/applications/{name}")
            response.raise_for_status()
            data = response.json()

            history = []
            for item in data.get("status", {}).get("history", [])[:limit]:
                history.append(
                    SyncResult(
                        revision=item.get("revision", ""),
                        started_at=self._parse_datetime(item.get("deployStartedAt")) or datetime.now(UTC),
                        finished_at=self._parse_datetime(item.get("deployedAt")),
                        phase=OperationPhase.SUCCEEDED,  # History only shows successful deployments
                        resources_synced=0,  # Not available in history
                    )
                )
            return history
        except httpx.HTTPError as e:
            logger.error(f"Failed to get sync history for {name}: {e}")
            raise

    async def create_application(
        self,
        name: str,
        repo_url: str,
        path: str,
        target_revision: str = "HEAD",
        destination_namespace: str = "default",
        project: str = "default",
        auto_sync: bool = True,
    ) -> Application:
        """Create a new ArgoCD application."""
        if self.is_mock():
            now = datetime.now(UTC)

            resources = self._generate_mock_resources(name, destination_namespace)

            app = Application(
                name=name,
                namespace="argocd",
                project=project,
                repo_url=repo_url,
                target_revision=target_revision,
                path=path,
                sync_status=SyncStatus.OUT_OF_SYNC,
                health_status=HealthStatus.MISSING,
                created_at=now,
                destination_namespace=destination_namespace,
                auto_sync_enabled=auto_sync,
                resources=resources,
            )

            self._mock_apps[name] = app
            return app

        try:
            client = await self._get_client()

            app_spec: dict[str, Any] = {
                "metadata": {
                    "name": name,
                },
                "spec": {
                    "project": project,
                    "source": {
                        "repoURL": repo_url,
                        "targetRevision": target_revision,
                        "path": path,
                    },
                    "destination": {
                        "server": "https://kubernetes.default.svc",
                        "namespace": destination_namespace,
                    },
                },
            }

            if auto_sync:
                app_spec["spec"]["syncPolicy"] = {
                    "automated": {
                        "prune": True,
                        "selfHeal": True,
                    },
                }

            response = await client.post("/applications", json=app_spec)
            response.raise_for_status()

            return self._parse_application(response.json())
        except httpx.HTTPError as e:
            logger.error(f"Failed to create application {name}: {e}")
            raise

    async def delete_application(
        self,
        name: str,
        cascade: bool = True,
    ) -> bool:
        """Delete an ArgoCD application."""
        if self.is_mock():
            if name in self._mock_apps:
                del self._mock_apps[name]
                return True
            return False

        try:
            client = await self._get_client()
            params = {"cascade": str(cascade).lower()}
            response = await client.delete(f"/applications/{name}", params=params)

            if response.status_code == 404:
                return False
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to delete application {name}: {e}")
            raise

    def _generate_mock_applications(self) -> dict[str, Application]:
        """Generate mock application data for demonstrations."""
        now = datetime.now(UTC)
        apps = {}

        mock_data = [
            {
                "name": "user-service",
                "project": "platform",
                "namespace": "production",
                "repo": "user-service",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.SYNCED,
                "age_days": 90,
            },
            {
                "name": "order-service",
                "project": "platform",
                "namespace": "production",
                "repo": "order-service",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.SYNCED,
                "age_days": 60,
            },
            {
                "name": "payment-gateway",
                "project": "platform",
                "namespace": "production",
                "repo": "payment-gateway",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.SYNCED,
                "age_days": 45,
            },
            {
                "name": "notification-service",
                "project": "platform",
                "namespace": "production",
                "repo": "notification-service",
                "health": HealthStatus.PROGRESSING,
                "sync": SyncStatus.OUT_OF_SYNC,
                "age_days": 30,
            },
            {
                "name": "analytics-pipeline",
                "project": "data",
                "namespace": "data-processing",
                "repo": "analytics-pipeline",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.SYNCED,
                "age_days": 25,
            },
            {
                "name": "ml-recommendation-engine",
                "project": "ml",
                "namespace": "ml-serving",
                "repo": "ml-recommendation-engine",
                "health": HealthStatus.DEGRADED,
                "sync": SyncStatus.SYNCED,
                "age_days": 15,
            },
            {
                "name": "inventory-tracker",
                "project": "platform",
                "namespace": "production",
                "repo": "inventory-tracker",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.SYNCED,
                "age_days": 100,
            },
            {
                "name": "api-gateway",
                "project": "infrastructure",
                "namespace": "production",
                "repo": "api-gateway",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.SYNCED,
                "age_days": 120,
            },
            {
                "name": "user-service-staging",
                "project": "platform",
                "namespace": "staging",
                "repo": "user-service",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.OUT_OF_SYNC,
                "age_days": 90,
            },
            {
                "name": "order-service-staging",
                "project": "platform",
                "namespace": "staging",
                "repo": "order-service",
                "health": HealthStatus.HEALTHY,
                "sync": SyncStatus.SYNCED,
                "age_days": 60,
            },
        ]

        for data in mock_data:
            created = now - timedelta(days=data["age_days"])
            synced = now - timedelta(hours=random.randint(1, 24))

            resources = self._generate_mock_resources(
                data["name"], data["namespace"]
            )

            last_sync = None
            if data["sync"] == SyncStatus.SYNCED:
                last_sync = SyncResult(
                    revision=f"abc{random.randint(1000, 9999)}",
                    started_at=synced - timedelta(seconds=random.randint(30, 120)),
                    finished_at=synced,
                    phase=OperationPhase.SUCCEEDED,
                    resources_synced=len(resources),
                )

            apps[data["name"]] = Application(
                name=data["name"],
                namespace="argocd",
                project=data["project"],
                repo_url=f"https://github.com/forge-org/{data['repo']}.git",
                target_revision="main",
                path="k8s/overlays/" + data["namespace"].split("-")[0],
                sync_status=data["sync"],
                health_status=data["health"],
                created_at=created,
                synced_at=synced if data["sync"] == SyncStatus.SYNCED else None,
                destination_namespace=data["namespace"],
                auto_sync_enabled=True,
                resources=resources,
                last_sync_result=last_sync,
            )

        return apps

    def _generate_mock_resources(
        self,
        app_name: str,
        namespace: str,
    ) -> list[ResourceStatus]:
        """Generate mock Kubernetes resources for an application."""
        base_name = app_name.replace("-staging", "").replace("-", "")

        resources = [
            ResourceStatus(
                group="apps",
                kind="Deployment",
                name=app_name,
                namespace=namespace,
                status=SyncStatus.SYNCED,
                health=HealthStatus.HEALTHY,
            ),
            ResourceStatus(
                group="",
                kind="Service",
                name=app_name,
                namespace=namespace,
                status=SyncStatus.SYNCED,
                health=HealthStatus.HEALTHY,
            ),
            ResourceStatus(
                group="",
                kind="ConfigMap",
                name=f"{app_name}-config",
                namespace=namespace,
                status=SyncStatus.SYNCED,
                health=None,
            ),
            ResourceStatus(
                group="",
                kind="Secret",
                name=f"{app_name}-secrets",
                namespace=namespace,
                status=SyncStatus.SYNCED,
                health=None,
            ),
            ResourceStatus(
                group="networking.k8s.io",
                kind="Ingress",
                name=app_name,
                namespace=namespace,
                status=SyncStatus.SYNCED,
                health=HealthStatus.HEALTHY,
            ),
            ResourceStatus(
                group="autoscaling",
                kind="HorizontalPodAutoscaler",
                name=app_name,
                namespace=namespace,
                status=SyncStatus.SYNCED,
                health=HealthStatus.HEALTHY,
            ),
        ]

        return resources

    def _generate_mock_sync_history(
        self,
        app_name: str,
        limit: int,
    ) -> list[SyncResult]:
        """Generate mock sync history."""
        now = datetime.now(UTC)
        history = []

        for i in range(limit):
            age_hours = i * random.randint(6, 24)
            started = now - timedelta(hours=age_hours)
            duration = random.randint(30, 180)

            # Most syncs succeed
            if random.random() > 0.9:
                phase = OperationPhase.FAILED
                message = "Sync failed: ImagePullBackOff"
            else:
                phase = OperationPhase.SUCCEEDED
                message = None

            history.append(
                SyncResult(
                    revision=f"rev{random.randint(1000, 9999)}",
                    started_at=started,
                    finished_at=started + timedelta(seconds=duration),
                    phase=phase,
                    message=message,
                    resources_synced=random.randint(4, 8),
                )
            )

        return history


# Singleton instance for the application
_argocd_adapter: ArgoCDAdapter | None = None


def get_argocd_adapter(
    mode: AdapterMode | None = None,
    server_url: str | None = None,
    token: str | None = None,
) -> ArgoCDAdapter:
    """Get or create the ArgoCD adapter instance.

    If no arguments are provided, uses settings from config.
    """
    global _argocd_adapter

    if _argocd_adapter is None:
        from app.core.config import settings

        # Use provided values or fall back to settings
        adapter_mode = mode
        if adapter_mode is None:
            adapter_mode = (
                AdapterMode.LIVE
                if settings.argocd_adapter_mode == "live"
                else AdapterMode.MOCK
            )

        _argocd_adapter = ArgoCDAdapter(
            mode=adapter_mode,
            server_url=server_url or settings.argocd_server,
            token=token or settings.argocd_token,
        )

    return _argocd_adapter


def reset_argocd_adapter() -> None:
    """Reset the ArgoCD adapter singleton (useful for testing)."""
    global _argocd_adapter
    _argocd_adapter = None
