"""Tests for Service API endpoints."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.service import Service, ServiceStatus, ServiceTier
from app.db.models.team import Team
from app.db.models.template import Template
from tests.conftest import create_service_data, create_team_data, create_template_data


@pytest.fixture
async def sample_team(test_session: AsyncSession) -> Team:
    """Create a sample team for testing."""
    data = create_team_data(name="Platform Team")
    team = Team(
        id=data["id"],
        name=data["name"],
        slug=data["slug"],
        description=data["description"],
        email=data["email"],
        slack_channel=data["slack_channel"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_session.add(team)
    await test_session.commit()
    await test_session.refresh(team)
    return team


@pytest.fixture
async def sample_template(test_session: AsyncSession) -> Template:
    """Create a sample template for testing."""
    data = create_template_data(name="Python API Template")
    template = Template(
        id=data["id"],
        name=data["name"],
        slug=data["slug"],
        description=data["description"],
        version=data["version"],
        workload_type=data["workload_type"],
        language=data["language"],
        capabilities=data["capabilities"],
        ideal_for=data["ideal_for"],
        stack=data["stack"],
        includes_ci=data["includes_ci"],
        includes_cd=data["includes_cd"],
        includes_monitoring=data["includes_monitoring"],
        includes_tests=data["includes_tests"],
        is_active=data["is_active"],
        is_recommended=data["is_recommended"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_session.add(template)
    await test_session.commit()
    await test_session.refresh(template)
    return template


@pytest.fixture
async def sample_service(
    test_session: AsyncSession,
    sample_team: Team,
    sample_template: Template,
) -> Service:
    """Create a sample service for testing."""
    service = Service(
        name="user-api",
        slug="user-api",
        description="User management API",
        team_id=sample_team.id,
        template_id=sample_template.id,
        status=ServiceStatus.HEALTHY,
        tier=ServiceTier.STANDARD,
        repository_url="https://github.com/test/user-api",
        repository_branch="main",
        namespace="production",
        tags=["api", "users"],
        metadata={"env": "production"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_session.add(service)
    await test_session.commit()
    await test_session.refresh(service)
    return service


@pytest.mark.asyncio
async def test_list_services_empty(client: AsyncClient):
    """Test listing services when database is empty."""
    response = await client.get("/api/v1/services")

    assert response.status_code == 200
    data = response.json()
    assert data["services"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_services_with_data(
    client: AsyncClient,
    sample_service: Service,
):
    """Test listing services with data."""
    response = await client.get("/api/v1/services")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["services"]) == 1
    assert data["services"][0]["name"] == "user-api"


@pytest.mark.asyncio
async def test_get_service_by_id(
    client: AsyncClient,
    sample_service: Service,
):
    """Test getting a service by ID."""
    response = await client.get(f"/api/v1/services/{sample_service.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_service.id
    assert data["name"] == "user-api"
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_service_not_found(client: AsyncClient):
    """Test getting a non-existent service."""
    response = await client.get("/api/v1/services/non-existent-id")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_service(
    client: AsyncClient,
    sample_team: Team,
    sample_template: Template,
):
    """Test creating a new service."""
    service_data = create_service_data(
        name="payment-service",
        team_id=sample_team.id,
        template_id=sample_template.id,
    )

    response = await client.post("/api/v1/services", json=service_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "payment-service"
    assert data["slug"] == "payment-service"
    assert data["team_id"] == sample_team.id
    assert data["status"] == "provisioning"  # Default status for new services


@pytest.mark.asyncio
async def test_create_service_invalid_team(client: AsyncClient):
    """Test creating a service with non-existent team."""
    service_data = create_service_data(name="invalid-service")

    response = await client.post("/api/v1/services", json=service_data)

    assert response.status_code == 400
    data = response.json()
    assert "team" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_service(
    client: AsyncClient,
    sample_service: Service,
):
    """Test updating a service."""
    update_data = {
        "description": "Updated description",
        "status": "degraded",
    }

    response = await client.put(
        f"/api/v1/services/{sample_service.id}",
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["status"] == "degraded"


@pytest.mark.asyncio
async def test_delete_service(
    client: AsyncClient,
    sample_service: Service,
):
    """Test deleting a service."""
    response = await client.delete(f"/api/v1/services/{sample_service.id}")

    assert response.status_code == 204

    # Verify service is deleted
    get_response = await client.get(f"/api/v1/services/{sample_service.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_service_stats(
    client: AsyncClient,
    sample_service: Service,
):
    """Test getting service statistics."""
    response = await client.get("/api/v1/services/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_services"] == 1
    assert "by_status" in data
    assert "by_tier" in data


@pytest.mark.asyncio
async def test_filter_services_by_status(
    client: AsyncClient,
    sample_service: Service,
):
    """Test filtering services by status."""
    response = await client.get("/api/v1/services?status=healthy")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

    # Filter by different status
    response = await client.get("/api/v1/services?status=unhealthy")
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_search_services(
    client: AsyncClient,
    sample_service: Service,
):
    """Test searching services by name."""
    response = await client.get("/api/v1/services?search=user")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["services"][0]["name"] == "user-api"

    # Search with no matches
    response = await client.get("/api/v1/services?search=nonexistent")
    data = response.json()
    assert data["total"] == 0
