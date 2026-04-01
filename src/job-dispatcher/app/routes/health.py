import json

from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.adapters import registry

router = APIRouter()

# Will be set by main.py after dispatcher is created
_dispatcher = None


def set_dispatcher(dispatcher):
    global _dispatcher
    _dispatcher = dispatcher


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/ready")
async def ready():
    """Readiness: checks adapter health, Kafka consumer/producer, and dispatch loop."""
    # Check adapters
    adapters = registry.list_all()
    if not adapters:
        return Response(
            content='{"status":"not_ready","reason":"no_adapters"}',
            status_code=503,
            media_type="application/json",
        )

    adapter_health = {}
    for name in adapters:
        adapter = registry.get(name)
        if adapter:
            adapter_health[name] = await adapter.health_check()

    # Check Kafka / dispatcher
    dispatcher_health = _dispatcher.is_healthy() if _dispatcher else {"healthy": False}

    all_ok = (
        all(adapter_health.values())
        and dispatcher_health.get("healthy", False)
    )

    result = {
        "status": "ready" if all_ok else "not_ready",
        "adapters": adapter_health,
        "dispatcher": dispatcher_health,
    }

    if not all_ok:
        return Response(
            content=json.dumps(result),
            status_code=503,
            media_type="application/json",
        )
    return result


@router.get("/status")
async def status():
    adapter_status = {}
    for name in registry.list_all():
        adapter = registry.get(name)
        if adapter:
            healthy = await adapter.health_check()
            adapter_status[name] = {"version": adapter.version, "healthy": healthy}

    dispatcher_health = _dispatcher.is_healthy() if _dispatcher else {}

    return {
        "status": "healthy" if all(a["healthy"] for a in adapter_status.values()) else "degraded",
        "adapters": adapter_status,
        "dispatcher": dispatcher_health,
    }


@router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
