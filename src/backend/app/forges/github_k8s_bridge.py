"""GitHub ↔ Kubernetes Bridge Forge.

This is the crown jewel of ForgeWorks - the Forge that bridges two tools
that fundamentally cannot communicate with each other natively.

THE PROBLEM:
- Kubernetes can run pods, scale deployments, monitor health
- GitHub can run workflows, build images, run tests
- BUT: Kubernetes can't ask GitHub "did the build pass?"
- AND: GitHub can't ask Kubernetes "is my deployment healthy?"

THE SOLUTION:
This Bridge Forge creates a bidirectional connection:

    ┌─────────────┐                           ┌─────────────┐
    │   GitHub    │                           │ Kubernetes  │
    │   Actions   │                           │   Cluster   │
    └──────┬──────┘                           └──────┬──────┘
           │                                         │
           │ Workflow Completed                      │ Pod Status
           │ Build Success/Failure                   │ Deployment Health
           │ Image Tag                               │ Rollout Status
           │                                         │
           ▼                                         ▼
    ┌──────────────────────────────────────────────────────┐
    │              GitHub ↔ Kubernetes Bridge              │
    │                                                      │
    │  ┌────────────────────────────────────────────────┐  │
    │  │             Correlation Engine                 │  │
    │  │  • Build ID → Deployment → Pod                 │  │
    │  │  • Image SHA → Running Container               │  │
    │  │  • PR Number → Feature Branch Deployment       │  │
    │  └────────────────────────────────────────────────┘  │
    │                                                      │
    │  ┌────────────────────────────────────────────────┐  │
    │  │             Report Generator                   │  │
    │  │  • Build Status Report (for K8s)               │  │
    │  │  • Deployment Health Report (for GitHub)       │  │
    │  │  • End-to-End Pipeline Report                  │  │
    │  └────────────────────────────────────────────────┘  │
    │                                                      │
    │  ┌────────────────────────────────────────────────┐  │
    │  │             Action Triggers                    │  │
    │  │  • Build passes → Trigger K8s deployment       │  │
    │  │  • Pod crashes → Re-trigger GitHub build       │  │
    │  │  • Health degrades → GitHub issue created      │  │
    │  └────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────┘
           │                                         │
           ▼                                         ▼
    ┌─────────────┐                           ┌─────────────┐
    │  Dashboard  │                           │   Alerts    │
    │  Real-time  │                           │  Anomalies  │
    └─────────────┘                           └─────────────┘

EXAMPLE USE CASE (from user's vision):
"If Kubernetes can't natively access GitHub Runners and generate
its own reports, ForgeWorks can create a template that makes it happen."

This Forge makes it happen by:
1. Listening to GitHub workflow completions
2. Correlating builds with Kubernetes deployments
3. Generating reports that Kubernetes can "read" through ForgeWorks
4. Triggering actions when states don't match expectations
"""

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from app.core.events import (
    broadcast_anomaly_detected,
    broadcast_deployment_scaled,
    broadcast_pipeline_completed,
    broadcast_service_status_changed,
)
from app.forges.base import (
    ForgeAdapter,
    ForgeConfig,
    ReconciliationStrategy,
    StateDiff,
    WebhookPayload,
)


