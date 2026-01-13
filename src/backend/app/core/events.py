"""Event broadcasting helpers for real-time updates.

This module provides convenient functions to broadcast events when
data changes occur in the application. It integrates with the
ConnectionManager to send events to subscribed clients.

Usage:
    from app.core.events import broadcast_service_created

    # After creating a service
    await broadcast_service_created(service)

    # Or use the generic broadcast function
    await broadcast_event(EventType.SERVICE_UPDATED, Channel.SERVICES, data)
"""

from typing import Any

from app.core.websocket import (
    Channel,
    EventType,
    WebSocketEvent,
    get_manager,
)


async def broadcast_event(
    event_type: EventType,
    channel: Channel,
    data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """
    Broadcast a generic event to subscribed clients.

    Args:
        event_type: Type of event
        channel: Target channel
        data: Event payload
        correlation_id: Optional correlation ID

    Returns:
        Number of clients that received the event
    """
    manager = get_manager()
    event = WebSocketEvent(
        type=event_type,
        channel=channel,
        data=data,
        correlation_id=correlation_id,
    )
    return await manager.broadcast(event)


# ============================================================================
# Service Events
# ============================================================================


async def broadcast_service_created(
    service_data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast service created event."""
    return await broadcast_event(
        EventType.SERVICE_CREATED,
        Channel.SERVICES,
        {"service": service_data, "action": "created"},
        correlation_id,
    )


async def broadcast_service_updated(
    service_data: dict[str, Any],
    changes: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast service updated event."""
    return await broadcast_event(
        EventType.SERVICE_UPDATED,
        Channel.SERVICES,
        {"service": service_data, "changes": changes or {}, "action": "updated"},
        correlation_id,
    )


async def broadcast_service_deleted(
    service_id: str,
    service_name: str | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast service deleted event."""
    return await broadcast_event(
        EventType.SERVICE_DELETED,
        Channel.SERVICES,
        {"service_id": service_id, "name": service_name, "action": "deleted"},
        correlation_id,
    )


async def broadcast_service_status_changed(
    service_id: str,
    old_status: str,
    new_status: str,
    correlation_id: str | None = None,
) -> int:
    """Broadcast service status change event."""
    return await broadcast_event(
        EventType.SERVICE_STATUS_CHANGED,
        Channel.SERVICES,
        {
            "service_id": service_id,
            "old_status": old_status,
            "new_status": new_status,
            "action": "status_changed",
        },
        correlation_id,
    )


# ============================================================================
# Anomaly Events
# ============================================================================


async def broadcast_anomaly_detected(
    anomaly_data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast anomaly detected event."""
    return await broadcast_event(
        EventType.ANOMALY_DETECTED,
        Channel.ANOMALIES,
        {"anomaly": anomaly_data, "action": "detected"},
        correlation_id,
    )


async def broadcast_anomaly_acknowledged(
    anomaly_id: str,
    acknowledged_by: str | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast anomaly acknowledged event."""
    return await broadcast_event(
        EventType.ANOMALY_ACKNOWLEDGED,
        Channel.ANOMALIES,
        {
            "anomaly_id": anomaly_id,
            "acknowledged_by": acknowledged_by,
            "action": "acknowledged",
        },
        correlation_id,
    )


async def broadcast_anomaly_resolved(
    anomaly_id: str,
    resolved_by: str | None = None,
    resolution: str | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast anomaly resolved event."""
    return await broadcast_event(
        EventType.ANOMALY_RESOLVED,
        Channel.ANOMALIES,
        {
            "anomaly_id": anomaly_id,
            "resolved_by": resolved_by,
            "resolution": resolution,
            "action": "resolved",
        },
        correlation_id,
    )


# ============================================================================
# Pipeline Events
# ============================================================================


async def broadcast_pipeline_started(
    pipeline_data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast pipeline started event."""
    return await broadcast_event(
        EventType.PIPELINE_STARTED,
        Channel.PIPELINES,
        {"pipeline": pipeline_data, "action": "started"},
        correlation_id,
    )


async def broadcast_pipeline_completed(
    pipeline_id: str,
    status: str,
    duration_seconds: float | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast pipeline completed event."""
    return await broadcast_event(
        EventType.PIPELINE_COMPLETED,
        Channel.PIPELINES,
        {
            "pipeline_id": pipeline_id,
            "status": status,
            "duration_seconds": duration_seconds,
            "action": "completed",
        },
        correlation_id,
    )


async def broadcast_pipeline_failed(
    pipeline_id: str,
    error: str | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast pipeline failed event."""
    return await broadcast_event(
        EventType.PIPELINE_FAILED,
        Channel.PIPELINES,
        {"pipeline_id": pipeline_id, "error": error, "action": "failed"},
        correlation_id,
    )


# ============================================================================
# Template Events
# ============================================================================


async def broadcast_template_created(
    template_data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast template created event."""
    return await broadcast_event(
        EventType.TEMPLATE_CREATED,
        Channel.TEMPLATES,
        {"template": template_data, "action": "created"},
        correlation_id,
    )


async def broadcast_template_updated(
    template_data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast template updated event."""
    return await broadcast_event(
        EventType.TEMPLATE_UPDATED,
        Channel.TEMPLATES,
        {"template": template_data, "action": "updated"},
        correlation_id,
    )


# ============================================================================
# Metrics Events
# ============================================================================


async def broadcast_metrics_updated(
    metrics_data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast metrics updated event."""
    return await broadcast_event(
        EventType.METRICS_UPDATED,
        Channel.METRICS,
        {"metrics": metrics_data, "action": "updated"},
        correlation_id,
    )


# ============================================================================
# Kubernetes Events (Phase 4.2)
# ============================================================================


async def broadcast_pod_created(
    pod_data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast pod created event."""
    return await broadcast_event(
        EventType.POD_CREATED,
        Channel.KUBERNETES,
        {"pod": pod_data, "action": "created"},
        correlation_id,
    )


async def broadcast_pod_deleted(
    pod_name: str,
    namespace: str | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast pod deleted event."""
    return await broadcast_event(
        EventType.POD_DELETED,
        Channel.KUBERNETES,
        {"pod_name": pod_name, "namespace": namespace, "action": "deleted"},
        correlation_id,
    )


async def broadcast_deployment_scaled(
    deployment_name: str,
    replicas: int,
    namespace: str | None = None,
    correlation_id: str | None = None,
) -> int:
    """Broadcast deployment scaled event."""
    return await broadcast_event(
        EventType.DEPLOYMENT_SCALED,
        Channel.KUBERNETES,
        {
            "deployment_name": deployment_name,
            "replicas": replicas,
            "namespace": namespace,
            "action": "scaled",
        },
        correlation_id,
    )


async def broadcast_kubernetes_event(
    event_type: str,
    data: dict[str, Any],
    correlation_id: str | None = None,
) -> int:
    """Broadcast a generic Kubernetes event.

    Use this for custom Kubernetes events not covered by specific functions.
    """
    # Map string event types to EventType enum if possible
    type_map = {
        "pod.created": EventType.POD_CREATED,
        "pod.deleted": EventType.POD_DELETED,
        "deployment.scaled": EventType.DEPLOYMENT_SCALED,
    }

    event_enum = type_map.get(event_type)
    if event_enum:
        return await broadcast_event(
            event_enum,
            Channel.KUBERNETES,
            data,
            correlation_id,
        )

    # For unknown event types, still broadcast to Kubernetes channel
    # Use a generic approach (this is a fallback)
    manager = get_manager()
    event = WebSocketEvent(
        type=EventType.METRICS_UPDATED,  # Fallback type
        channel=Channel.KUBERNETES,
        data={"custom_type": event_type, **data},
        correlation_id=correlation_id,
    )
    return await manager.broadcast(event)
