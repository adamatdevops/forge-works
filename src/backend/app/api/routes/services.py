"""Service catalog endpoints."""

from fastapi import APIRouter

router = APIRouter()


# TODO: Implement service catalog endpoints
# - GET /services - List all services
# - GET /services/{id} - Get service details
# - POST /services - Create new service
# - PUT /services/{id} - Update service
# - DELETE /services/{id} - Delete service


@router.get("")
async def list_services() -> dict:
    """List all services in the catalog."""
    # TODO: Implement with database
    return {"services": [], "total": 0, "message": "Service catalog - Coming soon"}


@router.get("/{service_id}")
async def get_service(service_id: str) -> dict:
    """Get service details by ID."""
    # TODO: Implement with database
    return {"service_id": service_id, "message": "Service details - Coming soon"}
