"""Integration tests for Service API endpoints.

Tests the service catalog API using mocking to avoid database dependencies.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.models.service import ServiceStatus, ServiceTier
from app.main import app


# =============================================================================
# Mock Helpers
# =============================================================================


def create_mock_service(
    service_id: str | None = None,
    name: str = "test-service",
    status: ServiceStatus = ServiceStatus.HEALTHY,
    tier: ServiceTier = ServiceTier.STANDARD,
    team_id: str | None = None,
    template_id: str | None = None,
):
    """Create a mock service object."""
    service = MagicMock()
    service.id = service_id or str(uuid4())
    service.name = name
    service.slug = name.lower().replace(" ", "-")
    service.description = f"Test service: {name}"
    service.team_id = team_id or str(uuid4())
    service.template_id = template_id
    service.status = status
    service.tier = tier
    service.repository_url = "https://github.com/test/test-service"
    service.repository_branch = "main"
    service.namespace = "production"
    service.argocd_app_name = None  # Optional field
    service.tags = ["test", "api"]
    service.extra_metadata = {"env": "test"}  # Note: uses alias extra_metadata
    service.deploys_today = 2
    service.rollbacks_this_week = 0
    service.last_deploy_at = None  # Optional field
    service.documentation_url = None  # Optional field
    service.dashboard_url = None  # Optional field
    service.runbook_url = None  # Optional field
    service.created_at = datetime.now(UTC)
    service.updated_at = datetime.now(UTC)
    # Related objects
    service.team = None
    service.template = None
    service.anomalies = []
    return service


def create_mock_team(team_id: str | None = None, name: str = "Platform Team"):
    """Create a mock team object."""
    team = MagicMock()
    team.id = team_id or str(uuid4())
    team.name = name
    team.slug = name.lower().replace(" ", "-")
    return team


# =============================================================================
# List Services Endpoint Tests
# =============================================================================


class TestListServicesEndpoint:
    """Tests for GET /api/v1/services endpoint."""

    @pytest.mark.asyncio
    async def test_list_services_empty(self):
        """Test listing services when database is empty."""
        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[])
            mock_crud.count = AsyncMock(return_value=0)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services")

        assert response.status_code == 200
        data = response.json()
        assert data["services"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_services_with_data(self):
        """Test listing services with data."""
        mock_service = create_mock_service(name="user-api")

        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[mock_service])
            mock_crud.count = AsyncMock(return_value=1)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["services"]) == 1
        assert data["services"][0]["name"] == "user-api"

    @pytest.mark.asyncio
    async def test_list_services_pagination(self):
        """Test service listing pagination."""
        services = [create_mock_service(name=f"service-{i}") for i in range(5)]

        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=services[:2])
            mock_crud.count = AsyncMock(return_value=5)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["pages"] == 3

    @pytest.mark.asyncio
    async def test_filter_services_by_status(self):
        """Test filtering services by status."""
        mock_service = create_mock_service(name="user-api", status=ServiceStatus.HEALTHY)

        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[mock_service])
            mock_crud.count = AsyncMock(return_value=1)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services?status=healthy")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_filter_services_by_status_no_matches(self):
        """Test filtering services by status with no matches."""
        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[])
            mock_crud.count = AsyncMock(return_value=0)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services?status=unhealthy")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_search_services(self):
        """Test searching services by name."""
        mock_service = create_mock_service(name="user-api")

        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[mock_service])
            mock_crud.count = AsyncMock(return_value=1)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services?search=user")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["services"][0]["name"] == "user-api"

    @pytest.mark.asyncio
    async def test_search_services_no_matches(self):
        """Test searching services with no matches."""
        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[])
            mock_crud.count = AsyncMock(return_value=0)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services?search=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


# =============================================================================
# Get Service Endpoint Tests
# =============================================================================


class TestGetServiceEndpoint:
    """Tests for GET /api/v1/services/{service_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_service_by_id(self):
        """Test getting a service by ID."""
        service_id = str(uuid4())
        mock_service = create_mock_service(service_id=service_id, name="user-api")

        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=mock_service)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/services/{service_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == service_id
        assert data["name"] == "user-api"
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_service_not_found(self):
        """Test getting a non-existent service."""
        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services/non-existent-id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_service_by_slug(self):
        """Test getting a service by slug."""
        mock_service = create_mock_service(name="user-api")

        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_by_slug = AsyncMock(return_value=mock_service)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services/slug/user-api")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "user-api"
        assert data["slug"] == "user-api"


# =============================================================================
# Create Service Endpoint Tests
# =============================================================================


class TestCreateServiceEndpoint:
    """Tests for POST /api/v1/services endpoint."""

    @pytest.mark.asyncio
    async def test_create_service_success(self):
        """Test creating a new service."""
        team_id = str(uuid4())
        template_id = str(uuid4())
        mock_service = create_mock_service(
            name="payment-service",
            team_id=team_id,
            template_id=template_id,
            status=ServiceStatus.PROVISIONING,
        )
        mock_template = MagicMock()
        mock_template.usage_count = 0

        with (
            patch("app.api.routes.services.ServiceCRUD") as mock_service_crud,
            patch("app.api.routes.services.TeamCRUD") as mock_team_crud,
            patch("app.api.routes.services.TemplateCRUD") as mock_template_crud,
            patch("app.api.routes.services.broadcast_service_created", new_callable=AsyncMock),
        ):
            mock_team_crud.exists = AsyncMock(return_value=True)
            mock_template_crud.exists = AsyncMock(return_value=True)
            mock_template_crud.get_by_id = AsyncMock(return_value=mock_template)
            mock_template_crud.increment_usage = AsyncMock()
            mock_service_crud.get_by_slug = AsyncMock(return_value=None)
            mock_service_crud.create = AsyncMock(return_value=mock_service)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/services",
                    json={
                        "name": "payment-service",
                        "description": "Payment processing service",
                        "team_id": team_id,
                        "template_id": template_id,
                        "tier": "standard",
                    },
                )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "payment-service"
        assert data["status"] == "provisioning"

    @pytest.mark.asyncio
    async def test_create_service_invalid_team(self):
        """Test creating a service with non-existent team."""
        with (
            patch("app.api.routes.services.TeamCRUD") as mock_team_crud,
        ):
            mock_team_crud.exists = AsyncMock(return_value=False)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/services",
                    json={
                        "name": "invalid-service",
                        "description": "Test",
                        "team_id": str(uuid4()),
                        "tier": "standard",
                    },
                )

        assert response.status_code == 400
        data = response.json()
        assert "team" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_service_duplicate_name(self):
        """Test creating a service with duplicate name."""
        team_id = str(uuid4())
        existing_service = create_mock_service(name="existing-service")

        with (
            patch("app.api.routes.services.ServiceCRUD") as mock_service_crud,
            patch("app.api.routes.services.TeamCRUD") as mock_team_crud,
        ):
            mock_team_crud.exists = AsyncMock(return_value=True)
            mock_service_crud.get_by_slug = AsyncMock(return_value=existing_service)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/services",
                    json={
                        "name": "existing-service",
                        "description": "Test",
                        "team_id": team_id,
                        "tier": "standard",
                    },
                )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()


