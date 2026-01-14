"""Demo Event Trigger API.

This module provides endpoints to trigger test WebSocket events for demos
and development testing. Only enabled in development mode.

Usage:
    POST /api/v1/demo/trigger-event
    {
        "event_type": "service.created",
        "data": {"service_id": "test-123", "name": "Test Service"}
    }
"""

from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.events import (
    broadcast_anomaly_detected,
    broadcast_anomaly_resolved,
    broadcast_deployment_scaled,
    broadcast_pipeline_completed,
    broadcast_pipeline_failed,
    broadcast_pipeline_started,
    broadcast_pod_created,
    broadcast_pod_deleted,
    broadcast_service_created,
    broadcast_service_deleted,
    broadcast_service_status_changed,
    broadcast_service_updated,
)

router = APIRouter()


class DemoEventType(str, Enum):
    """Available demo event types."""

    SERVICE_CREATED = "service.created"
    SERVICE_UPDATED = "service.updated"
    SERVICE_DELETED = "service.deleted"
    SERVICE_STATUS_CHANGED = "service.status_changed"
    ANOMALY_DETECTED = "anomaly.detected"
    ANOMALY_RESOLVED = "anomaly.resolved"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    POD_CREATED = "pod.created"
    POD_DELETED = "pod.deleted"
    DEPLOYMENT_SCALED = "deployment.scaled"


class TriggerEventRequest(BaseModel):
    """Request body for triggering a demo event."""

    event_type: DemoEventType = Field(
        ...,
        description="Type of event to trigger",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Optional custom data for the event. If not provided, sample data will be used.",
    )


class TriggerEventResponse(BaseModel):
    """Response from triggering a demo event."""

    success: bool
    event_type: str
    clients_notified: int
    message: str


def _get_sample_data(event_type: DemoEventType) -> dict[str, Any]:
    """Generate sample data for each event type."""
    event_id = str(uuid4())[:8]

    samples: dict[DemoEventType, dict[str, Any]] = {
        DemoEventType.SERVICE_CREATED: {
            "id": f"svc-demo-{event_id}",
            "name": f"Demo Service {event_id}",
            "status": "healthy",
            "team_id": "platform-team",
            "template_id": "microservice-python",
        },
        DemoEventType.SERVICE_UPDATED: {
            "id": f"svc-demo-{event_id}",
            "name": f"Demo Service {event_id}",
            "status": "degraded",
            "changes": {"status": {"old": "healthy", "new": "degraded"}},
        },
        DemoEventType.SERVICE_DELETED: {
            "service_id": f"svc-demo-{event_id}",
            "name": f"Demo Service {event_id}",
        },
        DemoEventType.SERVICE_STATUS_CHANGED: {
            "service_id": f"svc-demo-{event_id}",
            "old_status": "healthy",
            "new_status": "degraded",
        },
        DemoEventType.ANOMALY_DETECTED: {
            "id": f"ano-demo-{event_id}",
            "title": f"Demo Anomaly {event_id}",
            "severity": "warning",
            "service_id": f"svc-demo-{event_id}",
            "type": "latency_spike",
            "description": "Response latency exceeded threshold",
            "detected_value": "850ms",
            "expected_value": "<500ms",
        },
        DemoEventType.ANOMALY_RESOLVED: {
            "anomaly_id": f"ano-demo-{event_id}",
            "resolved_by": "demo-user",
            "resolution": "Auto-resolved after metrics normalized",
        },
        DemoEventType.PIPELINE_STARTED: {
            "id": f"pipe-demo-{event_id}",
            "service_id": f"svc-demo-{event_id}",
            "commit_sha": "abc123def",
            "branch": "main",
            "author": "demo-user",
        },
        DemoEventType.PIPELINE_COMPLETED: {
            "pipeline_id": f"pipe-demo-{event_id}",
            "status": "success",
            "duration_seconds": 245,
        },
        DemoEventType.PIPELINE_FAILED: {
            "pipeline_id": f"pipe-demo-{event_id}",
            "error": "Test compilation failed: missing dependency",
        },
        DemoEventType.POD_CREATED: {
            "name": f"demo-app-{event_id}",
            "namespace": "demo",
            "phase": "Running",
            "node_name": "demo-node-1",
        },
        DemoEventType.POD_DELETED: {
            "pod_name": f"demo-app-{event_id}",
            "namespace": "demo",
        },
        DemoEventType.DEPLOYMENT_SCALED: {
            "deployment_name": f"demo-deployment-{event_id}",
            "replicas": 5,
            "namespace": "demo",
        },
    }

    return samples.get(event_type, {})


