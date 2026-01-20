"""Base Forge adapter interface for bidirectional tool integrations.

Forges extend the basic adapter pattern to enable true collaboration
between DevOps tools, not just one-way integration.

Key Differences from BaseAdapter:
- Adapters: Read (pull) + Write (push) operations
- Forges: Read + Write + Listen (webhooks) + Reconcile (sync)

Architecture:
    ┌─────────────────┐                    ┌─────────────────┐
    │   External Tool │                    │   ForgeWorks    │
    │  (GitHub, K8s)  │                    │    Database     │
    └────────┬────────┘                    └────────┬────────┘
             │                                      │
             │ ◄──── LISTEN (webhooks) ────        │
             │                                      │
             │ ────► FETCH (read state) ──────►    │
             │                                      │
             │ ◄──── PUSH (write state) ◄─────     │
             │                                      │
             │ ◄───► RECONCILE (sync) ◄────►       │
             │                                      │
    ┌────────┴────────┐                    ┌────────┴────────┐
    │    Forge        │◄────────────────────│   Events       │
    │  (Bridge Layer) │─────────────────────►   (WebSocket)   │
    └─────────────────┘                    └─────────────────┘
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.adapters.base import AdapterHealth, AdapterMode, BaseAdapter


class ForgeMode(str, Enum):
    """Forge operation mode."""

    MOCK = "mock"  # Simulate external events for development
    LIVE = "live"  # Connect to real external tools
    PASSIVE = "passive"  # Read-only, no webhooks


class ReconciliationStrategy(str, Enum):
    """How to handle state conflicts between external and local."""

    EXTERNAL_WINS = "external_wins"  # External tool is source of truth
    LOCAL_WINS = "local_wins"  # ForgeWorks is source of truth
    MERGE = "merge"  # Attempt to merge changes
    ALERT = "alert"  # Don't auto-resolve, create anomaly


@dataclass
class ForgeConfig:
    """Configuration for a Forge adapter."""

    mode: ForgeMode = ForgeMode.MOCK
    reconciliation_strategy: ReconciliationStrategy = ReconciliationStrategy.EXTERNAL_WINS
    reconcile_interval_seconds: int = 60  # How often to sync
    webhook_secret: str | None = None  # For validating incoming webhooks
    enable_mock_events: bool = True  # Generate mock events in mock mode
    mock_event_interval_seconds: int = 30  # How often to generate mock events


@dataclass
class ForgeHealth(AdapterHealth):
    """Extended health status for Forge adapters."""

    webhook_active: bool = False
    last_webhook_received: datetime | None = None
    last_reconciliation: datetime | None = None
    pending_events: int = 0
    state_drift_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        base = super().to_dict()
        base.update(
            {
                "webhook_active": self.webhook_active,
                "last_webhook_received": (
                    self.last_webhook_received.isoformat() if self.last_webhook_received else None
                ),
                "last_reconciliation": (
                    self.last_reconciliation.isoformat() if self.last_reconciliation else None
                ),
                "pending_events": self.pending_events,
                "state_drift_detected": self.state_drift_detected,
            }
        )
        return base


@dataclass
class WebhookPayload:
    """Standardized webhook payload from external tools."""

    source: str  # github, argocd, kubernetes
    event_type: str  # pr.opened, deployment.synced, pod.crashed
    timestamp: datetime
    raw_payload: dict[str, Any]
    signature: str | None = None  # For validation
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if payload has required fields."""
        return bool(self.source and self.event_type and self.raw_payload)


@dataclass
class StateDiff:
    """Represents differences between external and local state."""

    entity_type: str  # service, deployment, pod, pr
    entity_id: str
    external_state: dict[str, Any]
    local_state: dict[str, Any]
    differences: list[dict[str, Any]]  # List of field differences
    drift_severity: str = "low"  # low, medium, high, critical

    @property
    def has_drift(self) -> bool:
        """Check if there are any differences."""
        return len(self.differences) > 0


