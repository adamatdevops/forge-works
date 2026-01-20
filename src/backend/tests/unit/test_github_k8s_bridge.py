"""Unit tests for GitHub ↔ Kubernetes Bridge Forge."""

from datetime import datetime, timedelta

import pytest

from app.forges.base import ForgeConfig, ForgeMode, WebhookPayload
from app.forges.github_k8s_bridge import (
    BuildDeploymentCorrelation,
    BuildToDeploymentStatus,
    GitHubKubernetesBridge,
    get_github_kubernetes_bridge,
)


class TestBuildToDeploymentStatus:
    """Tests for BuildToDeploymentStatus enum."""

    def test_all_statuses_exist(self):
        """Test all expected statuses exist."""
        assert BuildToDeploymentStatus.BUILDING == "building"
        assert BuildToDeploymentStatus.BUILD_PASSED == "build_passed"
        assert BuildToDeploymentStatus.BUILD_FAILED == "build_failed"
        assert BuildToDeploymentStatus.DEPLOYING == "deploying"
        assert BuildToDeploymentStatus.DEPLOYED == "deployed"
        assert BuildToDeploymentStatus.DEPLOYMENT_FAILED == "deployment_failed"
        assert BuildToDeploymentStatus.HEALTHY == "healthy"
        assert BuildToDeploymentStatus.DEGRADED == "degraded"
        assert BuildToDeploymentStatus.UNKNOWN == "unknown"


class TestBuildDeploymentCorrelation:
    """Tests for BuildDeploymentCorrelation dataclass."""

    def test_correlation_defaults(self):
        """Test default correlation values."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
        )

        assert correlation.build_status == "pending"
        assert correlation.deployment_status == "pending"
        assert correlation.namespace == "default"
        assert correlation.current_replicas == 0
        assert correlation.desired_replicas == 1
        assert correlation.pod_statuses == []
        assert correlation.pipeline_status == BuildToDeploymentStatus.UNKNOWN

    def test_compute_status_building(self):
        """Test status computation when building."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="pending",
        )

        assert correlation.compute_status() == BuildToDeploymentStatus.BUILDING

    def test_compute_status_build_failed(self):
        """Test status computation when build failed."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="failure",
        )

        assert correlation.compute_status() == BuildToDeploymentStatus.BUILD_FAILED

    def test_compute_status_build_passed(self):
        """Test status computation when build passed but not deployed."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="success",
            deployment_status="pending",
        )

        assert correlation.compute_status() == BuildToDeploymentStatus.BUILD_PASSED

    def test_compute_status_deploying(self):
        """Test status computation when deploying."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="success",
            deployment_status="progressing",
        )

        assert correlation.compute_status() == BuildToDeploymentStatus.DEPLOYING

    def test_compute_status_deployment_failed(self):
        """Test status computation when deployment failed."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="success",
            deployment_status="failed",
        )

        assert correlation.compute_status() == BuildToDeploymentStatus.DEPLOYMENT_FAILED

    def test_compute_status_healthy(self):
        """Test status computation when deployment is healthy."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="success",
            deployment_status="available",
            pod_statuses=["Running", "Running", "Running"],
        )

        assert correlation.compute_status() == BuildToDeploymentStatus.HEALTHY

    def test_compute_status_degraded(self):
        """Test status computation when pods are not all running."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="success",
            deployment_status="available",
            pod_statuses=["Running", "CrashLoopBackOff"],
        )

        assert correlation.compute_status() == BuildToDeploymentStatus.DEGRADED

    def test_compute_duration_complete(self):
        """Test duration computation with complete lifecycle."""
        start = datetime.utcnow() - timedelta(minutes=5)
        end = datetime.utcnow()

        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_started_at=start,
            deployment_completed_at=end,
        )

        duration = correlation.compute_duration()
        assert duration is not None
        assert 299 < duration < 301  # ~5 minutes

    def test_compute_duration_incomplete(self):
        """Test duration computation with incomplete lifecycle."""
        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_started_at=datetime.utcnow(),
        )

        assert correlation.compute_duration() is None

    def test_to_report(self):
        """Test report generation."""
        start = datetime.utcnow() - timedelta(minutes=5)
        build_end = datetime.utcnow() - timedelta(minutes=3)
        deploy_start = datetime.utcnow() - timedelta(minutes=2)
        deploy_end = datetime.utcnow()

        correlation = BuildDeploymentCorrelation(
            build_id="123",
            workflow_name="CI/CD Pipeline",
            repo="user-service",
            branch="main",
            commit_sha="abc123def",
            image_tag="user-service:abc123d",
            build_status="success",
            build_started_at=start,
            build_completed_at=build_end,
            deployment_name="user-service",
            namespace="production",
            deployment_status="available",
            current_replicas=3,
            desired_replicas=3,
            pod_statuses=["Running", "Running", "Running"],
            deployment_started_at=deploy_start,
            deployment_completed_at=deploy_end,
        )

        report = correlation.to_report()

        assert report["correlation_id"] == "user-service/123"
        assert report["status"] == "healthy"
        assert report["build"]["id"] == "123"
        assert report["build"]["workflow"] == "CI/CD Pipeline"
        assert report["build"]["repo"] == "user-service"
        assert report["build"]["status"] == "success"
        assert report["deployment"]["name"] == "user-service"
        assert report["deployment"]["namespace"] == "production"
        assert report["deployment"]["replicas"] == "3/3"
        assert report["metrics"]["end_to_end_duration_seconds"] is not None


