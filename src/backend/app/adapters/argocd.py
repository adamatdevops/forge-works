"""ArgoCD adapter for GitOps deployment management."""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from app.adapters.base import AdapterHealth, AdapterMode, BaseAdapter


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
    ) -> None:
        """Initialize ArgoCD adapter."""
        super().__init__(mode)
        self.server_url = server_url or "https://argocd.forge.internal"
        self.token = token
        self._mock_apps = self._generate_mock_applications()

    @property
    def name(self) -> str:
        """Return adapter name."""
        return "argocd"

    async def health_check(self) -> AdapterHealth:
        """Check ArgoCD API connectivity."""
        self._last_health_check = datetime.now(timezone.utc)

        if self.is_mock():
            await asyncio.sleep(0.015)
            return AdapterHealth(
                name=self.name,
                healthy=True,
                mode=self.mode,
                latency_ms=15.2,
                last_check=self._last_health_check,
            )

        # Live mode - would make actual API call
        return AdapterHealth(
            name=self.name,
            healthy=False,
            mode=self.mode,
            last_check=self._last_health_check,
            error="Live mode not yet implemented",
        )

    async def get_application(self, name: str) -> Application | None:
        """Get application details by name."""
        if self.is_mock():
            return self._mock_apps.get(name)

        raise NotImplementedError("Live mode not yet implemented")

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

        raise NotImplementedError("Live mode not yet implemented")

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

            now = datetime.now(timezone.utc)
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

        raise NotImplementedError("Live mode not yet implemented")

    async def get_application_resources(self, name: str) -> list[ResourceStatus]:
        """Get all resources for an application."""
        if self.is_mock():
            app = self._mock_apps.get(name)
            return app.resources if app else []

        raise NotImplementedError("Live mode not yet implemented")

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

            now = datetime.now(timezone.utc)
            await asyncio.sleep(0.1)

            return SyncOperation(
                app_name=name,
                revision=f"rollback-{revision_id}",
                phase=OperationPhase.SUCCEEDED,
                started_at=now,
                finished_at=now,
                message=f"Rolled back to revision {revision_id}",
            )

        raise NotImplementedError("Live mode not yet implemented")

    async def get_sync_history(
        self,
        name: str,
        limit: int = 10,
    ) -> list[SyncResult]:
        """Get sync history for an application."""
        if self.is_mock():
            return self._generate_mock_sync_history(name, limit)

        raise NotImplementedError("Live mode not yet implemented")

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
            now = datetime.now(timezone.utc)

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

        raise NotImplementedError("Live mode not yet implemented")

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

        raise NotImplementedError("Live mode not yet implemented")

    def _generate_mock_applications(self) -> dict[str, Application]:
        """Generate mock application data for demonstrations."""
        now = datetime.now(timezone.utc)
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
        now = datetime.now(timezone.utc)
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
    mode: AdapterMode = AdapterMode.MOCK,
    server_url: str | None = None,
    token: str | None = None,
) -> ArgoCDAdapter:
    """Get or create the ArgoCD adapter instance."""
    global _argocd_adapter
    if _argocd_adapter is None:
        _argocd_adapter = ArgoCDAdapter(mode=mode, server_url=server_url, token=token)
    return _argocd_adapter
