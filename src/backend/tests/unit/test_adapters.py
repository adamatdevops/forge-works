"""Unit tests for external service adapters."""

import pytest

from app.adapters import (
    AdapterMode,
    GitHubAdapter,
    ArgoCDAdapter,
    PRState,
    SyncStatus,
    HealthStatus,
    get_github_adapter,
    get_argocd_adapter,
)


class TestGitHubAdapter:
    """Tests for GitHub adapter in mock mode."""

    @pytest.fixture
    def adapter(self) -> GitHubAdapter:
        """Create a fresh GitHub adapter for each test."""
        return GitHubAdapter(mode=AdapterMode.MOCK)

    @pytest.mark.asyncio
    async def test_health_check(self, adapter: GitHubAdapter):
        """Test health check returns healthy in mock mode."""
        health = await adapter.health_check()

        assert health.healthy is True
        assert health.mode == AdapterMode.MOCK
        assert health.name == "github"
        assert health.latency_ms is not None
        assert health.error is None

    @pytest.mark.asyncio
    async def test_list_repositories(self, adapter: GitHubAdapter):
        """Test listing mock repositories."""
        repos = await adapter.list_repositories()

        assert len(repos) > 0
        assert all(r.name for r in repos)
        assert all(r.full_name.startswith("forge-org/") for r in repos)

    @pytest.mark.asyncio
    async def test_list_repositories_by_language(self, adapter: GitHubAdapter):
        """Test filtering repositories by language."""
        python_repos = await adapter.list_repositories(language="Python")
        go_repos = await adapter.list_repositories(language="Go")

        assert all(r.language == "Python" for r in python_repos)
        assert all(r.language == "Go" for r in go_repos)

    @pytest.mark.asyncio
    async def test_get_repository(self, adapter: GitHubAdapter):
        """Test getting a specific repository."""
        repo = await adapter.get_repository("user-service")

        assert repo is not None
        assert repo.name == "user-service"
        assert repo.full_name == "forge-org/user-service"
        assert repo.description is not None

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self, adapter: GitHubAdapter):
        """Test getting a non-existent repository."""
        repo = await adapter.get_repository("nonexistent-repo")

        assert repo is None

    @pytest.mark.asyncio
    async def test_get_branches(self, adapter: GitHubAdapter):
        """Test getting branches for a repository."""
        branches = await adapter.get_branches("user-service")

        assert len(branches) > 0
        branch_names = [b.name for b in branches]
        assert "main" in branch_names
        assert "develop" in branch_names

    @pytest.mark.asyncio
    async def test_get_recent_commits(self, adapter: GitHubAdapter):
        """Test getting recent commits."""
        commits = await adapter.get_recent_commits("user-service", limit=5)

        assert len(commits) == 5
        assert all(c.sha for c in commits)
        assert all(c.author for c in commits)
        assert all(c.message for c in commits)

    @pytest.mark.asyncio
    async def test_get_pull_requests(self, adapter: GitHubAdapter):
        """Test getting pull requests."""
        prs = await adapter.get_pull_requests("user-service")

        assert len(prs) > 0
        assert all(pr.title for pr in prs)
        assert all(pr.number > 0 for pr in prs)

    @pytest.mark.asyncio
    async def test_get_pull_requests_filtered(self, adapter: GitHubAdapter):
        """Test filtering pull requests by state."""
        open_prs = await adapter.get_pull_requests("user-service", state=PRState.OPEN)
        merged_prs = await adapter.get_pull_requests("user-service", state=PRState.MERGED)

        assert all(pr.state == PRState.OPEN for pr in open_prs)
        assert all(pr.state == PRState.MERGED for pr in merged_prs)

    @pytest.mark.asyncio
    async def test_get_workflow_runs(self, adapter: GitHubAdapter):
        """Test getting workflow runs."""
        runs = await adapter.get_workflow_runs("user-service", limit=5)

        assert len(runs) == 5
        assert all(r.name for r in runs)
        assert all(r.run_number > 0 for r in runs)

    @pytest.mark.asyncio
    async def test_create_repository_from_template(self, adapter: GitHubAdapter):
        """Test creating a repository from template."""
        repo = await adapter.create_repository_from_template(
            template_repo="python-api-template",
            new_repo_name="my-new-service",
            description="A new service",
        )

        assert repo.name == "my-new-service"
        assert repo.description == "A new service"
        assert "golden-path" in repo.topics

        # Verify it's now in the list
        found = await adapter.get_repository("my-new-service")
        assert found is not None


