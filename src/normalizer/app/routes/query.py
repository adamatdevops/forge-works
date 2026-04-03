"""
Config Query API — GET /config/{resource_ref}

Returns the current normalized config for a resource.
Used by Pattern Matcher (via HTTP) and dashboard.
"""

from fastapi import APIRouter
from starlette.responses import JSONResponse

from app import store

router = APIRouter(prefix="/config")


@router.get("/{resource_ref:path}")
async def get_config(resource_ref: str):
    """Get normalized config by resource_ref (e.g., kubernetes:default/my-pod)."""
    config = await store.get(resource_ref)
    if not config:
        return JSONResponse(
            {"error": "not_found", "resource_ref": resource_ref},
            status_code=404,
        )
    return config.model_dump()