class BuildToDeploymentStatus(str, Enum):
    """Status of the build-to-deployment pipeline."""

    BUILDING = "building"
    BUILD_PASSED = "build_passed"
    BUILD_FAILED = "build_failed"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    DEPLOYMENT_FAILED = "deployment_failed"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class BuildDeploymentCorrelation:
    """Links a GitHub build to a Kubernetes deployment.

    This is THE KEY DATA STRUCTURE that bridges the gap.
    It answers questions neither tool can answer alone:
    - "Which build is currently running in production?"
    - "Is the deployment healthy since the last build?"
    - "How long from PR merge to healthy deployment?"
    """

    # Build Information (from GitHub)
    build_id: str
    workflow_name: str
    repo: str
    branch: str
    commit_sha: str
    image_tag: str | None = None
    build_status: str = "pending"  # pending, success, failure
    build_started_at: datetime | None = None
    build_completed_at: datetime | None = None

    # Deployment Information (from Kubernetes)
    deployment_name: str | None = None
    namespace: str = "default"
    deployment_status: str = "pending"  # pending, progressing, available, failed
    current_replicas: int = 0
    desired_replicas: int = 1
    pod_statuses: list[str] = field(default_factory=list)  # Running, CrashLoopBackOff, etc.
    deployment_started_at: datetime | None = None
    deployment_completed_at: datetime | None = None

    # End-to-End Status (THE BRIDGE)
    pipeline_status: BuildToDeploymentStatus = BuildToDeploymentStatus.UNKNOWN
    end_to_end_duration_seconds: float | None = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    def compute_status(self) -> BuildToDeploymentStatus:
        """Compute the overall pipeline status based on both tools' states."""
        if self.build_status == "pending":
            return BuildToDeploymentStatus.BUILDING
        if self.build_status == "failure":
            return BuildToDeploymentStatus.BUILD_FAILED
        if self.build_status == "success":
            if self.deployment_status == "pending":
                return BuildToDeploymentStatus.BUILD_PASSED
            if self.deployment_status == "progressing":
                return BuildToDeploymentStatus.DEPLOYING
            if self.deployment_status == "failed":
                return BuildToDeploymentStatus.DEPLOYMENT_FAILED
            if self.deployment_status == "available":
                # Check pod health
                if all(s == "Running" for s in self.pod_statuses):
                    return BuildToDeploymentStatus.HEALTHY
                return BuildToDeploymentStatus.DEGRADED
        return BuildToDeploymentStatus.UNKNOWN

    def compute_duration(self) -> float | None:
        """Compute end-to-end duration from build start to deployment healthy."""
        if self.build_started_at and self.deployment_completed_at:
            return (self.deployment_completed_at - self.build_started_at).total_seconds()
        return None

    def to_report(self) -> dict[str, Any]:
        """Generate a report that Kubernetes can 'understand' through ForgeWorks.

        This is the report that fills the gap - Kubernetes can't generate
        this natively, but ForgeWorks can because it bridges both worlds.
        """
        return {
            "correlation_id": f"{self.repo}/{self.build_id}",
            "status": self.compute_status().value,
            # Build Context (from GitHub)
            "build": {
                "id": self.build_id,
                "workflow": self.workflow_name,
                "repo": self.repo,
                "branch": self.branch,
                "commit": self.commit_sha,
                "image_tag": self.image_tag,
                "status": self.build_status,
                "started_at": self.build_started_at.isoformat() if self.build_started_at else None,
                "completed_at": self.build_completed_at.isoformat()
                if self.build_completed_at
                else None,
            },
            # Deployment Context (from Kubernetes)
            "deployment": {
                "name": self.deployment_name,
                "namespace": self.namespace,
                "status": self.deployment_status,
                "replicas": f"{self.current_replicas}/{self.desired_replicas}",
                "pod_statuses": self.pod_statuses,
                "started_at": self.deployment_started_at.isoformat()
                if self.deployment_started_at
                else None,
                "completed_at": self.deployment_completed_at.isoformat()
                if self.deployment_completed_at
                else None,
            },
            # End-to-End Metrics (THE VALUE ADD)
            "metrics": {
                "end_to_end_duration_seconds": self.compute_duration(),
                "build_to_deploy_lag_seconds": (
                    (self.deployment_started_at - self.build_completed_at).total_seconds()
                    if self.build_completed_at and self.deployment_started_at
                    else None
                ),
                "last_updated": self.last_updated.isoformat(),
            },
        }