# =============================================================================
# Update Service Endpoint Tests
# =============================================================================


class TestUpdateServiceEndpoint:
    """Tests for PUT /api/v1/services/{service_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_service_success(self):
        """Test updating a service."""
        service_id = str(uuid4())
        mock_service = create_mock_service(service_id=service_id, name="user-api")
        updated_service = create_mock_service(
            service_id=service_id,
            name="user-api",
            status=ServiceStatus.DEGRADED,
        )
        updated_service.description = "Updated description"

        with (
            patch("app.api.routes.services.ServiceCRUD") as mock_crud,
            patch("app.api.routes.services.broadcast_service_updated", new_callable=AsyncMock),
        ):
            mock_crud.get_by_id = AsyncMock(return_value=mock_service)
            mock_crud.update = AsyncMock(return_value=updated_service)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/services/{service_id}",
                    json={
                        "description": "Updated description",
                        "status": "degraded",
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_update_service_not_found(self):
        """Test updating a non-existent service."""
        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/services/{str(uuid4())}",
                    json={"description": "Updated"},
                )

        assert response.status_code == 404


# =============================================================================
# Delete Service Endpoint Tests
# =============================================================================


class TestDeleteServiceEndpoint:
    """Tests for DELETE /api/v1/services/{service_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_service_success(self):
        """Test deleting a service."""
        service_id = str(uuid4())
        mock_service = create_mock_service(service_id=service_id, name="user-api")

        with (
            patch("app.api.routes.services.ServiceCRUD") as mock_crud,
            patch("app.api.routes.services.broadcast_service_deleted", new_callable=AsyncMock),
        ):
            mock_crud.get_by_id = AsyncMock(return_value=mock_service)
            mock_crud.delete = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(f"/api/v1/services/{service_id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_service_not_found(self):
        """Test deleting a non-existent service."""
        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(f"/api/v1/services/{str(uuid4())}")

        assert response.status_code == 404


# =============================================================================
# Service Stats Endpoint Tests
# =============================================================================


class TestServiceStatsEndpoint:
    """Tests for GET /api/v1/services/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_service_stats(self):
        """Test getting service statistics."""
        mock_stats = {
            "total_services": 10,
            "by_status": {"healthy": 8, "degraded": 1, "unhealthy": 1},
            "by_tier": {"critical": 2, "standard": 6, "experimental": 2},
            "active_anomalies": 3,
            "deploys_today": 15,
            "rollbacks_this_week": 2,
        }

        with patch("app.api.routes.services.ServiceCRUD") as mock_crud:
            mock_crud.get_stats = AsyncMock(return_value=mock_stats)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/services/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_services"] == 10
        assert "by_status" in data
        assert "by_tier" in data