class ForgeAdapter(BaseAdapter, ABC):
    """Abstract base class for bidirectional Forge adapters.

    Forges extend adapters with:
    1. LISTEN: Receive webhooks/events from external tools
    2. RECONCILE: Sync state between external and local
    3. BRIDGE: Connect tools that can't communicate directly

    Example Usage:
        forge = GitHubKubernetesForge(config)

        # Start listening for webhooks
        await forge.start_webhook_listener()

        # Periodic reconciliation
        async def reconcile_loop():
            while True:
                await forge.reconcile()
                await asyncio.sleep(forge.config.reconcile_interval_seconds)

        # Handle incoming webhook
        @app.post("/webhooks/github")
        async def github_webhook(payload: dict):
            await forge.on_webhook(WebhookPayload(
                source="github",
                event_type=payload["action"],
                timestamp=datetime.now(UTC),
                raw_payload=payload,
            ))
    """

    def __init__(self, config: ForgeConfig | None = None) -> None:
        """Initialize Forge with configuration."""
        self.config = config or ForgeConfig()
        super().__init__(mode=AdapterMode(self.config.mode.value))

        self._webhook_handlers: dict[str, list[Callable]] = {}
        self._last_reconciliation: datetime | None = None
        self._last_webhook: datetime | None = None
        self._event_queue: list[WebhookPayload] = []
        self._state_cache: dict[str, Any] = {}
        self._drift_alerts: list[StateDiff] = []

    # =========================================================================
    # Abstract Methods - Must be implemented by concrete Forges
    # =========================================================================

    @property
    @abstractmethod
    def forge_name(self) -> str:
        """Return the forge name (e.g., 'github-kubernetes-bridge')."""
        ...

    @property
    @abstractmethod
    def supported_webhook_events(self) -> list[str]:
        """Return list of webhook event types this forge handles."""
        ...

    @abstractmethod
    async def fetch_external_state(self) -> dict[str, Any]:
        """Fetch current state from external tool(s).

        Returns a dictionary representing the current state of the
        external resources this forge manages.
        """
        ...

    @abstractmethod
    async def get_local_state(self) -> dict[str, Any]:
        """Get the current local state from ForgeWorks database.

        Returns a dictionary representing what ForgeWorks believes
        the state should be.
        """
        ...

    @abstractmethod
    async def apply_external_state(self, diff: StateDiff) -> bool:
        """Apply external state changes to local database.

        Called when external_wins reconciliation determines
        ForgeWorks needs to update its state.
        """
        ...

    @abstractmethod
    async def push_local_state(self, diff: StateDiff) -> bool:
        """Push local state changes to external tool.

        Called when local_wins reconciliation determines
        the external tool needs to be updated.
        """
        ...

    @abstractmethod
    async def handle_webhook_event(self, payload: WebhookPayload) -> None:
        """Process an incoming webhook event.

        Concrete forges implement this to handle specific
        event types from their external tools.
        """
        ...

    @abstractmethod
    async def generate_mock_events(self) -> list[WebhookPayload]:
        """Generate realistic mock events for testing/demos.

        Called periodically in mock mode to simulate
        external tool activity.
        """
        ...

    # =========================================================================
    # Base Implementation - Webhook Handling
    # =========================================================================

    def register_webhook_handler(
        self,
        event_type: str,
        handler: Callable[[WebhookPayload], None],
    ) -> None:
        """Register a handler for a specific webhook event type."""
        if event_type not in self._webhook_handlers:
            self._webhook_handlers[event_type] = []
        self._webhook_handlers[event_type].append(handler)

    async def on_webhook(self, payload: WebhookPayload) -> None:
        """Process an incoming webhook.

        Validates the payload, routes to appropriate handlers,
        and queues events for processing.
        """
        if not payload.is_valid:
            raise ValueError(f"Invalid webhook payload: {payload}")

        # Validate signature if configured
        if self.config.webhook_secret and payload.signature:
            if not self._validate_signature(payload):
                raise ValueError("Invalid webhook signature")

        self._last_webhook = datetime.now(UTC)
        self._event_queue.append(payload)

        # Call registered handlers
        handlers = self._webhook_handlers.get(payload.event_type, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:
                # Log but don't fail - webhook handling should be resilient
                print(f"Webhook handler error: {e}")

        # Call the concrete forge's handler
        await self.handle_webhook_event(payload)

    def _validate_signature(self, payload: WebhookPayload) -> bool:
        """Validate webhook signature.

        Override in concrete forges for tool-specific validation.
        """
        # Default: accept if no secret configured
        if not self.config.webhook_secret:
            return True

        # Concrete forges should implement proper validation
        return True

    # =========================================================================
    # Base Implementation - Reconciliation
    # =========================================================================

    async def reconcile(self) -> list[StateDiff]:
        """Reconcile state between external tool and ForgeWorks.

        Compares external and local state, identifies differences,
        and applies changes according to the reconciliation strategy.

        Returns list of differences that were found and handled.
        """
        external_state = await self.fetch_external_state()
        local_state = await self.get_local_state()

        diffs = self._compute_state_diff(external_state, local_state)
        self._drift_alerts = [d for d in diffs if d.has_drift]
        self._last_reconciliation = datetime.now(UTC)

        for diff in diffs:
            if not diff.has_drift:
                continue

            match self.config.reconciliation_strategy:
                case ReconciliationStrategy.EXTERNAL_WINS:
                    await self.apply_external_state(diff)
                case ReconciliationStrategy.LOCAL_WINS:
                    await self.push_local_state(diff)
                case ReconciliationStrategy.MERGE:
                    await self._merge_states(diff)
                case ReconciliationStrategy.ALERT:
                    await self._create_drift_alert(diff)

        return diffs

    def _compute_state_diff(
        self,
        external: dict[str, Any],
        local: dict[str, Any],
    ) -> list[StateDiff]:
        """Compute differences between external and local state.

        Override for custom diff logic in concrete forges.
        """
        diffs = []

        # Compare by entity type and ID
        for entity_type in set(external.keys()) | set(local.keys()):
            ext_entities = external.get(entity_type, {})
            local_entities = local.get(entity_type, {})

            for entity_id in set(ext_entities.keys()) | set(local_entities.keys()):
                ext_state = ext_entities.get(entity_id, {})
                local_state = local_entities.get(entity_id, {})

                differences = self._find_field_differences(ext_state, local_state)

                if differences:
                    severity = self._calculate_drift_severity(differences)
                    diffs.append(
                        StateDiff(
                            entity_type=entity_type,
                            entity_id=entity_id,
                            external_state=ext_state,
                            local_state=local_state,
                            differences=differences,
                            drift_severity=severity,
                        )
                    )

        return diffs

    def _find_field_differences(
        self,
        external: dict[str, Any],
        local: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Find field-level differences between states."""
        differences = []
        all_keys = set(external.keys()) | set(local.keys())

        for key in all_keys:
            ext_val = external.get(key)
            local_val = local.get(key)

            if ext_val != local_val:
                differences.append(
                    {
                        "field": key,
                        "external_value": ext_val,
                        "local_value": local_val,
                    }
                )

        return differences

    def _calculate_drift_severity(
        self,
        differences: list[dict[str, Any]],
    ) -> str:
        """Calculate severity of state drift.

        Override for custom severity logic.
        """
        critical_fields = {"status", "health", "state", "replicas"}
        high_fields = {"sync_status", "deployment_status", "build_status"}

        for diff in differences:
            field = diff.get("field", "")
            if field in critical_fields:
                return "critical"
            if field in high_fields:
                return "high"

        if len(differences) > 5:
            return "medium"

        return "low"

    async def _merge_states(self, diff: StateDiff) -> None:
        """Merge external and local states.

        Default implementation: external wins for most fields,
        local wins for ForgeWorks-specific fields.
        """
        # Override in concrete forges for custom merge logic
        await self.apply_external_state(diff)

    async def _create_drift_alert(self, diff: StateDiff) -> None:
        """Create an anomaly alert for state drift.

        Override to integrate with ForgeWorks anomaly system.
        """
        # Import here to avoid circular dependencies
        from app.core.events import broadcast_anomaly_detected

        await broadcast_anomaly_detected(
            {
                "type": "state_drift",
                "forge": self.forge_name,
                "entity_type": diff.entity_type,
                "entity_id": diff.entity_id,
                "severity": diff.drift_severity,
                "differences": diff.differences,
                "detected_at": datetime.now(UTC).isoformat(),
            }
        )

    # =========================================================================
    # Base Implementation - Health Check
    # =========================================================================

    async def health_check(self) -> ForgeHealth:
        """Check forge health including webhook and reconciliation status."""
        # Perform base adapter health check
        try:
            # Check if we can fetch state
            await self.fetch_external_state()
            healthy = True
            error = None
            latency = 50.0  # TODO: Measure actual latency
        except Exception as e:
            healthy = False
            error = str(e)
            latency = None

        return ForgeHealth(
            name=self.forge_name,
            healthy=healthy,
            mode=self.mode,
            latency_ms=latency,
            last_check=datetime.now(UTC),
            error=error,
            webhook_active=self._last_webhook is not None,
            last_webhook_received=self._last_webhook,
            last_reconciliation=self._last_reconciliation,
            pending_events=len(self._event_queue),
            state_drift_detected=len(self._drift_alerts) > 0,
        )

    # =========================================================================
    # Base Implementation - Mock Mode
    # =========================================================================

    async def simulate_activity(self) -> None:
        """Generate and process mock events for development/demos.

        Called periodically in mock mode to simulate
        realistic external tool activity.
        """
        if not self.config.enable_mock_events:
            return

        if not self.is_mock():
            return

        mock_events = await self.generate_mock_events()
        for event in mock_events:
            await self.on_webhook(event)

    # =========================================================================
    # Compatibility with BaseAdapter
    # =========================================================================

    @property
    def name(self) -> str:
        """Return adapter name for BaseAdapter compatibility."""
        return self.forge_name
