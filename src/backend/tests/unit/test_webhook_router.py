"""Unit tests for webhook router and signature validation."""

import hashlib
import hmac
from unittest.mock import MagicMock

from app.forges.base import ForgeAdapter, StateDiff, WebhookPayload
from app.forges.webhook_router import (
    _forge_registry,
    get_registered_forges,
    list_webhook_sources,
    parse_argocd_event,
    parse_github_event,
    parse_kubernetes_event,
    register_forge,
    unregister_forge,
    validate_argocd_signature,
    validate_github_signature,
    validate_kubernetes_token,
)


class MockForge(ForgeAdapter):
    """Mock Forge implementation for testing."""

    @property
    def forge_name(self) -> str:
        return "mock-forge"

    @property
    def supported_webhook_events(self) -> list[str]:
        return ["test.event"]

    async def fetch_external_state(self) -> dict:
        return {}

    async def get_local_state(self) -> dict:
        return {}

    async def apply_external_state(self, diff: StateDiff) -> bool:
        return True

    async def push_local_state(self, diff: StateDiff) -> bool:
        return True

    async def handle_webhook_event(self, payload: WebhookPayload) -> None:
        pass

    async def generate_mock_events(self) -> list[WebhookPayload]:
        return []


class TestForgeRegistry:
    """Tests for forge registration."""

    def setup_method(self):
        """Clear registry before each test."""
        _forge_registry.clear()

    def test_register_forge(self):
        """Test registering a forge."""
        forge = MockForge()
        register_forge("github", forge)

        assert "github" in _forge_registry
        assert forge in _forge_registry["github"]

    def test_register_multiple_forges_same_source(self):
        """Test registering multiple forges for same source."""
        forge1 = MockForge()
        forge2 = MockForge()

        register_forge("github", forge1)
        register_forge("github", forge2)

        forges = get_registered_forges("github")
        assert len(forges) == 2
        assert forge1 in forges
        assert forge2 in forges

    def test_unregister_forge(self):
        """Test unregistering a forge."""
        forge = MockForge()
        register_forge("github", forge)
        unregister_forge("github", forge)

        forges = get_registered_forges("github")
        assert forge not in forges

    def test_unregister_nonexistent_forge(self):
        """Test unregistering a forge that doesn't exist."""
        forge = MockForge()
        # Should not raise
        unregister_forge("github", forge)

    def test_get_registered_forges_empty(self):
        """Test getting forges for unregistered source."""
        forges = get_registered_forges("nonexistent")
        assert forges == []

    def test_list_webhook_sources(self):
        """Test listing webhook sources."""
        forge = MockForge()
        register_forge("github", forge)
        register_forge("kubernetes", forge)

        sources = list_webhook_sources()
        assert "github" in sources
        assert "kubernetes" in sources


class TestGitHubSignatureValidation:
    """Tests for GitHub webhook signature validation."""

    def test_valid_signature(self):
        """Test valid GitHub signature."""
        secret = "test-secret"
        payload = b'{"action": "opened"}'
        signature = (
            "sha256="
            + hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()
        )

        assert validate_github_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        """Test invalid GitHub signature."""
        payload = b'{"action": "opened"}'
        assert validate_github_signature(payload, "sha256=invalid", "secret") is False

    def test_missing_prefix(self):
        """Test signature without sha256= prefix."""
        payload = b'{"action": "opened"}'
        signature = hmac.new(
            b"secret",
            payload,
            hashlib.sha256,
        ).hexdigest()

        assert validate_github_signature(payload, signature, "secret") is False


class TestArgoCDSignatureValidation:
    """Tests for ArgoCD webhook signature validation."""

    def test_valid_signature(self):
        """Test valid ArgoCD signature."""
        secret = "test-secret"
        payload = b'{"type": "sync"}'
        signature = (
            "sha1="
            + hmac.new(
                secret.encode(),
                payload,
                hashlib.sha1,
            ).hexdigest()
        )

        assert validate_argocd_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        """Test invalid ArgoCD signature."""
        payload = b'{"type": "sync"}'
        assert validate_argocd_signature(payload, "sha1=invalid", "secret") is False

    def test_missing_prefix(self):
        """Test signature without sha1= prefix."""
        payload = b'{"type": "sync"}'
        signature = hmac.new(
            b"secret",
            payload,
            hashlib.sha1,
        ).hexdigest()

        assert validate_argocd_signature(payload, signature, "secret") is False


