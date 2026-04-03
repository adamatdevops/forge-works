import hmac
import json

from fastapi import APIRouter, Header
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app import store
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/ready")
async def ready():
    if store._redis is None:
        return Response(
            content='{"status":"not_ready","reason":"redis_not_connected"}',
            status_code=503,
            media_type="application/json",
        )
    return {"status": "ready"}


@router.get("/status")
async def status(x_forgeworks_internal: str | None = Header(None)):
    """Internal diagnostics — requires B5 HMAC token."""
    expected = settings.internal_api_token
    if not expected or not x_forgeworks_internal or not hmac.compare_digest(x_forgeworks_internal, expected):
        return Response(
            content='{"error":"forbidden","message":"Internal endpoint"}',
            status_code=403,
            media_type="application/json",
        )

    refs = await store.list_refs()
    return {
        "status": "healthy",
        "cached_configs": len(refs),
        "resource_refs": refs[:20],
    }


@router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