class TestGitHubKubernetesBridge:
    """Tests for GitHubKubernetesBridge."""

    @pytest.fixture
    def bridge(self) -> GitHubKubernetesBridge:
        """Create a fresh bridge for each test."""
        config = ForgeConfig(mode=ForgeMode.MOCK)
        return GitHubKubernetesBridge(
            config=config,
            github_org="test-org",
            default_namespace="production",
        )

    def test_forge_name(self, bridge: GitHubKubernetesBridge):
        """Test forge name property."""
        assert bridge.forge_name == "github-kubernetes-bridge"

    def test_supported_webhook_events(self, bridge: GitHubKubernetesBridge):
        """Test supported webhook events include both GitHub and K8s."""
        events = bridge.supported_webhook_events

        # GitHub events
        assert "workflow_run.completed" in events
        assert "workflow_run.in_progress" in events
        assert "push" in events

        # Kubernetes events
        assert "deployment.progressing" in events
        assert "deployment.available" in events
        assert "deployment.failed" in events
        assert "pod.running" in events
        assert "pod.failed" in events
        assert "pod.crashloop" in events

    def test_register_repo_deployment_mapping(self, bridge: GitHubKubernetesBridge):
        """Test registering repo to deployment mapping."""
        bridge.register_repo_deployment_mapping(
            repo_name="user-service",
            deployment_name="user-service-deploy",
            namespace="production",
        )

        result = bridge.get_deployment_for_repo("user-service")
        assert result == ("production", "user-service-deploy")

    def test_register_repo_deployment_mapping_default_namespace(
        self, bridge: GitHubKubernetesBridge
    ):
        """Test mapping uses default namespace when not specified."""
        bridge.register_repo_deployment_mapping(
            repo_name="api-gateway",
            deployment_name="api-gateway-deploy",
        )

        result = bridge.get_deployment_for_repo("api-gateway")
        assert result == ("production", "api-gateway-deploy")

    def test_get_deployment_for_unknown_repo(self, bridge: GitHubKubernetesBridge):
        """Test getting deployment for unmapped repo."""
        result = bridge.get_deployment_for_repo("unknown-repo")
        assert result is None

    @pytest.mark.asyncio
    async def test_health_check(self, bridge: GitHubKubernetesBridge):
        """Test health check."""
        health = await bridge.health_check()

        assert health.healthy is True
        assert health.name == "github-kubernetes-bridge"

    @pytest.mark.asyncio
    async def test_generate_mock_events(self, bridge: GitHubKubernetesBridge):
        """Test generating mock events."""
        events = await bridge.generate_mock_events()

        # Mock events may be empty if no correlations exist
        assert isinstance(events, list)
        # Bridge generates events based on existing correlations
        # so empty list is valid for a fresh bridge


