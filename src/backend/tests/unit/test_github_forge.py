"""Unit tests for GitHub Forge."""

from datetime import UTC, datetime

import pytest

from app.forges.base import ForgeConfig, ForgeMode, WebhookPayload
from app.forges.github_forge import GitHubForge, get_github_forge


class TestGitHubForge:
    """Tests for GitHub Forge."""

    @pytest.fixture
    def forge(self) -> GitHubForge:
        """Create a fresh GitHub Forge for each test."""
        config = ForgeConfig(mode=ForgeMode.MOCK)
        return GitHubForge(config=config, github_org="test-org")

    def test_forge_name(self, forge: GitHubForge):
        """Test forge name property."""
        assert forge.forge_name == "github-forge"

    def test_supported_webhook_events(self, forge: GitHubForge):
        """Test supported webhook events."""
        events = forge.supported_webhook_events

        assert "pull_request.opened" in events
        assert "pull_request.closed" in events
        assert "pull_request.merged" in events
        assert "workflow_run.completed" in events
        assert "push" in events
        assert "release.published" in events

    def test_default_config(self, forge: GitHubForge):
        """Test default forge configuration."""
        assert forge.github_org == "test-org"
        assert forge.config.mode == ForgeMode.MOCK

    @pytest.mark.asyncio
    async def test_health_check(self, forge: GitHubForge):
        """Test health check returns healthy in mock mode."""
        health = await forge.health_check()

        assert health.healthy is True
        assert health.name == "github-forge"
        assert health.webhook_active is False  # No webhooks received yet

    @pytest.mark.asyncio
    async def test_fetch_external_state(self, forge: GitHubForge):
        """Test fetching external state."""
        state = await forge.fetch_external_state()

        assert isinstance(state, dict)
        assert "repos" in state
        assert "workflows" in state
        assert "pull_requests" in state

    @pytest.mark.asyncio
    async def test_get_local_state(self, forge: GitHubForge):
        """Test getting local state."""
        state = await forge.get_local_state()

        assert isinstance(state, dict)

    @pytest.mark.asyncio
    async def test_generate_mock_events(self, forge: GitHubForge):
        """Test generating mock events."""
        events = await forge.generate_mock_events()

        assert isinstance(events, list)
        assert len(events) > 0
        for event in events:
            assert isinstance(event, WebhookPayload)
            assert event.source == "github"


