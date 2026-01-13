"""WebSocket endpoint for real-time updates.

This module provides the WebSocket endpoint that clients connect to
for receiving real-time updates about services, anomalies, pipelines, etc.

Usage:
    Connect to: ws://localhost:8000/ws
    Or with client ID: ws://localhost:8000/ws?client_id=my-client

Message Format (incoming):
    {
        "action": "subscribe" | "unsubscribe",
        "channel": "services" | "anomalies" | "pipelines" | "templates" | "metrics"
    }

Message Format (outgoing):
    {
        "type": "service.created" | "anomaly.detected" | etc.,
        "channel": "services" | "anomalies" | etc.,
        "data": { ... },
        "timestamp": "2025-01-13T10:00:00.000Z",
        "correlation_id": "optional-id"
    }
"""

import uuid
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.websocket import Channel, EventType, WebSocketEvent, get_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str | None = Query(None, description="Optional client identifier"),
) -> None:
    """
    WebSocket endpoint for real-time updates.

    Clients connect to this endpoint to receive real-time updates about
    platform events (services, anomalies, pipelines, etc.).

    Query Parameters:
        client_id: Optional unique identifier for this client.
                   If not provided, a UUID will be generated.

    Actions:
        subscribe: Subscribe to a channel
        unsubscribe: Unsubscribe from a channel
        ping: Keepalive ping (responds with pong)

    Example connection:
        ws://localhost:8000/ws?client_id=dashboard-1
    """
    manager = get_manager()

    # Generate client ID if not provided
    if not client_id:
        client_id = f"client-{uuid.uuid4().hex[:8]}"

    # Connect with default subscription to ALL channel
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            await handle_client_message(client_id, data)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        # Send error event before disconnecting
        try:
            await manager.send_to_client(
                client_id,
                WebSocketEvent(
                    type=EventType.ERROR,
                    channel=Channel.ALL,
                    data={"error": str(e), "message": "Connection error"},
                ),
            )
        except Exception:
            pass
        manager.disconnect(client_id)


async def handle_client_message(client_id: str, data: dict[str, Any]) -> None:
    """
    Handle incoming messages from WebSocket clients.

    Args:
        client_id: The client sending the message
        data: The message data

    Supported actions:
        - subscribe: Subscribe to a channel
        - unsubscribe: Unsubscribe from a channel
        - ping: Keepalive ping
    """
    manager = get_manager()
    action = data.get("action", "").lower()

    if action == "subscribe":
        channel_name = data.get("channel", "").lower()
        try:
            channel = Channel(channel_name)
            await manager.subscribe(client_id, channel)
        except ValueError:
            await manager.send_to_client(
                client_id,
                WebSocketEvent(
                    type=EventType.ERROR,
                    channel=Channel.ALL,
                    data={
                        "error": f"Unknown channel: {channel_name}",
                        "valid_channels": [c.value for c in Channel],
                    },
                ),
            )

    elif action == "unsubscribe":
        channel_name = data.get("channel", "").lower()
        try:
            channel = Channel(channel_name)
            await manager.unsubscribe(client_id, channel)
        except ValueError:
            await manager.send_to_client(
                client_id,
                WebSocketEvent(
                    type=EventType.ERROR,
                    channel=Channel.ALL,
                    data={
                        "error": f"Unknown channel: {channel_name}",
                        "valid_channels": [c.value for c in Channel],
                    },
                ),
            )

    elif action == "ping":
        # Respond with pong for keepalive
        await manager.send_to_client(
            client_id,
            WebSocketEvent(
                type=EventType.CONNECTED,
                channel=Channel.ALL,
                data={"pong": True},
            ),
        )

    else:
        # Unknown action
        await manager.send_to_client(
            client_id,
            WebSocketEvent(
                type=EventType.ERROR,
                channel=Channel.ALL,
                data={
                    "error": f"Unknown action: {action}",
                    "valid_actions": ["subscribe", "unsubscribe", "ping"],
                },
            ),
        )


@router.get("/ws/status")
async def websocket_status() -> dict[str, Any]:
    """
    Get WebSocket server status.

    Returns information about active connections and channels.
    Useful for debugging and monitoring.
    """
    manager = get_manager()

    # Count subscribers per channel
    channel_stats = {}
    for channel in Channel:
        subscribers = manager.get_channel_subscribers(channel)
        channel_stats[channel.value] = len(subscribers)

    return {
        "active_connections": manager.active_connections,
        "client_ids": manager.client_ids,
        "channels": channel_stats,
        "status": "healthy" if manager.active_connections >= 0 else "degraded",
    }
