"""Unit tests for WebSocket connection manager and event broadcasting.

Tests cover:
- ConnectionManager class functionality
- WebSocket event creation and serialization
- Channel subscription management
- Event broadcasting and routing
- Error handling and edge cases
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.websocket import (
    Channel,
    ConnectedClient,
    ConnectionManager,
    EventType,
    EVENT_CHANNEL_MAP,
    WebSocketEvent,
    get_manager,
)


# =============================================================================
# WebSocketEvent Tests
# =============================================================================


class TestWebSocketEvent:
    """Tests for WebSocketEvent dataclass."""

    def test_event_creation_with_defaults(self):
        """Test creating an event with default timestamp."""
        event = WebSocketEvent(
            type=EventType.SERVICE_CREATED,
            channel=Channel.SERVICES,
            data={"service_id": "svc-123"},
        )

        assert event.type == EventType.SERVICE_CREATED
        assert event.channel == Channel.SERVICES
        assert event.data == {"service_id": "svc-123"}
        assert event.timestamp is not None
        assert event.correlation_id is None

    def test_event_creation_with_correlation_id(self):
        """Test creating an event with correlation ID."""
        event = WebSocketEvent(
            type=EventType.ANOMALY_DETECTED,
            channel=Channel.ANOMALIES,
            data={"anomaly_id": "anom-456", "severity": "critical"},
            correlation_id="req-abc-123",
        )

        assert event.correlation_id == "req-abc-123"

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        timestamp = "2025-01-15T10:30:00"
        event = WebSocketEvent(
            type=EventType.PIPELINE_COMPLETED,
            channel=Channel.PIPELINES,
            data={"pipeline_id": "pipe-789", "duration_seconds": 120},
            timestamp=timestamp,
            correlation_id="corr-123",
        )

        result = event.to_dict()

        assert result["type"] == "pipeline.completed"
        assert result["channel"] == "pipelines"
        assert result["data"] == {"pipeline_id": "pipe-789", "duration_seconds": 120}
        assert result["timestamp"] == timestamp
        assert result["correlation_id"] == "corr-123"

    def test_event_to_dict_without_correlation_id(self):
        """Test event serialization without correlation ID."""
        event = WebSocketEvent(
            type=EventType.METRICS_UPDATED,
            channel=Channel.METRICS,
            data={"cpu": 45.5},
        )

        result = event.to_dict()

        assert result["correlation_id"] is None


# =============================================================================
# ConnectedClient Tests
# =============================================================================


class TestConnectedClient:
    """Tests for ConnectedClient dataclass."""

    def test_client_creation_with_defaults(self):
        """Test creating a client with default subscriptions."""
        mock_ws = MagicMock()
        client = ConnectedClient(
            websocket=mock_ws,
            client_id="test-client-1",
        )

        assert client.websocket is mock_ws
        assert client.client_id == "test-client-1"
        assert Channel.ALL in client.subscriptions
        assert client.connected_at is not None

    def test_client_creation_with_custom_subscriptions(self):
        """Test creating a client with specific subscriptions."""
        mock_ws = MagicMock()
        client = ConnectedClient(
            websocket=mock_ws,
            client_id="test-client-2",
            subscriptions={Channel.SERVICES, Channel.ANOMALIES},
        )

        assert Channel.SERVICES in client.subscriptions
        assert Channel.ANOMALIES in client.subscriptions
        assert Channel.ALL not in client.subscriptions


# =============================================================================
# ConnectionManager Tests - Basic Operations
# =============================================================================


class TestConnectionManagerBasic:
    """Tests for basic ConnectionManager operations."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self) -> AsyncMock:
        """Create a mock WebSocket."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    def test_initial_state(self, manager: ConnectionManager):
        """Test initial manager state."""
        assert manager.active_connections == 0
        assert manager.client_ids == []

    @pytest.mark.asyncio
    async def test_connect(self, manager: ConnectionManager, mock_websocket: AsyncMock):
        """Test connecting a client."""
        client = await manager.connect(mock_websocket, "client-1")

        assert manager.active_connections == 1
        assert "client-1" in manager.client_ids
        assert client.client_id == "client-1"
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_sends_confirmation(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ):
        """Test that connection sends confirmation event."""
        await manager.connect(mock_websocket, "client-1")

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "connected"
        assert call_args["channel"] == "all"
        assert call_args["data"]["client_id"] == "client-1"

    @pytest.mark.asyncio
    async def test_connect_with_initial_subscriptions(
        self, manager: ConnectionManager, mock_websocket: AsyncMock
    ):
        """Test connecting with initial subscriptions."""
        subscriptions = {Channel.SERVICES, Channel.ANOMALIES}
        client = await manager.connect(
            mock_websocket, "client-1", initial_subscriptions=subscriptions
        )

        assert Channel.SERVICES in client.subscriptions
        assert Channel.ANOMALIES in client.subscriptions

    @pytest.mark.asyncio
    async def test_disconnect(self, manager: ConnectionManager, mock_websocket: AsyncMock):
        """Test disconnecting a client."""
        await manager.connect(mock_websocket, "client-1")
        assert manager.active_connections == 1

        manager.disconnect("client-1")

        assert manager.active_connections == 0
        assert "client-1" not in manager.client_ids

    def test_disconnect_nonexistent_client(self, manager: ConnectionManager):
        """Test disconnecting a non-existent client doesn't raise."""
        # Should not raise
        manager.disconnect("nonexistent-client")
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_multiple_clients(self, manager: ConnectionManager):
        """Test connecting multiple clients."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")
        await manager.connect(ws3, "client-3")

        assert manager.active_connections == 3
        assert set(manager.client_ids) == {"client-1", "client-2", "client-3"}


# =============================================================================
# ConnectionManager Tests - Subscriptions
# =============================================================================


class TestConnectionManagerSubscriptions:
    """Tests for subscription management."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.fixture
    async def connected_client(self, manager: ConnectionManager) -> tuple[AsyncMock, str]:
        """Create a connected client."""
        ws = AsyncMock()
        await manager.connect(ws, "test-client")
        return ws, "test-client"

    @pytest.mark.asyncio
    async def test_subscribe(
        self, manager: ConnectionManager, connected_client: tuple[AsyncMock, str]
    ):
        """Test subscribing to a channel."""
        ws, client_id = connected_client

        result = await manager.subscribe(client_id, Channel.PIPELINES)

        assert result is True
        subscriptions = manager.get_client_subscriptions(client_id)
        assert Channel.PIPELINES in subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_sends_confirmation(
        self, manager: ConnectionManager, connected_client: tuple[AsyncMock, str]
    ):
        """Test that subscribe sends confirmation event."""
        ws, client_id = connected_client
        ws.send_json.reset_mock()

        await manager.subscribe(client_id, Channel.KUBERNETES)

        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "subscribed"
        assert call_args["channel"] == "kubernetes"

    @pytest.mark.asyncio
    async def test_subscribe_nonexistent_client(self, manager: ConnectionManager):
        """Test subscribing for non-existent client."""
        result = await manager.subscribe("nonexistent", Channel.SERVICES)
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe(
        self, manager: ConnectionManager, connected_client: tuple[AsyncMock, str]
    ):
        """Test unsubscribing from a channel."""
        ws, client_id = connected_client
        await manager.subscribe(client_id, Channel.SERVICES)

        result = await manager.unsubscribe(client_id, Channel.SERVICES)

        assert result is True
        subscriptions = manager.get_client_subscriptions(client_id)
        assert Channel.SERVICES not in subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe_sends_confirmation(
        self, manager: ConnectionManager, connected_client: tuple[AsyncMock, str]
    ):
        """Test that unsubscribe sends confirmation event."""
        ws, client_id = connected_client
        await manager.subscribe(client_id, Channel.TEMPLATES)
        ws.send_json.reset_mock()

        await manager.unsubscribe(client_id, Channel.TEMPLATES)

        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "unsubscribed"
        assert call_args["channel"] == "templates"

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_client(self, manager: ConnectionManager):
        """Test unsubscribing for non-existent client."""
        result = await manager.unsubscribe("nonexistent", Channel.SERVICES)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_channel_subscribers(self, manager: ConnectionManager):
        """Test getting subscribers for a channel."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, "client-1", initial_subscriptions={Channel.SERVICES})
        await manager.connect(ws2, "client-2", initial_subscriptions={Channel.SERVICES})
        await manager.connect(ws3, "client-3", initial_subscriptions={Channel.ANOMALIES})

        services_subscribers = manager.get_channel_subscribers(Channel.SERVICES)
        anomalies_subscribers = manager.get_channel_subscribers(Channel.ANOMALIES)

        assert set(services_subscribers) == {"client-1", "client-2"}
        assert set(anomalies_subscribers) == {"client-3"}

    @pytest.mark.asyncio
    async def test_all_channel_receives_all_events(self, manager: ConnectionManager):
        """Test that ALL channel subscription receives all events."""
        ws = AsyncMock()
        await manager.connect(ws, "all-client", initial_subscriptions={Channel.ALL})

        subscribers = manager.get_channel_subscribers(Channel.SERVICES)

        # Client subscribed to ALL should be in every channel's subscribers
        assert "all-client" in subscribers

    def test_get_client_subscriptions_nonexistent(self, manager: ConnectionManager):
        """Test getting subscriptions for non-existent client."""
        result = manager.get_client_subscriptions("nonexistent")
        assert result is None


# =============================================================================
# ConnectionManager Tests - Broadcasting
# =============================================================================


class TestConnectionManagerBroadcasting:
    """Tests for event broadcasting."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager: ConnectionManager):
        """Test broadcasting to all connected clients."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")

        event = WebSocketEvent(
            type=EventType.METRICS_UPDATED,
            channel=Channel.METRICS,
            data={"cpu": 50},
        )

        sent_count = await manager.broadcast(event)

        assert sent_count == 2
        # Both clients should have received the event
        assert ws1.send_json.call_count == 2  # 1 for connect, 1 for broadcast
        assert ws2.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_to_subscribed_channel(self, manager: ConnectionManager):
        """Test broadcasting only to clients subscribed to specific channel."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, "client-1", initial_subscriptions={Channel.SERVICES})
        await manager.connect(ws2, "client-2", initial_subscriptions={Channel.ANOMALIES})

        event = WebSocketEvent(
            type=EventType.SERVICE_CREATED,
            channel=Channel.SERVICES,
            data={"service_id": "svc-new"},
        )

        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()

        sent_count = await manager.broadcast(event)

        assert sent_count == 1
        assert ws1.send_json.call_count == 1  # Received
        assert ws2.send_json.call_count == 0  # Not subscribed

    @pytest.mark.asyncio
    async def test_broadcast_cleans_up_disconnected_clients(
        self, manager: ConnectionManager
    ):
        """Test that broadcast cleans up clients that fail to receive."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")

        # Set side effect AFTER connection is established
        ws2.send_json.side_effect = Exception("Connection closed")

        event = WebSocketEvent(
            type=EventType.TEMPLATE_UPDATED,
            channel=Channel.TEMPLATES,
            data={},
        )

        sent_count = await manager.broadcast(event)

        assert sent_count == 1
        assert manager.active_connections == 1
        assert "client-2" not in manager.client_ids

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, manager: ConnectionManager):
        """Test convenience method for broadcasting to channel."""
        ws = AsyncMock()
        await manager.connect(ws, "client-1")
        ws.send_json.reset_mock()

        sent_count = await manager.broadcast_to_channel(
            channel=Channel.PIPELINES,
            event_type=EventType.PIPELINE_STARTED,
            data={"pipeline_id": "pipe-123"},
            correlation_id="corr-456",
        )

        assert sent_count == 1
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "pipeline.started"
        assert call_args["channel"] == "pipelines"
        assert call_args["data"] == {"pipeline_id": "pipe-123"}
        assert call_args["correlation_id"] == "corr-456"

    @pytest.mark.asyncio
    async def test_broadcast_no_clients(self, manager: ConnectionManager):
        """Test broadcasting when no clients connected."""
        event = WebSocketEvent(
            type=EventType.SERVICE_UPDATED,
            channel=Channel.SERVICES,
            data={},
        )

        sent_count = await manager.broadcast(event)

        assert sent_count == 0


# =============================================================================
# ConnectionManager Tests - Direct Client Messaging
# =============================================================================


class TestConnectionManagerDirectMessaging:
    """Tests for sending messages to specific clients."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_send_to_client(self, manager: ConnectionManager):
        """Test sending event to specific client."""
        ws = AsyncMock()
        await manager.connect(ws, "target-client")
        ws.send_json.reset_mock()

        event = WebSocketEvent(
            type=EventType.ERROR,
            channel=Channel.ALL,
            data={"error": "Something went wrong"},
        )

        result = await manager.send_to_client("target-client", event)

        assert result is True
        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_client(self, manager: ConnectionManager):
        """Test sending to non-existent client."""
        event = WebSocketEvent(
            type=EventType.ERROR,
            channel=Channel.ALL,
            data={"error": "Something went wrong"},
        )

        result = await manager.send_to_client("nonexistent", event)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_client_handles_error(self, manager: ConnectionManager):
        """Test that send_to_client handles transmission errors."""
        ws = AsyncMock()
        await manager.connect(ws, "failing-client")

        # Set side effect AFTER connection is established
        ws.send_json.side_effect = Exception("Connection lost")

        event = WebSocketEvent(
            type=EventType.ERROR,
            channel=Channel.ALL,
            data={"error": "test"},
        )

        result = await manager.send_to_client("failing-client", event)

        assert result is False
        assert "failing-client" not in manager.client_ids