class TestGitHubKubernetesBridgeWebhookHandling:
    """Tests for bridge webhook handling."""

    @pytest.fixture
    def bridge(self) -> GitHubKubernetesBridge:
        """Create bridge with repo mapping."""
        config = ForgeConfig(mode=ForgeMode.MOCK)
        bridge = GitHubKubernetesBridge(config=config)
        bridge.register_repo_deployment_mapping(
            repo_name="user-service",
            deployment_name="user-service",
            namespace="production",
        )
        return bridge

    @pytest.mark.asyncio
    async def test_handle_build_started(self, bridge: GitHubKubernetesBridge):
        """Test handling build started event creates correlation."""
        payload = WebhookPayload(
            source="github",
            event_type="workflow_run.in_progress",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {
                    "id": 11111,
                    "name": "CI/CD Pipeline",
                    "head_branch": "main",
                    "head_sha": "abc123def456",
                    "status": "in_progress",
                },
                "repository": {"name": "user-service"},
            },
        )

        await bridge.on_webhook(payload)

        # Verify correlation was created
        correlation_id = "user-service/11111"
        assert correlation_id in bridge._correlations

        correlation = bridge._correlations[correlation_id]
        assert correlation.build_id == "11111"
        assert correlation.workflow_name == "CI/CD Pipeline"
        assert correlation.repo == "user-service"
        assert correlation.build_status == "pending"
        assert correlation.deployment_name == "user-service"
        assert correlation.namespace == "production"

    @pytest.mark.asyncio
    async def test_handle_build_completed_success(self, bridge: GitHubKubernetesBridge):
        """Test handling successful build completion."""
        # First start the build
        start_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.in_progress",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {
                    "id": 22222,
                    "name": "CI/CD Pipeline",
                    "head_branch": "main",
                    "head_sha": "def456ghi789",
                },
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(start_payload)

        # Now complete it
        complete_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.completed",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {
                    "id": 22222,
                    "name": "CI/CD Pipeline",
                    "head_branch": "main",
                    "head_sha": "def456ghi789",
                    "status": "completed",
                    "conclusion": "success",
                },
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(complete_payload)

        correlation = bridge._correlations["user-service/22222"]
        assert correlation.build_status == "success"
        assert correlation.build_completed_at is not None
        assert correlation.image_tag is not None
        assert correlation.compute_status() == BuildToDeploymentStatus.BUILD_PASSED

    @pytest.mark.asyncio
    async def test_handle_build_completed_failure(self, bridge: GitHubKubernetesBridge):
        """Test handling failed build completion."""
        # First start the build
        start_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.in_progress",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {"id": 33333, "name": "CI/CD", "head_sha": "xyz"},
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(start_payload)

        # Now fail it
        fail_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.completed",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {
                    "id": 33333,
                    "conclusion": "failure",
                },
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(fail_payload)

        correlation = bridge._correlations["user-service/33333"]
        assert correlation.build_status == "failure"
        assert correlation.compute_status() == BuildToDeploymentStatus.BUILD_FAILED

    @pytest.mark.asyncio
    async def test_handle_deployment_progressing(self, bridge: GitHubKubernetesBridge):
        """Test handling deployment progressing event."""
        # First create a build correlation
        start_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.in_progress",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {"id": 44444, "name": "CI/CD", "head_sha": "prog123"},
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(start_payload)

        # Complete the build
        complete_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.completed",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {
                    "id": 44444,
                    "conclusion": "success",
                    "head_sha": "prog123",
                },
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(complete_payload)

        # Now deployment starts
        deploy_payload = WebhookPayload(
            source="kubernetes",
            event_type="deployment.progressing",
            timestamp=datetime.utcnow(),
            raw_payload={
                "deployment": {
                    "name": "user-service",
                    "namespace": "production",
                },
                "image": f"user-service:{bridge._correlations['user-service/44444'].commit_sha[:7]}",
            },
        )
        await bridge.on_webhook(deploy_payload)

        correlation = bridge._correlations["user-service/44444"]
        assert correlation.deployment_status == "progressing"
        assert correlation.compute_status() == BuildToDeploymentStatus.DEPLOYING

    @pytest.mark.asyncio
    async def test_handle_deployment_available(self, bridge: GitHubKubernetesBridge):
        """Test handling deployment available event."""
        # Create correlation
        start_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.in_progress",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {"id": 55555, "name": "CI/CD", "head_sha": "avail123"},
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(start_payload)

        complete_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.completed",
            timestamp=datetime.utcnow(),
            raw_payload={
                "workflow_run": {"id": 55555, "conclusion": "success", "head_sha": "avail123"},
                "repository": {"name": "user-service"},
            },
        )
        await bridge.on_webhook(complete_payload)

        # Deployment becomes available
        available_payload = WebhookPayload(
            source="kubernetes",
            event_type="deployment.available",
            timestamp=datetime.utcnow(),
            raw_payload={
                "deployment": {
                    "name": "user-service",
                    "namespace": "production",
                    "replicas": 3,
                    "availableReplicas": 3,
                },
                "image": f"user-service:{bridge._correlations['user-service/55555'].commit_sha[:7]}",
            },
        )
        await bridge.on_webhook(available_payload)

        correlation = bridge._correlations["user-service/55555"]
        assert correlation.deployment_status == "available"
        assert correlation.deployment_completed_at is not None

    @pytest.mark.asyncio
    async def test_full_build_to_deploy_cycle(self, bridge: GitHubKubernetesBridge):
        """Test complete build→deploy cycle and correlation report."""
        build_id = 99999

        # 1. Build starts
        await bridge.on_webhook(
            WebhookPayload(
                source="github",
                event_type="workflow_run.in_progress",
                timestamp=datetime.utcnow(),
                raw_payload={
                    "workflow_run": {
                        "id": build_id,
                        "name": "CI/CD Pipeline",
                        "head_branch": "main",
                        "head_sha": "fullcycle123",
                    },
                    "repository": {"name": "user-service"},
                },
            )
        )

        # 2. Build completes
        await bridge.on_webhook(
            WebhookPayload(
                source="github",
                event_type="workflow_run.completed",
                timestamp=datetime.utcnow(),
                raw_payload={
                    "workflow_run": {
                        "id": build_id,
                        "conclusion": "success",
                        "head_sha": "fullcycle123",
                    },
                    "repository": {"name": "user-service"},
                },
            )
        )

        # 3. Deployment progresses
        await bridge.on_webhook(
            WebhookPayload(
                source="kubernetes",
                event_type="deployment.progressing",
                timestamp=datetime.utcnow(),
                raw_payload={
                    "deployment": {"name": "user-service", "namespace": "production"},
                    "image": "user-service:fullcyc",
                },
            )
        )

        # 4. Deployment available
        await bridge.on_webhook(
            WebhookPayload(
                source="kubernetes",
                event_type="deployment.available",
                timestamp=datetime.utcnow(),
                raw_payload={
                    "deployment": {
                        "name": "user-service",
                        "namespace": "production",
                        "replicas": 3,
                        "availableReplicas": 3,
                    },
                    "image": "user-service:fullcyc",
                },
            )
        )

        # Verify final state
        correlation = bridge._correlations[f"user-service/{build_id}"]
        assert correlation.build_status == "success"
        assert correlation.deployment_status == "available"

        # Generate report
        report = correlation.to_report()
        assert report["status"] in ("healthy", "deployed")
        assert report["build"]["status"] == "success"
        assert report["deployment"]["status"] == "available"


