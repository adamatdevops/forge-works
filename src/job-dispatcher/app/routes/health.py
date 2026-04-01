from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.adapters import registry

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/ready")
async def ready():
    adapters = registry.list_all()
    if not adapters:
        return Response(
            content='{"status":"not_ready","reason":"no_adapters"}',
            status_code=503,
            media_type="application/json",
        )
    return {"status": "ready", "adapters": adapters}


@router.get("/status")
async def status():
    adapter_status = {}
    for name in registry.list_all():
        adapter = registry.get(name)
        if adapter:
            healthy = await adapter.health_check()
            adapter_status[name] = {
                "version": adapter.version,
                "healthy": healthy,
            }
    return {
        "status": "healthy" if all(a["healthy"] for a in adapter_status.values()) else "degraded",
        "adapters": adapter_status,
    }


@router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