# =============================================================================
# ConnectionManager Tests - Event Hooks
# =============================================================================


class TestConnectionManagerEventHooks:
    """Tests for event hook functionality."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_add_event_hook(self, manager: ConnectionManager):
        """Test adding and calling event hooks."""
        hook_called = []

        def my_hook(event: WebSocketEvent):
            hook_called.append(event)

        manager.add_event_hook(my_hook)

        ws = AsyncMock()
        await manager.connect(ws, "client-1")

        event = WebSocketEvent(
            type=EventType.ANOMALY_DETECTED,
            channel=Channel.ANOMALIES,
            data={"severity": "high"},
        )

        await manager.broadcast(event)

        assert len(hook_called) == 1
        assert hook_called[0].type == EventType.ANOMALY_DETECTED

    @pytest.mark.asyncio
    async def test_multiple_event_hooks(self, manager: ConnectionManager):
        """Test multiple event hooks are all called."""
        calls = {"hook1": 0, "hook2": 0, "hook3": 0}

        manager.add_event_hook(lambda e: calls.update(hook1=calls["hook1"] + 1))
        manager.add_event_hook(lambda e: calls.update(hook2=calls["hook2"] + 1))
        manager.add_event_hook(lambda e: calls.update(hook3=calls["hook3"] + 1))

        ws = AsyncMock()
        await manager.connect(ws, "client-1")

        event = WebSocketEvent(
            type=EventType.DEPLOYMENT_SCALED,
            channel=Channel.KUBERNETES,
            data={},
        )

        await manager.broadcast(event)

        assert calls["hook1"] == 1
        assert calls["hook2"] == 1
        assert calls["hook3"] == 1

    @pytest.mark.asyncio
    async def test_hook_error_doesnt_break_broadcast(self, manager: ConnectionManager):
        """Test that hook errors don't break broadcasting."""

        def failing_hook(event: WebSocketEvent):
            raise Exception("Hook failed!")

        manager.add_event_hook(failing_hook)

        ws = AsyncMock()
        await manager.connect(ws, "client-1")
        ws.send_json.reset_mock()

        event = WebSocketEvent(
            type=EventType.POD_CREATED,
            channel=Channel.KUBERNETES,
            data={},
        )

        # Should not raise
        sent_count = await manager.broadcast(event)

        assert sent_count == 1
        ws.send_json.assert_called_once()


