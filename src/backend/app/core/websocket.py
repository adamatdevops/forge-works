"""WebSocket connection manager and event broadcasting.

This module implements the WebSocket infrastructure for real-time updates
in the ForgeWorks dashboard. It uses a pub/sub pattern with typed events.

Architecture:
- ConnectionManager: Handles WebSocket connections and broadcasts
- Event Types: Typed events for different data updates
- Channels: Logical groupings for event routing

Event Flow:
1. Client connects to /ws endpoint
2. Client subscribes to channels (services, anomalies, pipelines, etc.)
3. Backend broadcasts events when data changes
4. Client receives events and updates UI in real-time
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import WebSocket


class EventType(str, Enum):
    """WebSocket event types for real-time updates."""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    ERROR = "error"

    # Service events
    SERVICE_CREATED = "service.created"
    SERVICE_UPDATED = "service.updated"
    SERVICE_DELETED = "service.deleted"
    SERVICE_STATUS_CHANGED = "service.status_changed"

    # Anomaly events
    ANOMALY_DETECTED = "anomaly.detected"
    ANOMALY_ACKNOWLEDGED = "anomaly.acknowledged"
    ANOMALY_RESOLVED = "anomaly.resolved"

    # Pipeline events
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"

    # Template events
    TEMPLATE_CREATED = "template.created"
    TEMPLATE_UPDATED = "template.updated"

    # Metrics events
    METRICS_UPDATED = "metrics.updated"

    # Kubernetes events (Phase 4.2)
    POD_CREATED = "pod.created"
    POD_DELETED = "pod.deleted"
    DEPLOYMENT_SCALED = "deployment.scaled"

    # Forge events (bidirectional bridges)
    FORGE_WEBHOOK_RECEIVED = "forge.webhook_received"
    FORGE_CORRELATION_CREATED = "forge.correlation_created"
    FORGE_CORRELATION_UPDATED = "forge.correlation_updated"
    FORGE_STATE_DRIFT = "forge.state_drift"
    BUILD_TO_DEPLOY_STARTED = "forge.build_to_deploy.started"
    BUILD_TO_DEPLOY_COMPLETED = "forge.build_to_deploy.completed"
    BUILD_TO_DEPLOY_FAILED = "forge.build_to_deploy.failed"


class Channel(str, Enum):
    """WebSocket channels for event routing."""

    ALL = "all"  # Receives all events
    SERVICES = "services"
    ANOMALIES = "anomalies"
    PIPELINES = "pipelines"
    TEMPLATES = "templates"
    METRICS = "metrics"
    KUBERNETES = "kubernetes"
    FORGES = "forges"  # Bidirectional bridge events


# Map event types to their primary channel
EVENT_CHANNEL_MAP: dict[EventType, Channel] = {
    EventType.SERVICE_CREATED: Channel.SERVICES,
    EventType.SERVICE_UPDATED: Channel.SERVICES,
    EventType.SERVICE_DELETED: Channel.SERVICES,
    EventType.SERVICE_STATUS_CHANGED: Channel.SERVICES,
    EventType.ANOMALY_DETECTED: Channel.ANOMALIES,
    EventType.ANOMALY_ACKNOWLEDGED: Channel.ANOMALIES,
    EventType.ANOMALY_RESOLVED: Channel.ANOMALIES,
    EventType.PIPELINE_STARTED: Channel.PIPELINES,
    EventType.PIPELINE_COMPLETED: Channel.PIPELINES,
    EventType.PIPELINE_FAILED: Channel.PIPELINES,
    EventType.TEMPLATE_CREATED: Channel.TEMPLATES,
    EventType.TEMPLATE_UPDATED: Channel.TEMPLATES,
    EventType.METRICS_UPDATED: Channel.METRICS,
    EventType.POD_CREATED: Channel.KUBERNETES,
    EventType.POD_DELETED: Channel.KUBERNETES,
    EventType.DEPLOYMENT_SCALED: Channel.KUBERNETES,
    # Forge events
    EventType.FORGE_WEBHOOK_RECEIVED: Channel.FORGES,
    EventType.FORGE_CORRELATION_CREATED: Channel.FORGES,
    EventType.FORGE_CORRELATION_UPDATED: Channel.FORGES,
    EventType.FORGE_STATE_DRIFT: Channel.FORGES,
    EventType.BUILD_TO_DEPLOY_STARTED: Channel.FORGES,
    EventType.BUILD_TO_DEPLOY_COMPLETED: Channel.FORGES,
    EventType.BUILD_TO_DEPLOY_FAILED: Channel.FORGES,
}


@dataclass
class WebSocketEvent:
    """Structured WebSocket event for transmission."""

    type: EventType
    channel: Channel
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "channel": self.channel.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }


@dataclass
class ConnectedClient:
    """Represents a connected WebSocket client."""

    websocket: WebSocket
    client_id: str
    subscriptions: set[Channel] = field(default_factory=lambda: {Channel.ALL})
    connected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ConnectionManager:
    """
    Manages WebSocket connections and event broadcasting.

    Features:
    - Connection pooling with unique client IDs
    - Channel-based subscriptions
    - Broadcast to all or specific channels
    - Automatic cleanup on disconnect

    Usage:
        manager = ConnectionManager()

        # In WebSocket endpoint
        await manager.connect(websocket, client_id)
        await manager.subscribe(client_id, Channel.SERVICES)
        await manager.broadcast(event)
        manager.disconnect(client_id)
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._clients: dict[str, ConnectedClient] = {}
        self._event_hooks: list[Callable[[WebSocketEvent], None]] = []

    @property
    def active_connections(self) -> int:
        """Return the number of active connections."""
        return len(self._clients)

    @property
    def client_ids(self) -> list[str]:
        """Return list of connected client IDs."""
        return list(self._clients.keys())

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        initial_subscriptions: set[Channel] | None = None,
    ) -> ConnectedClient:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The FastAPI WebSocket instance
            client_id: Unique identifier for this client
            initial_subscriptions: Channels to subscribe to on connect

        Returns:
            ConnectedClient instance
        """
        await websocket.accept()

        subscriptions = initial_subscriptions or {Channel.ALL}
        client = ConnectedClient(
            websocket=websocket,
            client_id=client_id,
            subscriptions=subscriptions,
        )
        self._clients[client_id] = client

        # Send connection confirmation
        await self._send_to_client(
            client,
            WebSocketEvent(
                type=EventType.CONNECTED,
                channel=Channel.ALL,
                data={
                    "client_id": client_id,
                    "subscriptions": [s.value for s in subscriptions],
                    "message": "Connected to ForgeWorks real-time updates",
                },
            ),
        )

        return client

    def disconnect(self, client_id: str) -> None:
        """
        Remove a client from the connection pool.

        Args:
            client_id: The client to disconnect
        """
        if client_id in self._clients:
            del self._clients[client_id]

    async def subscribe(self, client_id: str, channel: Channel) -> bool:
        """
        Subscribe a client to a channel.

        Args:
            client_id: The client to subscribe
            channel: The channel to subscribe to

        Returns:
            True if subscription successful, False if client not found
        """
        if client_id not in self._clients:
            return False

        client = self._clients[client_id]
        client.subscriptions.add(channel)

        await self._send_to_client(
            client,
            WebSocketEvent(
                type=EventType.SUBSCRIBED,
                channel=channel,
                data={
                    "channel": channel.value,
                    "subscriptions": [s.value for s in client.subscriptions],
                },
            ),
        )

        return True

    async def unsubscribe(self, client_id: str, channel: Channel) -> bool:
        """
        Unsubscribe a client from a channel.

        Args:
            client_id: The client to unsubscribe
            channel: The channel to unsubscribe from

        Returns:
            True if unsubscription successful, False if client not found
        """
        if client_id not in self._clients:
            return False

        client = self._clients[client_id]
        client.subscriptions.discard(channel)

        await self._send_to_client(
            client,
            WebSocketEvent(
                type=EventType.UNSUBSCRIBED,
                channel=channel,
                data={
                    "channel": channel.value,
                    "subscriptions": [s.value for s in client.subscriptions],
                },
            ),
        )

        return True

    async def broadcast(self, event: WebSocketEvent) -> int:
        """
        Broadcast an event to all subscribed clients.

        Args:
            event: The event to broadcast

        Returns:
            Number of clients that received the event
        """
        sent_count = 0
        disconnected: list[str] = []

        for client_id, client in self._clients.items():
            # Check if client is subscribed to this channel or ALL
            if Channel.ALL in client.subscriptions or event.channel in client.subscriptions:
                try:
                    await self._send_to_client(client, event)
                    sent_count += 1
                except Exception:
                    # Client disconnected, mark for removal
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

        # Call event hooks
        for hook in self._event_hooks:
            try:
                hook(event)
            except Exception:
                pass  # Don't let hooks break broadcasting

        return sent_count

    async def broadcast_to_channel(
        self,
        channel: Channel,
        event_type: EventType,
        data: dict[str, Any],
        correlation_id: str | None = None,
    ) -> int:
        """
        Convenience method to broadcast an event to a specific channel.

        Args:
            channel: Target channel
            event_type: Type of event
            data: Event payload
            correlation_id: Optional correlation ID for tracing

        Returns:
            Number of clients that received the event
        """
        event = WebSocketEvent(
            type=event_type,
            channel=channel,
            data=data,
            correlation_id=correlation_id,
        )
        return await self.broadcast(event)

    async def send_to_client(
        self,
        client_id: str,
        event: WebSocketEvent,
    ) -> bool:
        """
        Send an event to a specific client.

        Args:
            client_id: Target client ID
            event: The event to send

        Returns:
            True if sent successfully, False if client not found
        """
        if client_id not in self._clients:
            return False

        client = self._clients[client_id]
        try:
            await self._send_to_client(client, event)
            return True
        except Exception:
            self.disconnect(client_id)
            return False

    async def _send_to_client(
        self,
        client: ConnectedClient,
        event: WebSocketEvent,
    ) -> None:
        """Internal method to send an event to a client."""
        await client.websocket.send_json(event.to_dict())

    def add_event_hook(self, hook: Callable[[WebSocketEvent], None]) -> None:
        """
        Add a hook to be called on every broadcast event.

        Useful for logging, metrics, or side effects.

        Args:
            hook: Callable that receives the event
        """
        self._event_hooks.append(hook)

    def get_channel_subscribers(self, channel: Channel) -> list[str]:
        """
        Get list of client IDs subscribed to a channel.

        Args:
            channel: The channel to check

        Returns:
            List of client IDs
        """
        return [
            client_id
            for client_id, client in self._clients.items()
            if channel in client.subscriptions or Channel.ALL in client.subscriptions
        ]

    def get_client_subscriptions(self, client_id: str) -> set[Channel] | None:
        """
        Get the subscriptions for a specific client.

        Args:
            client_id: The client to check

        Returns:
            Set of channels or None if client not found
        """
        if client_id not in self._clients:
            return None
        return self._clients[client_id].subscriptions


# Global connection manager instance
manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
