"""Unit tests for Forge base classes and utilities."""

from datetime import UTC, datetime

from app.forges.base import (
    ForgeConfig,
    ForgeHealth,
    ForgeMode,
    ReconciliationStrategy,
    StateDiff,
    WebhookPayload,
)


class TestForgeMode:
    """Tests for ForgeMode enum."""

    def test_forge_modes_exist(self):
        """Test all expected forge modes exist."""
        assert ForgeMode.MOCK == "mock"
        assert ForgeMode.LIVE == "live"
        assert ForgeMode.PASSIVE == "passive"

    def test_forge_mode_from_string(self):
        """Test creating ForgeMode from string."""
        assert ForgeMode("mock") == ForgeMode.MOCK
        assert ForgeMode("live") == ForgeMode.LIVE
        assert ForgeMode("passive") == ForgeMode.PASSIVE


class TestReconciliationStrategy:
    """Tests for ReconciliationStrategy enum."""

    def test_strategies_exist(self):
        """Test all expected reconciliation strategies exist."""
        assert ReconciliationStrategy.EXTERNAL_WINS == "external_wins"
        assert ReconciliationStrategy.LOCAL_WINS == "local_wins"
        assert ReconciliationStrategy.MERGE == "merge"
        assert ReconciliationStrategy.ALERT == "alert"


class TestForgeConfig:
    """Tests for ForgeConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ForgeConfig()

        assert config.mode == ForgeMode.MOCK
        assert config.reconciliation_strategy == ReconciliationStrategy.EXTERNAL_WINS
        assert config.reconcile_interval_seconds == 60
        assert config.webhook_secret is None
        assert config.enable_mock_events is True
        assert config.mock_event_interval_seconds == 30

    def test_custom_config(self):
        """Test custom configuration."""
        config = ForgeConfig(
            mode=ForgeMode.LIVE,
            reconciliation_strategy=ReconciliationStrategy.LOCAL_WINS,
            reconcile_interval_seconds=120,
            webhook_secret="my-secret",
            enable_mock_events=False,
            mock_event_interval_seconds=60,
        )

        assert config.mode == ForgeMode.LIVE
        assert config.reconciliation_strategy == ReconciliationStrategy.LOCAL_WINS
        assert config.reconcile_interval_seconds == 120
        assert config.webhook_secret == "my-secret"
        assert config.enable_mock_events is False
        assert config.mock_event_interval_seconds == 60


class TestForgeHealth:
    """Tests for ForgeHealth dataclass."""

    def test_forge_health_defaults(self):
        """Test default health values."""
        from app.adapters.base import AdapterMode

        health = ForgeHealth(
            name="test-forge",
            healthy=True,
            mode=AdapterMode.MOCK,
            latency_ms=50.0,
            last_check=datetime.now(UTC),
        )

        assert health.webhook_active is False
        assert health.last_webhook_received is None
        assert health.last_reconciliation is None
        assert health.pending_events == 0
        assert health.state_drift_detected is False

    def test_forge_health_to_dict(self):
        """Test ForgeHealth serialization."""
        from app.adapters.base import AdapterMode

        now = datetime.now(UTC)
        health = ForgeHealth(
            name="test-forge",
            healthy=True,
            mode=AdapterMode.MOCK,
            latency_ms=50.0,
            last_check=now,
            webhook_active=True,
            last_webhook_received=now,
            last_reconciliation=now,
            pending_events=5,
            state_drift_detected=True,
        )

        data = health.to_dict()

        assert data["name"] == "test-forge"
        assert data["healthy"] is True
        assert data["mode"] == "mock"
        assert data["latency_ms"] == 50.0
        assert data["webhook_active"] is True
        assert data["pending_events"] == 5
        assert data["state_drift_detected"] is True
        assert data["last_webhook_received"] is not None
        assert data["last_reconciliation"] is not None

    def test_forge_health_to_dict_none_values(self):
        """Test ForgeHealth serialization with None values."""
        from app.adapters.base import AdapterMode

        health = ForgeHealth(
            name="test-forge",
            healthy=True,
            mode=AdapterMode.MOCK,
            latency_ms=50.0,
            last_check=datetime.now(UTC),
        )

        data = health.to_dict()

        assert data["last_webhook_received"] is None
        assert data["last_reconciliation"] is None


class TestWebhookPayload:
    """Tests for WebhookPayload dataclass."""

    def test_valid_payload(self):
        """Test creating a valid webhook payload."""
        payload = WebhookPayload(
            source="github",
            event_type="push",
            timestamp=datetime.now(UTC),
            raw_payload={"ref": "refs/heads/main"},
        )

        assert payload.is_valid is True
        assert payload.source == "github"
        assert payload.event_type == "push"
        assert payload.signature is None
        assert payload.headers == {}

    def test_payload_with_signature(self):
        """Test payload with signature."""
        payload = WebhookPayload(
            source="github",
            event_type="push",
            timestamp=datetime.now(UTC),
            raw_payload={"ref": "refs/heads/main"},
            signature="sha256=abc123",
            headers={"X-GitHub-Event": "push"},
        )

        assert payload.is_valid is True
        assert payload.signature == "sha256=abc123"
        assert payload.headers["X-GitHub-Event"] == "push"

    def test_invalid_payload_no_source(self):
        """Test payload is invalid without source."""
        payload = WebhookPayload(
            source="",
            event_type="push",
            timestamp=datetime.now(UTC),
            raw_payload={"data": "test"},
        )

        assert payload.is_valid is False

    def test_invalid_payload_no_event_type(self):
        """Test payload is invalid without event_type."""
        payload = WebhookPayload(
            source="github",
            event_type="",
            timestamp=datetime.now(UTC),
            raw_payload={"data": "test"},
        )

        assert payload.is_valid is False

    def test_invalid_payload_empty_raw_payload(self):
        """Test payload is invalid with empty raw_payload."""
        payload = WebhookPayload(
            source="github",
            event_type="push",
            timestamp=datetime.now(UTC),
            raw_payload={},
        )

        assert payload.is_valid is False


class TestStateDiff:
    """Tests for StateDiff dataclass."""

    def test_state_diff_with_differences(self):
        """Test StateDiff with actual differences."""
        diff = StateDiff(
            entity_type="deployment",
            entity_id="user-service",
            external_state={"replicas": 3, "status": "running"},
            local_state={"replicas": 2, "status": "running"},
            differences=[{"field": "replicas", "external_value": 3, "local_value": 2}],
        )

        assert diff.has_drift is True
        assert diff.drift_severity == "low"
        assert len(diff.differences) == 1

    def test_state_diff_no_differences(self):
        """Test StateDiff with no differences."""
        diff = StateDiff(
            entity_type="deployment",
            entity_id="user-service",
            external_state={"replicas": 3},
            local_state={"replicas": 3},
            differences=[],
        )

        assert diff.has_drift is False

    def test_state_diff_custom_severity(self):
        """Test StateDiff with custom severity."""
        diff = StateDiff(
            entity_type="deployment",
            entity_id="user-service",
            external_state={"status": "failed"},
            local_state={"status": "running"},
            differences=[{"field": "status", "external_value": "failed", "local_value": "running"}],
            drift_severity="critical",
        )

        assert diff.drift_severity == "critical"
