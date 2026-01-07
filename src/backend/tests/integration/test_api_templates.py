"""Tests for Template API endpoints."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.template import Template
from tests.conftest import create_template_data


@pytest.fixture
async def sample_templates(test_session: AsyncSession) -> list[Template]:
    """Create multiple sample templates for testing."""
    templates_data = [
        create_template_data(
            name="Python API",
            workload_type="api",
            language="python",
        ),
        create_template_data(
            name="Go Service",
            workload_type="api",
            language="go",
        ),
        create_template_data(
            name="Stream Processor",
            workload_type="stream",
            language="python",
        ),
    ]

    templates = []
    for data in templates_data:
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_session.add(template)
        templates.append(template)

    await test_session.commit()
    for t in templates:
        await test_session.refresh(t)

    return templates


@pytest.mark.asyncio
async def test_list_templates_empty(client: AsyncClient):
    """Test listing templates when database is empty."""
    response = await client.get("/api/v1/templates")

    assert response.status_code == 200
    data = response.json()
    assert data["templates"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_templates_with_data(
    client: AsyncClient,
    sample_templates: list[Template],
):
    """Test listing templates with data."""
    response = await client.get("/api/v1/templates")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["templates"]) == 3


@pytest.mark.asyncio
async def test_filter_templates_by_workload_type(
    client: AsyncClient,
    sample_templates: list[Template],
):
    """Test filtering templates by workload type."""
    response = await client.get("/api/v1/templates?workload_type=api")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # Python API and Go Service

    response = await client.get("/api/v1/templates?workload_type=stream")
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_filter_templates_by_language(
    client: AsyncClient,
    sample_templates: list[Template],
):
    """Test filtering templates by language."""
    response = await client.get("/api/v1/templates?language=python")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # Python API and Stream Processor


@pytest.mark.asyncio
async def test_get_template_by_id(
    client: AsyncClient,
    sample_templates: list[Template],
):
    """Test getting a template by ID."""
    template = sample_templates[0]
    response = await client.get(f"/api/v1/templates/{template.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template.id
    assert data["name"] == template.name


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient):
    """Test getting a non-existent template."""
    response = await client.get("/api/v1/templates/non-existent-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recommend_templates(
    client: AsyncClient,
    sample_templates: list[Template],
):
    """Test template recommendation endpoint."""
    request_data = {
        "workload_type": "api",
        "language": "python",
        "requirements": ["low_latency", "rest_api"],
    }

    response = await client.post("/api/v1/templates/recommend", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "recommendations" in data
    assert "processing_time_ms" in data
    assert data["model_version"] == "1.0.0-rule-based"

    # Python API should be the top recommendation
    if data["recommendations"]:
        top = data["recommendations"][0]
        assert top["template"]["language"] == "python"
        assert top["score"] > 0
        assert len(top["match_reasons"]) > 0


@pytest.mark.asyncio
async def test_recommend_templates_language_mismatch(
    client: AsyncClient,
    sample_templates: list[Template],
):
    """Test recommendation with language mismatch shows warnings."""
    request_data = {
        "workload_type": "api",
        "language": "rust",  # No Rust templates exist
        "requirements": [],
    }

    response = await client.post("/api/v1/templates/recommend", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Should still return API templates but with warnings
    if data["recommendations"]:
        for rec in data["recommendations"]:
            assert any("mismatch" in w.lower() for w in rec["warnings"])


@pytest.mark.asyncio
async def test_recommend_templates_no_matches(client: AsyncClient):
    """Test recommendation when no templates exist."""
    request_data = {
        "workload_type": "api",
        "language": "python",
        "requirements": [],
    }

    response = await client.post("/api/v1/templates/recommend", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"] == []
    assert data["top_recommendation"] is None