class TestGitHubForgeWebhookHandling:
    """Tests for GitHub Forge webhook handling."""

    @pytest.fixture
    def forge(self) -> GitHubForge:
        """Create a fresh GitHub Forge for each test."""
        config = ForgeConfig(mode=ForgeMode.MOCK)
        return GitHubForge(config=config)

    @pytest.mark.asyncio
    async def test_handle_pr_opened(self, forge: GitHubForge):
        """Test handling PR opened event."""
        payload = WebhookPayload(
            source="github",
            event_type="pull_request.opened",
            timestamp=datetime.now(UTC),
            raw_payload={
                "action": "opened",
                "pull_request": {
                    "number": 123,
                    "title": "Add new feature",
                    "user": {"login": "developer"},
                    "head": {"ref": "feature-branch"},
                    "base": {"ref": "main"},
                    "html_url": "https://github.com/org/repo/pull/123",
                    "created_at": "2024-01-15T10:00:00Z",
                },
                "repository": {"name": "user-service"},
            },
        )

        await forge.on_webhook(payload)

        # Check PR was cached
        pr_id = "user-service/123"
        assert pr_id in forge._pr_cache
        assert forge._pr_cache[pr_id]["title"] == "Add new feature"
        assert forge._pr_cache[pr_id]["state"] == "open"

    @pytest.mark.asyncio
    async def test_handle_pr_closed_without_merge(self, forge: GitHubForge):
        """Test handling PR closed without merge."""
        # First open the PR
        open_payload = WebhookPayload(
            source="github",
            event_type="pull_request.opened",
            timestamp=datetime.now(UTC),
            raw_payload={
                "pull_request": {
                    "number": 124,
                    "title": "Feature PR",
                    "user": {"login": "dev"},
                    "head": {"ref": "feature"},
                    "base": {"ref": "main"},
                },
                "repository": {"name": "api-service"},
            },
        )
        await forge.on_webhook(open_payload)

        # Now close without merge
        close_payload = WebhookPayload(
            source="github",
            event_type="pull_request.closed",
            timestamp=datetime.now(UTC),
            raw_payload={
                "action": "closed",
                "pull_request": {
                    "number": 124,
                    "merged": False,
                },
                "repository": {"name": "api-service"},
            },
        )
        await forge.on_webhook(close_payload)

        assert forge._pr_cache["api-service/124"]["state"] == "closed"

    @pytest.mark.asyncio
    async def test_handle_workflow_run_started(self, forge: GitHubForge):
        """Test handling workflow run started event."""
        payload = WebhookPayload(
            source="github",
            event_type="workflow_run.requested",
            timestamp=datetime.now(UTC),
            raw_payload={
                "action": "requested",
                "workflow_run": {
                    "id": 12345,
                    "name": "CI/CD Pipeline",
                    "run_number": 42,
                    "head_sha": "abc123",
                    "head_branch": "main",
                    "status": "queued",
                    "conclusion": None,
                },
                "repository": {"name": "user-service"},
            },
        )

        await forge.on_webhook(payload)

        # Workflow should be cached by ID
        assert "12345" in forge._workflow_cache
        assert forge._workflow_cache["12345"]["repo"] == "user-service"

    @pytest.mark.asyncio
    async def test_handle_workflow_run_completed_success(self, forge: GitHubForge):
        """Test handling successful workflow completion."""
        # First start the workflow (completion only updates existing cache)
        start_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.requested",
            timestamp=datetime.now(UTC),
            raw_payload={
                "workflow_run": {
                    "id": 12346,
                    "name": "CI/CD Pipeline",
                    "head_branch": "main",
                    "head_sha": "def456",
                },
                "repository": {"name": "user-service"},
            },
        )
        await forge.on_webhook(start_payload)

        # Now complete it
        complete_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.completed",
            timestamp=datetime.now(UTC),
            raw_payload={
                "action": "completed",
                "workflow_run": {
                    "id": 12346,
                    "name": "CI/CD Pipeline",
                    "run_number": 43,
                    "head_sha": "def456",
                    "head_branch": "main",
                    "status": "completed",
                    "conclusion": "success",
                },
                "repository": {"name": "user-service"},
            },
        )
        await forge.on_webhook(complete_payload)

        # Verify workflow was processed (cached by ID only)
        assert "12346" in forge._workflow_cache
        assert forge._workflow_cache["12346"]["conclusion"] == "success"

    @pytest.mark.asyncio
    async def test_handle_workflow_run_completed_failure(self, forge: GitHubForge):
        """Test handling failed workflow completion."""
        # First start the workflow (completion only updates existing cache)
        start_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.requested",
            timestamp=datetime.now(UTC),
            raw_payload={
                "workflow_run": {
                    "id": 12347,
                    "name": "CI/CD Pipeline",
                    "head_branch": "main",
                    "head_sha": "ghi789",
                },
                "repository": {"name": "user-service"},
            },
        )
        await forge.on_webhook(start_payload)

        # Now fail it
        fail_payload = WebhookPayload(
            source="github",
            event_type="workflow_run.completed",
            timestamp=datetime.now(UTC),
            raw_payload={
                "action": "completed",
                "workflow_run": {
                    "id": 12347,
                    "name": "CI/CD Pipeline",
                    "run_number": 44,
                    "head_sha": "ghi789",
                    "head_branch": "main",
                    "status": "completed",
                    "conclusion": "failure",
                },
                "repository": {"name": "user-service"},
            },
        )
        await forge.on_webhook(fail_payload)

        # Verify workflow was processed (cached by ID only)
        assert "12347" in forge._workflow_cache
        assert forge._workflow_cache["12347"]["conclusion"] == "failure"

    @pytest.mark.asyncio
    async def test_handle_push_event(self, forge: GitHubForge):
        """Test handling push event."""
        payload = WebhookPayload(
            source="github",
            event_type="push",
            timestamp=datetime.now(UTC),
            raw_payload={
                "ref": "refs/heads/main",
                "after": "newsha123",
                "before": "oldsha456",
                "commits": [
                    {
                        "id": "newsha123",
                        "message": "Update feature",
                        "author": {"name": "Developer"},
                    }
                ],
                "repository": {"name": "user-service"},
            },
        )

        # Should not raise
        await forge.on_webhook(payload)

    @pytest.mark.asyncio
    async def test_handle_release_event(self, forge: GitHubForge):
        """Test handling release event."""
        payload = WebhookPayload(
            source="github",
            event_type="release.published",
            timestamp=datetime.now(UTC),
            raw_payload={
                "action": "published",
                "release": {
                    "tag_name": "v1.2.0",
                    "name": "Version 1.2.0",
                    "body": "Release notes...",
                    "html_url": "https://github.com/org/repo/releases/tag/v1.2.0",
                    "created_at": "2024-01-20T12:00:00Z",
                },
                "repository": {"name": "user-service"},
            },
        )

        # Should not raise
        await forge.on_webhook(payload)

    @pytest.mark.asyncio
    async def test_unknown_event_type_ignored(self, forge: GitHubForge):
        """Test that unknown event types are gracefully ignored."""
        payload = WebhookPayload(
            source="github",
            event_type="unknown.event",
            timestamp=datetime.now(UTC),
            raw_payload={"data": "test"},
        )

        # Should not raise
        await forge.on_webhook(payload)


class TestGitHubForgeSingleton:
    """Tests for GitHub Forge singleton factory."""

    def test_get_github_forge_singleton(self):
        """Test that get_github_forge returns singleton."""
        import app.forges.github_forge as module

        # Reset singleton
        module._github_forge = None

        forge1 = get_github_forge()
        forge2 = get_github_forge()

        assert forge1 is forge2


class TestGitHubForgeRepoServiceMapping:
    """Tests for repository to service mapping."""

    @pytest.fixture
    def forge(self) -> GitHubForge:
        """Create forge with service mapping."""
        config = ForgeConfig(mode=ForgeMode.MOCK)
        forge = GitHubForge(config=config)
        forge._repo_to_service = {
            "user-service": "svc-123",
            "api-gateway": "svc-456",
        }
        return forge

    @pytest.mark.asyncio
    async def test_pr_updates_service_status(self, forge: GitHubForge):
        """Test that PR opened updates mapped service status."""
        payload = WebhookPayload(
            source="github",
            event_type="pull_request.opened",
            timestamp=datetime.now(UTC),
            raw_payload={
                "pull_request": {
                    "number": 100,
                    "title": "New feature",
                    "user": {"login": "dev"},
                    "head": {"ref": "feature"},
                    "base": {"ref": "main"},
                },
                "repository": {"name": "user-service"},
            },
        )

        # Should trigger service status broadcast
        await forge.on_webhook(payload)

        # PR should be cached
        assert "user-service/100" in forge._pr_cache