class TestArgoCDAdapter:
    """Tests for ArgoCD adapter in mock mode."""

    @pytest.fixture
    def adapter(self) -> ArgoCDAdapter:
        """Create a fresh ArgoCD adapter for each test."""
        return ArgoCDAdapter(mode=AdapterMode.MOCK)

    @pytest.mark.asyncio
    async def test_health_check(self, adapter: ArgoCDAdapter):
        """Test health check returns healthy in mock mode."""
        health = await adapter.health_check()

        assert health.healthy is True
        assert health.mode == AdapterMode.MOCK
        assert health.name == "argocd"
        assert health.error is None

    @pytest.mark.asyncio
    async def test_list_applications(self, adapter: ArgoCDAdapter):
        """Test listing all applications."""
        apps = await adapter.list_applications()

        assert len(apps) > 0
        assert all(a.name for a in apps)

    @pytest.mark.asyncio
    async def test_list_applications_by_project(self, adapter: ArgoCDAdapter):
        """Test filtering applications by project."""
        platform_apps = await adapter.list_applications(project="platform")

        assert len(platform_apps) > 0
        # All summaries should be from the platform project

    @pytest.mark.asyncio
    async def test_list_applications_by_health(self, adapter: ArgoCDAdapter):
        """Test filtering applications by health status."""
        healthy_apps = await adapter.list_applications(health_status=HealthStatus.HEALTHY)
        degraded_apps = await adapter.list_applications(health_status=HealthStatus.DEGRADED)

        assert all(a.health_status == HealthStatus.HEALTHY for a in healthy_apps)
        assert all(a.health_status == HealthStatus.DEGRADED for a in degraded_apps)

    @pytest.mark.asyncio
    async def test_get_application(self, adapter: ArgoCDAdapter):
        """Test getting a specific application."""
        app = await adapter.get_application("user-service")

        assert app is not None
        assert app.name == "user-service"
        assert app.project == "platform"
        assert len(app.resources) > 0

    @pytest.mark.asyncio
    async def test_get_application_not_found(self, adapter: ArgoCDAdapter):
        """Test getting a non-existent application."""
        app = await adapter.get_application("nonexistent-app")

        assert app is None

    @pytest.mark.asyncio
    async def test_get_application_resources(self, adapter: ArgoCDAdapter):
        """Test getting application resources."""
        resources = await adapter.get_application_resources("user-service")

        assert len(resources) > 0
        kinds = [r.kind for r in resources]
        assert "Deployment" in kinds
        assert "Service" in kinds

    @pytest.mark.asyncio
    async def test_sync_application(self, adapter: ArgoCDAdapter):
        """Test syncing an application."""
        result = await adapter.sync_application("user-service")

        assert result.app_name == "user-service"
        assert result.phase.value == "Succeeded"
        assert result.finished_at is not None

    @pytest.mark.asyncio
    async def test_sync_application_dry_run(self, adapter: ArgoCDAdapter):
        """Test dry run sync."""
        result = await adapter.sync_application("user-service", dry_run=True)

        assert result.phase.value == "Succeeded"
        assert "Dry run" in result.message

    @pytest.mark.asyncio
    async def test_sync_application_not_found(self, adapter: ArgoCDAdapter):
        """Test syncing non-existent application."""
        with pytest.raises(ValueError, match="not found"):
            await adapter.sync_application("nonexistent-app")

    @pytest.mark.asyncio
    async def test_rollback_application(self, adapter: ArgoCDAdapter):
        """Test rolling back an application."""
        result = await adapter.rollback_application("user-service", revision_id=5)

        assert result.app_name == "user-service"
        assert "rollback" in result.revision
        assert result.phase.value == "Succeeded"

    @pytest.mark.asyncio
    async def test_get_sync_history(self, adapter: ArgoCDAdapter):
        """Test getting sync history."""
        history = await adapter.get_sync_history("user-service", limit=5)

        assert len(history) == 5
        assert all(h.revision for h in history)
        assert all(h.started_at for h in history)

    @pytest.mark.asyncio
    async def test_create_application(self, adapter: ArgoCDAdapter):
        """Test creating a new application."""
        app = await adapter.create_application(
            name="new-service",
            repo_url="https://github.com/forge-org/new-service.git",
            path="k8s/overlays/production",
            destination_namespace="production",
        )

        assert app.name == "new-service"
        assert app.sync_status == SyncStatus.OUT_OF_SYNC
        assert app.health_status == HealthStatus.MISSING
        assert len(app.resources) > 0

        # Verify it's now retrievable
        found = await adapter.get_application("new-service")
        assert found is not None

    @pytest.mark.asyncio
    async def test_delete_application(self, adapter: ArgoCDAdapter):
        """Test deleting an application."""
        # First create one
        await adapter.create_application(
            name="to-delete",
            repo_url="https://github.com/forge-org/to-delete.git",
            path="k8s",
        )

        # Delete it
        result = await adapter.delete_application("to-delete")
        assert result is True

        # Verify it's gone
        found = await adapter.get_application("to-delete")
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_application_not_found(self, adapter: ArgoCDAdapter):
        """Test deleting non-existent application."""
        result = await adapter.delete_application("nonexistent-app")
        assert result is False


