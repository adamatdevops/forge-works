"""Integration tests for health check endpoints.

Tests the health check endpoints without requiring a real database connection.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# =============================================================================
# Health Check Endpoint Tests
# =============================================================================


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test that health check endpoint returns healthy status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "app_name" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_check_app_name(self):
        """Test health check returns correct app name."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        data = response.json()
        assert data["app_name"] == "ForgeWorks"

    @pytest.mark.asyncio
    async def test_health_check_version_format(self):
        """Test health check returns properly formatted version."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        data = response.json()
        # Version should be a string like "0.4.0"
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0


# =============================================================================
# Detailed Health Check Endpoint Tests
# =============================================================================


class TestDetailedHealthEndpoint:
    """Tests for GET /health/detailed endpoint."""

    @pytest.mark.asyncio
    async def test_detailed_health_check(self):
        """Test that detailed health endpoint returns component status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in data

    @pytest.mark.asyncio
    async def test_detailed_health_has_database_component(self):
        """Test detailed health includes database component."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/detailed")

        data = response.json()
        assert "database" in data["components"]
        db_status = data["components"]["database"]
        # components values are status strings, not dicts
        assert db_status in ["healthy", "unhealthy", "degraded"]

    @pytest.mark.asyncio
    async def test_detailed_health_structure(self):
        """Test detailed health response structure."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/detailed")

        data = response.json()
        # Should have basic fields
        assert "status" in data
        assert "components" in data
        assert isinstance(data["components"], dict)