# =============================================================================
# Event Channel Map Tests
# =============================================================================


class TestEventChannelMap:
    """Tests for event to channel mapping."""

    def test_service_events_map_to_services_channel(self):
        """Test service events map correctly."""
        assert EVENT_CHANNEL_MAP[EventType.SERVICE_CREATED] == Channel.SERVICES
        assert EVENT_CHANNEL_MAP[EventType.SERVICE_UPDATED] == Channel.SERVICES
        assert EVENT_CHANNEL_MAP[EventType.SERVICE_DELETED] == Channel.SERVICES
        assert EVENT_CHANNEL_MAP[EventType.SERVICE_STATUS_CHANGED] == Channel.SERVICES

    def test_anomaly_events_map_to_anomalies_channel(self):
        """Test anomaly events map correctly."""
        assert EVENT_CHANNEL_MAP[EventType.ANOMALY_DETECTED] == Channel.ANOMALIES
        assert EVENT_CHANNEL_MAP[EventType.ANOMALY_ACKNOWLEDGED] == Channel.ANOMALIES
        assert EVENT_CHANNEL_MAP[EventType.ANOMALY_RESOLVED] == Channel.ANOMALIES

    def test_pipeline_events_map_to_pipelines_channel(self):
        """Test pipeline events map correctly."""
        assert EVENT_CHANNEL_MAP[EventType.PIPELINE_STARTED] == Channel.PIPELINES
        assert EVENT_CHANNEL_MAP[EventType.PIPELINE_COMPLETED] == Channel.PIPELINES
        assert EVENT_CHANNEL_MAP[EventType.PIPELINE_FAILED] == Channel.PIPELINES

    def test_template_events_map_to_templates_channel(self):
        """Test template events map correctly."""
        assert EVENT_CHANNEL_MAP[EventType.TEMPLATE_CREATED] == Channel.TEMPLATES
        assert EVENT_CHANNEL_MAP[EventType.TEMPLATE_UPDATED] == Channel.TEMPLATES

    def test_metrics_events_map_to_metrics_channel(self):
        """Test metrics events map correctly."""
        assert EVENT_CHANNEL_MAP[EventType.METRICS_UPDATED] == Channel.METRICS

    def test_kubernetes_events_map_to_kubernetes_channel(self):
        """Test Kubernetes events map correctly."""
        assert EVENT_CHANNEL_MAP[EventType.POD_CREATED] == Channel.KUBERNETES
        assert EVENT_CHANNEL_MAP[EventType.POD_DELETED] == Channel.KUBERNETES
        assert EVENT_CHANNEL_MAP[EventType.DEPLOYMENT_SCALED] == Channel.KUBERNETES