class TestGitHubKubernetesBridgeSingleton:
    """Tests for bridge singleton factory."""

    def test_get_github_kubernetes_bridge_singleton(self):
        """Test that factory returns singleton."""
        import app.forges.github_k8s_bridge as module

        # Reset singleton
        module._github_k8s_bridge = None

        bridge1 = get_github_kubernetes_bridge()
        bridge2 = get_github_kubernetes_bridge()

        assert bridge1 is bridge2


class TestBridgeCorrelationLookup:
    """Tests for correlation lookup methods."""

    @pytest.fixture
    def bridge_with_correlations(self) -> GitHubKubernetesBridge:
        """Create bridge with pre-populated correlations."""
        config = ForgeConfig(mode=ForgeMode.MOCK)
        bridge = GitHubKubernetesBridge(config=config)

        # Add some correlations
        bridge._correlations["user-service/100"] = BuildDeploymentCorrelation(
            build_id="100",
            workflow_name="CI/CD",
            repo="user-service",
            branch="main",
            commit_sha="abc123",
            build_status="success",
            deployment_status="available",
        )
        bridge._correlations["api-gateway/200"] = BuildDeploymentCorrelation(
            build_id="200",
            workflow_name="Build",
            repo="api-gateway",
            branch="main",
            commit_sha="def456",
            build_status="failure",
        )

        return bridge

    def test_get_all_correlations(self, bridge_with_correlations: GitHubKubernetesBridge):
        """Test getting all correlations."""
        correlations = bridge_with_correlations._correlations

        assert len(correlations) == 2
        assert "user-service/100" in correlations
        assert "api-gateway/200" in correlations

    def test_correlation_report_generation(self, bridge_with_correlations: GitHubKubernetesBridge):
        """Test generating reports from correlations."""
        reports = [c.to_report() for c in bridge_with_correlations._correlations.values()]

        assert len(reports) == 2
        assert any(r["build"]["repo"] == "user-service" for r in reports)
        assert any(r["build"]["repo"] == "api-gateway" for r in reports)