async def _trigger_event(event_type: DemoEventType, data: dict[str, Any]) -> int:
    """Trigger the appropriate event broadcast."""
    event_handlers = {
        DemoEventType.SERVICE_CREATED: lambda d: broadcast_service_created(d),
        DemoEventType.SERVICE_UPDATED: lambda d: broadcast_service_updated(
            d, d.get("changes")
        ),
        DemoEventType.SERVICE_DELETED: lambda d: broadcast_service_deleted(
            d["service_id"], d.get("name")
        ),
        DemoEventType.SERVICE_STATUS_CHANGED: lambda d: broadcast_service_status_changed(
            d["service_id"], d["old_status"], d["new_status"]
        ),
        DemoEventType.ANOMALY_DETECTED: lambda d: broadcast_anomaly_detected(d),
        DemoEventType.ANOMALY_RESOLVED: lambda d: broadcast_anomaly_resolved(
            d["anomaly_id"], d.get("resolved_by"), d.get("resolution")
        ),
        DemoEventType.PIPELINE_STARTED: lambda d: broadcast_pipeline_started(d),
        DemoEventType.PIPELINE_COMPLETED: lambda d: broadcast_pipeline_completed(
            d["pipeline_id"], d["status"], d.get("duration_seconds")
        ),
        DemoEventType.PIPELINE_FAILED: lambda d: broadcast_pipeline_failed(
            d["pipeline_id"], d.get("error")
        ),
        DemoEventType.POD_CREATED: lambda d: broadcast_pod_created(d),
        DemoEventType.POD_DELETED: lambda d: broadcast_pod_deleted(
            d["pod_name"], d.get("namespace")
        ),
        DemoEventType.DEPLOYMENT_SCALED: lambda d: broadcast_deployment_scaled(
            d["deployment_name"], d["replicas"], d.get("namespace")
        ),
    }

    handler = event_handlers.get(event_type)
    if handler:
        return await handler(data)
    return 0


@router.post(
    "/trigger-event",
    response_model=TriggerEventResponse,
    summary="Trigger a demo WebSocket event",
    description="Trigger a test event for development and demo purposes. Only available in development mode.",
)
async def trigger_demo_event(request: TriggerEventRequest) -> TriggerEventResponse:
    """Trigger a demo WebSocket event.

    This endpoint allows triggering test events to verify WebSocket
    functionality and demonstrate real-time updates.

    Only available in development mode.
    """
    # Check if we're in development mode
    if settings.environment not in ("development", "dev", "local") and not settings.debug:
        raise HTTPException(
            status_code=403,
            detail="Demo events are only available in development mode",
        )

    # Get data (use sample if not provided)
    event_data = request.data or _get_sample_data(request.event_type)

    # Trigger the event
    clients_notified = await _trigger_event(request.event_type, event_data)

    return TriggerEventResponse(
        success=True,
        event_type=request.event_type.value,
        clients_notified=clients_notified,
        message=f"Event '{request.event_type.value}' triggered successfully",
    )


@router.get(
    "/event-types",
    summary="List available demo event types",
    description="Get a list of all available event types that can be triggered for demos.",
)
async def list_event_types() -> dict[str, Any]:
    """List all available demo event types with descriptions."""
    return {
        "event_types": [
            {
                "type": event_type.value,
                "name": event_type.name,
                "sample_data": _get_sample_data(event_type),
            }
            for event_type in DemoEventType
        ],
        "usage": {
            "endpoint": "POST /api/v1/demo/trigger-event",
            "body": {
                "event_type": "<event_type>",
                "data": "<optional custom data>",
            },
        },
    }


@router.get(
    "/status",
    summary="Demo API status",
    description="Check if demo mode is enabled and get WebSocket connection stats.",
)
async def demo_status() -> dict[str, Any]:
    """Get demo API status and WebSocket stats."""
    from app.core.websocket import Channel, get_manager

    manager = get_manager()
    is_enabled = settings.environment in ("development", "dev", "local") or settings.debug

    return {
        "demo_mode_enabled": is_enabled,
        "environment": settings.environment,
        "websocket_stats": {
            "active_connections": manager.active_connections,
            "client_ids": manager.client_ids,
            "channels": {
                channel.value: len(manager.get_channel_subscribers(channel))
                for channel in Channel
            },
        },
        "available_event_types": len(DemoEventType),
    }