# =============================================================================
# Global Manager Tests
# =============================================================================


class TestGlobalManager:
    """Tests for the global manager singleton."""

    def test_get_manager_returns_same_instance(self):
        """Test that get_manager returns singleton."""
        manager1 = get_manager()
        manager2 = get_manager()

        assert manager1 is manager2

    def test_get_manager_is_connection_manager(self):
        """Test that get_manager returns ConnectionManager."""
        manager = get_manager()
        assert isinstance(manager, ConnectionManager)


# =============================================================================
# EventType and Channel Enum Tests
# =============================================================================


class TestEnums:
    """Tests for EventType and Channel enums."""

    def test_event_type_values(self):
        """Test EventType enum values."""
        assert EventType.CONNECTED.value == "connected"
        assert EventType.SERVICE_CREATED.value == "service.created"
        assert EventType.ANOMALY_DETECTED.value == "anomaly.detected"
        assert EventType.PIPELINE_COMPLETED.value == "pipeline.completed"
        assert EventType.POD_CREATED.value == "pod.created"

    def test_channel_values(self):
        """Test Channel enum values."""
        assert Channel.ALL.value == "all"
        assert Channel.SERVICES.value == "services"
        assert Channel.ANOMALIES.value == "anomalies"
        assert Channel.PIPELINES.value == "pipelines"
        assert Channel.TEMPLATES.value == "templates"
        assert Channel.METRICS.value == "metrics"
        assert Channel.KUBERNETES.value == "kubernetes"

    def test_all_event_types_are_strings(self):
        """Test all event types can be used as strings."""
        for event_type in EventType:
            assert isinstance(event_type.value, str)
            assert len(event_type.value) > 0

    def test_all_channels_are_strings(self):
        """Test all channels can be used as strings."""
        for channel in Channel:
            assert isinstance(channel.value, str)
            assert len(channel.value) > 0
