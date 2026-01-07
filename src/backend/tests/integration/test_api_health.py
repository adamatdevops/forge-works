"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test that health check endpoint returns healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "app_name" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_detailed_health_check(client: AsyncClient):
    """Test that detailed health endpoint returns component status."""
    response = await client.get("/health/detailed")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "database" in data["components"]