class TestKubernetesTokenValidation:
    """Tests for Kubernetes webhook token validation."""

    def test_valid_token(self):
        """Test valid Kubernetes token."""
        assert validate_kubernetes_token("valid-token", "valid-token") is True

    def test_invalid_token(self):
        """Test invalid Kubernetes token."""
        assert validate_kubernetes_token("wrong-token", "valid-token") is False


class TestGitHubEventParser:
    """Tests for GitHub event parsing."""

    def test_parse_push_event(self):
        """Test parsing a push event."""
        request = MagicMock()
        request.headers = {"X-GitHub-Event": "push"}

        body = {"ref": "refs/heads/main", "commits": []}

        payload = parse_github_event(request, body)

        assert payload.source == "github"
        assert payload.event_type == "push"
        assert payload.raw_payload == body

    def test_parse_pull_request_event(self):
        """Test parsing a pull request event with action."""
        request = MagicMock()
        request.headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=abc123",
        }

        body = {"action": "opened", "pull_request": {"number": 123}}

        payload = parse_github_event(request, body)

        assert payload.source == "github"
        assert payload.event_type == "pull_request.opened"
        assert payload.signature == "sha256=abc123"

    def test_parse_workflow_run_event(self):
        """Test parsing a workflow run event."""
        request = MagicMock()
        request.headers = {"X-GitHub-Event": "workflow_run"}

        body = {
            "action": "completed",
            "workflow_run": {"id": 123, "conclusion": "success"},
        }

        payload = parse_github_event(request, body)

        assert payload.event_type == "workflow_run.completed"


class TestArgoCDEventParser:
    """Tests for ArgoCD event parsing."""

    def test_parse_sync_event(self):
        """Test parsing a sync event."""
        request = MagicMock()
        request.headers = {"X-Argocd-Signature": "sha1=abc123"}

        body = {"type": "sync", "application": "user-service"}

        payload = parse_argocd_event(request, body)

        assert payload.source == "argocd"
        assert payload.event_type == "sync"
        assert payload.signature == "sha1=abc123"

    def test_parse_default_event_type(self):
        """Test parsing event without explicit type."""
        request = MagicMock()
        request.headers = {}

        body = {"application": "user-service"}

        payload = parse_argocd_event(request, body)

        # Defaults to "sync"
        assert payload.event_type == "sync"


class TestKubernetesEventParser:
    """Tests for Kubernetes event parsing."""

    def test_parse_custom_format(self):
        """Test parsing ForgeWorks custom format."""
        request = MagicMock()
        request.headers = {"Authorization": "Bearer token123"}

        body = {
            "event_type": "deployment.available",
            "deployment": {"name": "user-service"},
        }

        payload = parse_kubernetes_event(request, body)

        assert payload.source == "kubernetes"
        assert payload.event_type == "deployment.available"
        assert payload.signature == "Bearer token123"

    def test_parse_admission_webhook(self):
        """Test parsing Kubernetes AdmissionReview format."""
        request = MagicMock()
        request.headers = {"Authorization": "Bearer token123"}

        body = {
            "kind": "AdmissionReview",
            "request": {
                "operation": "CREATE",
                "object": {"kind": "Deployment"},
            },
        }

        payload = parse_kubernetes_event(request, body)

        assert payload.source == "kubernetes"
        assert payload.event_type == "AdmissionReview.CREATE"

    def test_parse_without_operation(self):
        """Test parsing without operation field."""
        request = MagicMock()
        request.headers = {}

        body = {"kind": "AdmissionReview"}

        payload = parse_kubernetes_event(request, body)

        assert payload.event_type == "AdmissionReview.unknown"