class TestAdapterSingletons:
    """Tests for adapter singleton factories."""

    def test_github_adapter_singleton(self):
        """Test GitHub adapter factory returns same instance."""
        # Reset singleton for test
        import app.adapters.github as gh_module
        gh_module._github_adapter = None

        adapter1 = get_github_adapter()
        adapter2 = get_github_adapter()

        assert adapter1 is adapter2

    def test_argocd_adapter_singleton(self):
        """Test ArgoCD adapter factory returns same instance."""
        # Reset singleton for test
        import app.adapters.argocd as argo_module
        argo_module._argocd_adapter = None

        adapter1 = get_argocd_adapter()
        adapter2 = get_argocd_adapter()

        assert adapter1 is adapter2


class TestAdapterDataConversion:
    """Tests for data class to_dict methods."""

    @pytest.mark.asyncio
    async def test_repository_to_dict(self):
        """Test Repository serialization."""
        adapter = GitHubAdapter(mode=AdapterMode.MOCK)
        repo = await adapter.get_repository("user-service")

        data = repo.to_dict()

        assert "id" in data
        assert "name" in data
        assert "full_name" in data
        assert "created_at" in data
        assert isinstance(data["topics"], list)

    @pytest.mark.asyncio
    async def test_application_to_dict(self):
        """Test Application serialization."""
        adapter = ArgoCDAdapter(mode=AdapterMode.MOCK)
        app = await adapter.get_application("user-service")

        data = app.to_dict()

        assert "name" in data
        assert "sync_status" in data
        assert "health_status" in data
        assert "resources" in data
        assert isinstance(data["resources"], list)

    @pytest.mark.asyncio
    async def test_adapter_health_to_dict(self):
        """Test AdapterHealth serialization."""
        adapter = GitHubAdapter(mode=AdapterMode.MOCK)
        health = await adapter.health_check()

        data = health.to_dict()

        assert data["name"] == "github"
        assert data["healthy"] is True
        assert data["mode"] == "mock"