class GitHubKubernetesBridge(ForgeAdapter):
    """The Bridge Forge that connects GitHub and Kubernetes.

    This forge:
    1. Listens to GitHub workflow events
    2. Listens to Kubernetes deployment events
    3. Correlates them to create end-to-end visibility
    4. Generates reports that neither tool can produce alone
    5. Triggers actions based on combined state
    """

    def __init__(
        self,
        config: ForgeConfig | None = None,
        github_org: str = "forge-works",
        default_namespace: str = "default",
    ) -> None:
        """Initialize the GitHub ↔ Kubernetes Bridge.

        Args:
            config: Forge configuration
            github_org: GitHub organization
            default_namespace: Default Kubernetes namespace
        """
        super().__init__(
            config
            or ForgeConfig(
                reconciliation_strategy=ReconciliationStrategy.MERGE,
                reconcile_interval_seconds=30,
            )
        )
        self.github_org = github_org
        self.default_namespace = default_namespace

        # THE CORRELATION ENGINE - the heart of the bridge
        self._correlations: dict[str, BuildDeploymentCorrelation] = {}

        # Mappings for lookup
        self._repo_to_deployment: dict[str, str] = {}  # repo → deployment name
        self._image_to_correlation: dict[str, str] = {}  # image:tag → correlation_id
        self._build_to_correlation: dict[str, str] = {}  # build_id → correlation_id

    @property
    def forge_name(self) -> str:
        return "github-kubernetes-bridge"

    @property
    def supported_webhook_events(self) -> list[str]:
        return [
            # GitHub Events
            "workflow_run.completed",
            "workflow_run.in_progress",
            "push",
            # Kubernetes Events (via admission webhook or watch API)
            "deployment.progressing",
            "deployment.available",
            "deployment.failed",
            "pod.running",
            "pod.failed",
            "pod.crashloop",
        ]

    # =========================================================================
    # Configuration - Setting Up the Bridge
    # =========================================================================

    def register_repo_deployment_mapping(
        self,
        repo_name: str,
        deployment_name: str,
        namespace: str | None = None,
    ) -> None:
        """Register which GitHub repo corresponds to which K8s deployment.

        This is the configuration that enables the bridge.

        Args:
            repo_name: GitHub repository name
            deployment_name: Kubernetes deployment name
            namespace: Kubernetes namespace (optional, uses default)
        """
        key = f"{namespace or self.default_namespace}/{deployment_name}"
        self._repo_to_deployment[repo_name] = key

    def get_deployment_for_repo(self, repo_name: str) -> tuple[str, str] | None:
        """Get the Kubernetes deployment for a GitHub repo.

        Returns (namespace, deployment_name) tuple or None.
        """
        key = self._repo_to_deployment.get(repo_name)
        if key:
            parts = key.split("/", 1)
            return (parts[0], parts[1]) if len(parts) == 2 else (self.default_namespace, parts[0])
        return None

    # =========================================================================
    # Webhook Event Handlers
    # =========================================================================

    async def handle_webhook_event(self, payload: WebhookPayload) -> None:
        """Route webhook to appropriate handler."""
        handlers = {
            # GitHub events
            "workflow_run.completed": self._handle_build_completed,
            "workflow_run.in_progress": self._handle_build_started,
            "push": self._handle_push,
            # Kubernetes events
            "deployment.progressing": self._handle_deployment_progressing,
            "deployment.available": self._handle_deployment_available,
            "deployment.failed": self._handle_deployment_failed,
            "pod.running": self._handle_pod_running,
            "pod.failed": self._handle_pod_failed,
            "pod.crashloop": self._handle_pod_crashloop,
        }

        handler = handlers.get(payload.event_type)
        if handler:
            await handler(payload)

    # =========================================================================
    # GitHub Event Handlers
    # =========================================================================

    async def _handle_build_started(self, payload: WebhookPayload) -> None:
        """Handle GitHub workflow started - create correlation entry."""
        workflow = payload.raw_payload.get("workflow_run", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")

        build_id = str(workflow.get("id"))
        correlation_id = f"{repo}/{build_id}"

        # Get the deployment this repo maps to
        deployment_info = self.get_deployment_for_repo(repo)

        correlation = BuildDeploymentCorrelation(
            build_id=build_id,
            workflow_name=workflow.get("name", ""),
            repo=repo,
            branch=workflow.get("head_branch", "main"),
            commit_sha=workflow.get("head_sha", ""),
            build_status="pending",
            build_started_at=datetime.now(UTC),
            deployment_name=deployment_info[1] if deployment_info else None,
            namespace=deployment_info[0] if deployment_info else self.default_namespace,
        )

        self._correlations[correlation_id] = correlation
        self._build_to_correlation[build_id] = correlation_id

        # Broadcast that a build is starting
        await broadcast_service_status_changed(
            service_id=correlation_id,
            old_status="stable",
            new_status="building",
        )

    async def _handle_build_completed(self, payload: WebhookPayload) -> None:
        """Handle GitHub workflow completed - THE KEY BRIDGE EVENT.

        When a build completes, we:
        1. Update the correlation with build results
        2. Extract the image tag if available
        3. Prepare for deployment tracking
        4. Generate a report for Kubernetes
        """
        workflow = payload.raw_payload.get("workflow_run", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")
        conclusion = workflow.get("conclusion", "unknown")

        build_id = str(workflow.get("id"))
        correlation_id = self._build_to_correlation.get(build_id)

        if correlation_id and correlation_id in self._correlations:
            correlation = self._correlations[correlation_id]
            correlation.build_status = conclusion
            correlation.build_completed_at = datetime.now(UTC)
            correlation.last_updated = datetime.now(UTC)

            # Try to extract image tag from workflow outputs
            # In real implementation, this would parse workflow artifacts
            correlation.image_tag = f"{repo}:{correlation.commit_sha[:7]}"

            if correlation.image_tag:
                self._image_to_correlation[correlation.image_tag] = correlation_id

            correlation.pipeline_status = correlation.compute_status()

            # Broadcast based on build result
            if conclusion == "success":
                await broadcast_pipeline_completed(
                    pipeline_id=build_id,
                    status="success",
                    duration_seconds=(
                        datetime.now(UTC) - correlation.build_started_at
                    ).total_seconds()
                    if correlation.build_started_at
                    else None,
                )

                await broadcast_service_status_changed(
                    service_id=correlation_id,
                    old_status="building",
                    new_status="ready_to_deploy",
                )

                # Generate the report that Kubernetes can "read"
                correlation.to_report()
                # This report would be stored and accessible via API
                # Kubernetes-related tools can query ForgeWorks to get build status

            else:
                await broadcast_anomaly_detected(
                    {
                        "type": "build_to_deployment_failure",
                        "severity": "high",
                        "source": self.forge_name,
                        "title": f"Build failed for {repo}",
                        "description": (
                            f"GitHub workflow '{correlation.workflow_name}' failed. "
                            f"Deployment {correlation.deployment_name} will not be updated."
                        ),
                        "correlation": correlation.to_report(),
                    }
                )

    async def _handle_push(self, payload: WebhookPayload) -> None:
        """Handle push to main branch - track for correlation."""
        ref = payload.raw_payload.get("ref", "")
        if ref not in ("refs/heads/main", "refs/heads/master"):
            return

        payload.raw_payload.get("repository", {}).get("name", "")
        commits = payload.raw_payload.get("commits", [])

        if commits:
            commits[-1].get("id", "")
            # This push will trigger a workflow, correlation created then

    # =========================================================================
    # Kubernetes Event Handlers
    # =========================================================================

    async def _handle_deployment_progressing(self, payload: WebhookPayload) -> None:
        """Handle Kubernetes deployment progressing.

        Bridge: Connect deployment to the build that triggered it.
        """
        deployment = payload.raw_payload.get("deployment", {})
        deployment_name = deployment.get("name", "")
        namespace = deployment.get("namespace", self.default_namespace)

        # Find correlation by image tag or deployment name
        correlation = self._find_correlation_for_deployment(deployment_name, namespace)

        if correlation:
            correlation.deployment_status = "progressing"
            correlation.deployment_started_at = datetime.now(UTC)
            correlation.pipeline_status = correlation.compute_status()
            correlation.last_updated = datetime.now(UTC)

            await broadcast_service_status_changed(
                service_id=f"{correlation.repo}/{correlation.build_id}",
                old_status="ready_to_deploy",
                new_status="deploying",
            )

    async def _handle_deployment_available(self, payload: WebhookPayload) -> None:
        """Handle Kubernetes deployment available (healthy).

        Bridge: Complete the build→deploy→healthy cycle.
        """
        deployment = payload.raw_payload.get("deployment", {})
        deployment_name = deployment.get("name", "")
        namespace = deployment.get("namespace", self.default_namespace)
        replicas = deployment.get("ready_replicas", 1)

        correlation = self._find_correlation_for_deployment(deployment_name, namespace)

        if correlation:
            correlation.deployment_status = "available"
            correlation.current_replicas = replicas
            correlation.deployment_completed_at = datetime.now(UTC)
            correlation.pipeline_status = correlation.compute_status()
            correlation.end_to_end_duration_seconds = correlation.compute_duration()
            correlation.last_updated = datetime.now(UTC)

            await broadcast_service_status_changed(
                service_id=f"{correlation.repo}/{correlation.build_id}",
                old_status="deploying",
                new_status="healthy",
            )

            await broadcast_deployment_scaled(
                deployment_name=deployment_name,
                replicas=replicas,
                namespace=namespace,
            )

            # Generate the COMPLETE end-to-end report
            # This is what Kubernetes could never generate on its own
            correlation.to_report()
            # Log or store for API access

    async def _handle_deployment_failed(self, payload: WebhookPayload) -> None:
        """Handle Kubernetes deployment failed.

        Bridge: Create anomaly linking build to failed deployment.
        """
        deployment = payload.raw_payload.get("deployment", {})
        deployment_name = deployment.get("name", "")
        namespace = deployment.get("namespace", self.default_namespace)
        message = deployment.get("message", "Unknown error")

        correlation = self._find_correlation_for_deployment(deployment_name, namespace)

        if correlation:
            correlation.deployment_status = "failed"
            correlation.pipeline_status = correlation.compute_status()
            correlation.last_updated = datetime.now(UTC)

            # THE KEY VALUE: Anomaly links build to deployment failure
            await broadcast_anomaly_detected(
                {
                    "type": "deployment_failed_after_build",
                    "severity": "critical",
                    "source": self.forge_name,
                    "title": f"Deployment {deployment_name} failed",
                    "description": (
                        f"Build {correlation.build_id} succeeded but deployment failed: {message}"
                    ),
                    "correlation": correlation.to_report(),
                    "suggested_action": "Check Kubernetes events and pod logs",
                }
            )

    async def _handle_pod_running(self, payload: WebhookPayload) -> None:
        """Handle pod running - track for health monitoring."""
        pod = payload.raw_payload.get("pod", {})
        deployment_name = pod.get("labels", {}).get("app", "")
        namespace = pod.get("namespace", self.default_namespace)

        correlation = self._find_correlation_for_deployment(deployment_name, namespace)
        if correlation and "Running" not in correlation.pod_statuses:
            correlation.pod_statuses.append("Running")
            correlation.pipeline_status = correlation.compute_status()
            correlation.last_updated = datetime.now(UTC)

    async def _handle_pod_failed(self, payload: WebhookPayload) -> None:
        """Handle pod failed - link to build for root cause."""
        pod = payload.raw_payload.get("pod", {})
        deployment_name = pod.get("labels", {}).get("app", "")
        namespace = pod.get("namespace", self.default_namespace)

        correlation = self._find_correlation_for_deployment(deployment_name, namespace)
        if correlation:
            correlation.pod_statuses = ["Failed"]
            correlation.pipeline_status = BuildToDeploymentStatus.DEGRADED
            correlation.last_updated = datetime.now(UTC)

            await broadcast_anomaly_detected(
                {
                    "type": "pod_failure_linked_to_build",
                    "severity": "high",
                    "source": self.forge_name,
                    "title": f"Pod failed in {deployment_name}",
                    "description": (
                        f"Pod failure may be related to build {correlation.build_id} "
                        f"(commit {correlation.commit_sha[:7]})"
                    ),
                    "correlation": correlation.to_report(),
                }
            )

    async def _handle_pod_crashloop(self, payload: WebhookPayload) -> None:
        """Handle pod CrashLoopBackOff - critical anomaly with build context."""
        pod = payload.raw_payload.get("pod", {})
        deployment_name = pod.get("labels", {}).get("app", "")
        namespace = pod.get("namespace", self.default_namespace)

        correlation = self._find_correlation_for_deployment(deployment_name, namespace)
        if correlation:
            correlation.pod_statuses = ["CrashLoopBackOff"]
            correlation.pipeline_status = BuildToDeploymentStatus.DEGRADED
            correlation.last_updated = datetime.now(UTC)

            await broadcast_anomaly_detected(
                {
                    "type": "crashloop_with_build_context",
                    "severity": "critical",
                    "source": self.forge_name,
                    "title": f"CrashLoopBackOff: {deployment_name}",
                    "description": (
                        f"Pod is crash-looping. Last successful build: {correlation.build_id}. "
                        f"Consider rolling back to previous image."
                    ),
                    "correlation": correlation.to_report(),
                    "suggested_action": "Check logs, consider rollback",
                    "rollback_to": correlation.image_tag,
                }
            )

    # =========================================================================
    # Correlation Engine
    # =========================================================================

    def _find_correlation_for_deployment(
        self,
        deployment_name: str,
        namespace: str,
    ) -> BuildDeploymentCorrelation | None:
        """Find the build correlation for a Kubernetes deployment."""
        # First, try to find by deployment name
        for correlation in self._correlations.values():
            if (
                correlation.deployment_name == deployment_name
                and correlation.namespace == namespace
            ):
                return correlation

        # If not found, try to match by repo→deployment mapping
        for repo, key in self._repo_to_deployment.items():
            if key == f"{namespace}/{deployment_name}":
                # Find the most recent correlation for this repo
                for correlation in sorted(
                    self._correlations.values(),
                    key=lambda c: c.build_started_at or datetime.min,
                    reverse=True,
                ):
                    if correlation.repo == repo:
                        correlation.deployment_name = deployment_name
                        correlation.namespace = namespace
                        return correlation

        return None

    def get_correlation(self, correlation_id: str) -> BuildDeploymentCorrelation | None:
        """Get a specific correlation by ID."""
        return self._correlations.get(correlation_id)

    def get_all_correlations(self) -> list[dict[str, Any]]:
        """Get all correlations as reports."""
        return [c.to_report() for c in self._correlations.values()]

    def get_active_correlations(self) -> list[dict[str, Any]]:
        """Get correlations that are still in progress."""
        return [
            c.to_report()
            for c in self._correlations.values()
            if c.pipeline_status
            not in (
                BuildToDeploymentStatus.HEALTHY,
                BuildToDeploymentStatus.BUILD_FAILED,
                BuildToDeploymentStatus.DEPLOYMENT_FAILED,
            )
        ]

    # =========================================================================
    # State Management (ForgeAdapter interface)
    # =========================================================================

    async def fetch_external_state(self) -> dict[str, Any]:
        """Fetch combined state from GitHub and Kubernetes.

        In live mode, this would query both APIs.
        """
        return {
            "correlations": {cid: c.to_report() for cid, c in self._correlations.items()},
            "mappings": dict(self._repo_to_deployment),
        }

    async def get_local_state(self) -> dict[str, Any]:
        """Get local ForgeWorks state."""
        return {
            "correlations": {cid: c.to_report() for cid, c in self._correlations.items()},
        }

    async def apply_external_state(self, diff: StateDiff) -> bool:
        """Apply external state updates."""
        # Correlations are updated through events, not reconciliation
        return True

    async def push_local_state(self, diff: StateDiff) -> bool:
        """Push local state to external tools (rarely needed)."""
        return True

    # =========================================================================
    # Mock Event Generation
    # =========================================================================

    async def generate_mock_events(self) -> list[WebhookPayload]:
        """Generate realistic mock events simulating build→deploy cycle."""
        events: list[WebhookPayload] = []

        repos = list(self._repo_to_deployment.keys()) or ["user-service", "api-gateway"]
        repo = random.choice(repos)
        build_id = str(random.randint(1000000, 9999999))

        # 30% chance to generate a full build→deploy cycle
        if random.random() < 0.3:
            # Workflow started
            events.append(
                WebhookPayload(
                    source="github",
                    event_type="workflow_run.in_progress",
                    timestamp=datetime.now(UTC),
                    raw_payload={
                        "workflow_run": {
                            "id": build_id,
                            "name": "CI/CD Pipeline",
                            "head_branch": "main",
                            "head_sha": f"abc{random.randint(1000, 9999)}",
                        },
                        "repository": {"name": repo},
                    },
                )
            )

            # Workflow completed (85% success rate)
            conclusion = "success" if random.random() < 0.85 else "failure"
            events.append(
                WebhookPayload(
                    source="github",
                    event_type="workflow_run.completed",
                    timestamp=datetime.now(UTC) + timedelta(seconds=5),
                    raw_payload={
                        "workflow_run": {
                            "id": build_id,
                            "name": "CI/CD Pipeline",
                            "head_branch": "main",
                            "head_sha": f"abc{random.randint(1000, 9999)}",
                            "conclusion": conclusion,
                        },
                        "repository": {"name": repo},
                    },
                )
            )

            if conclusion == "success":
                deployment_info = self.get_deployment_for_repo(repo)
                if deployment_info:
                    namespace, deployment_name = deployment_info

                    # Deployment progressing
                    events.append(
                        WebhookPayload(
                            source="kubernetes",
                            event_type="deployment.progressing",
                            timestamp=datetime.now(UTC) + timedelta(seconds=10),
                            raw_payload={
                                "deployment": {
                                    "name": deployment_name,
                                    "namespace": namespace,
                                },
                            },
                        )
                    )

                    # 90% deployment success rate
                    if random.random() < 0.9:
                        events.append(
                            WebhookPayload(
                                source="kubernetes",
                                event_type="deployment.available",
                                timestamp=datetime.now(UTC) + timedelta(seconds=30),
                                raw_payload={
                                    "deployment": {
                                        "name": deployment_name,
                                        "namespace": namespace,
                                        "ready_replicas": 3,
                                    },
                                },
                            )
                        )
                    else:
                        events.append(
                            WebhookPayload(
                                source="kubernetes",
                                event_type="deployment.failed",
                                timestamp=datetime.now(UTC) + timedelta(seconds=30),
                                raw_payload={
                                    "deployment": {
                                        "name": deployment_name,
                                        "namespace": namespace,
                                        "message": "ImagePullBackOff",
                                    },
                                },
                            )
                        )

        return events


# Singleton instance
_bridge: GitHubKubernetesBridge | None = None


def get_github_kubernetes_bridge(
    config: ForgeConfig | None = None,
) -> GitHubKubernetesBridge:
    """Get or create the GitHub ↔ Kubernetes Bridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = GitHubKubernetesBridge(config)

        # Register some default repo→deployment mappings
        _bridge.register_repo_deployment_mapping("user-service", "user-service", "production")
        _bridge.register_repo_deployment_mapping("api-gateway", "api-gateway", "production")
        _bridge.register_repo_deployment_mapping("order-service", "order-service", "production")

    return _bridge
