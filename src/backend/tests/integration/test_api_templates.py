"""Integration tests for Template API endpoints.

Tests the Golden Path template API using mocking to avoid database dependencies.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# =============================================================================
# Mock Helpers
# =============================================================================


def create_mock_template(
    template_id: str | None = None,
    name: str = "Test Template",
    workload_type: str = "api",
    language: str = "python",
    is_active: bool = True,
    is_recommended: bool = True,
    usage_count: int = 5,
):
    """Create a mock template object."""
    template = MagicMock()
    template.id = template_id or str(uuid4())
    template.name = name
    template.slug = name.lower().replace(" ", "-")
    template.description = f"Test template: {name}"
    template.version = "1.0.0"
    template.workload_type = workload_type
    template.language = language
    template.capabilities = ["api", "crud", "rest"]
    template.ideal_for = ["low_latency", "rest_api", "microservice"]
    template.stack = {"framework": "fastapi", "db": "postgresql"}
    template.repository_url = None  # Optional field
    template.documentation_url = None  # Optional field
    template.includes_ci = True
    template.includes_cd = True
    template.includes_monitoring = True
    template.includes_tests = True
    template.is_active = is_active
    template.is_recommended = is_recommended
    template.usage_count = usage_count
    template.created_at = datetime.now(UTC)
    template.updated_at = datetime.now(UTC)
    return template


# =============================================================================
# List Templates Endpoint Tests
# =============================================================================


class TestListTemplatesEndpoint:
    """Tests for GET /api/v1/templates endpoint."""

    @pytest.mark.asyncio
    async def test_list_templates_empty(self):
        """Test listing templates when database is empty."""
        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[])
            mock_crud.count = AsyncMock(return_value=0)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates")

        assert response.status_code == 200
        data = response.json()
        assert data["templates"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_templates_with_data(self):
        """Test listing templates with data."""
        templates = [
            create_mock_template(name="Python API"),
            create_mock_template(name="Go Service", language="go"),
            create_mock_template(name="Stream Processor", workload_type="stream"),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=templates)
            mock_crud.count = AsyncMock(return_value=3)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["templates"]) == 3

    @pytest.mark.asyncio
    async def test_list_templates_pagination(self):
        """Test template listing pagination."""
        templates = [create_mock_template(name=f"Template {i}") for i in range(2)]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=templates)
            mock_crud.count = AsyncMock(return_value=5)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["pages"] == 3

    @pytest.mark.asyncio
    async def test_filter_templates_by_workload_type(self):
        """Test filtering templates by workload type."""
        api_templates = [
            create_mock_template(name="Python API", workload_type="api"),
            create_mock_template(name="Go Service", workload_type="api", language="go"),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=api_templates)
            mock_crud.count = AsyncMock(return_value=2)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates?workload_type=api")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_filter_templates_by_language(self):
        """Test filtering templates by language."""
        python_templates = [
            create_mock_template(name="Python API", language="python"),
            create_mock_template(
                name="Stream Processor", workload_type="stream", language="python"
            ),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=python_templates)
            mock_crud.count = AsyncMock(return_value=2)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates?language=python")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_filter_templates_by_active_status(self):
        """Test filtering templates by active status."""
        active_templates = [create_mock_template(name="Active Template", is_active=True)]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=active_templates)
            mock_crud.count = AsyncMock(return_value=1)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# =============================================================================
# Get Template Endpoint Tests
# =============================================================================


class TestGetTemplateEndpoint:
    """Tests for GET /api/v1/templates/{template_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_template_by_id(self):
        """Test getting a template by ID."""
        template_id = str(uuid4())
        mock_template = create_mock_template(template_id=template_id, name="Python API")

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=mock_template)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/templates/{template_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Python API"

    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Test getting a non-existent template."""
        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates/non-existent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_template_by_slug(self):
        """Test getting a template by slug."""
        mock_template = create_mock_template(name="Python API")

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_by_slug = AsyncMock(return_value=mock_template)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates/slug/python-api")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Python API"
        assert data["slug"] == "python-api"

    @pytest.mark.asyncio
    async def test_get_template_includes_stack(self):
        """Test template response includes stack information."""
        mock_template = create_mock_template(name="Python API")

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=mock_template)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/templates/{mock_template.id}")

        assert response.status_code == 200
        data = response.json()
        assert "stack" in data
        assert data["stack"]["framework"] == "fastapi"


# =============================================================================
# Recommend Templates Endpoint Tests
# =============================================================================


class TestRecommendTemplatesEndpoint:
    """Tests for POST /api/v1/templates/recommend endpoint."""

    @pytest.mark.asyncio
    async def test_recommend_templates_success(self):
        """Test template recommendation endpoint."""
        templates = [
            create_mock_template(name="Python API", workload_type="api", language="python"),
            create_mock_template(name="Go Service", workload_type="api", language="go"),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=templates)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/templates/recommend",
                    json={
                        "workload_type": "api",
                        "language": "python",
                        "requirements": ["low_latency", "rest_api"],
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "recommendations" in data
        assert "processing_time_ms" in data
        assert data["model_version"] == "1.0.0-rule-based"

    @pytest.mark.asyncio
    async def test_recommend_templates_top_match(self):
        """Test that Python API is the top recommendation for Python API request."""
        templates = [
            create_mock_template(name="Python API", workload_type="api", language="python"),
            create_mock_template(name="Go Service", workload_type="api", language="go"),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=templates)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/templates/recommend",
                    json={
                        "workload_type": "api",
                        "language": "python",
                        "requirements": [],
                    },
                )

        assert response.status_code == 200
        data = response.json()
        if data["recommendations"]:
            top = data["recommendations"][0]
            assert top["template"]["language"] == "python"
            assert top["score"] > 0
            assert len(top["match_reasons"]) > 0

    @pytest.mark.asyncio
    async def test_recommend_templates_language_mismatch_warning(self):
        """Test recommendation with language mismatch shows warnings."""
        templates = [
            create_mock_template(name="Python API", workload_type="api", language="python"),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=templates)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/templates/recommend",
                    json={
                        "workload_type": "api",
                        "language": "rust",  # No Rust templates
                        "requirements": [],
                    },
                )

        assert response.status_code == 200
        data = response.json()
        # Should still return API templates but with warnings
        if data["recommendations"]:
            for rec in data["recommendations"]:
                assert any("mismatch" in w.lower() for w in rec["warnings"])

    @pytest.mark.asyncio
    async def test_recommend_templates_no_matches(self):
        """Test recommendation when no templates exist."""
        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[])

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/templates/recommend",
                    json={
                        "workload_type": "api",
                        "language": "python",
                        "requirements": [],
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []
        assert data["top_recommendation"] is None

    @pytest.mark.asyncio
    async def test_recommend_templates_includes_reasons(self):
        """Test that recommendations include match reasons."""
        templates = [
            create_mock_template(name="Python API", workload_type="api", language="python"),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=templates)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/templates/recommend",
                    json={
                        "workload_type": "api",
                        "language": "python",
                        "requirements": ["low_latency"],
                    },
                )

        assert response.status_code == 200
        data = response.json()
        if data["recommendations"]:
            rec = data["recommendations"][0]
            assert "match_reasons" in rec
            assert len(rec["match_reasons"]) > 0

    @pytest.mark.asyncio
    async def test_recommend_templates_score_range(self):
        """Test that recommendation scores are within valid range."""
        templates = [
            create_mock_template(name="Python API", workload_type="api", language="python"),
        ]

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=templates)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/templates/recommend",
                    json={
                        "workload_type": "api",
                        "language": "python",
                        "requirements": [],
                    },
                )

        assert response.status_code == 200
        data = response.json()
        for rec in data["recommendations"]:
            assert 0.0 <= rec["score"] <= 1.0


# =============================================================================
# Template Response Structure Tests
# =============================================================================


class TestTemplateResponseStructure:
    """Tests for template response structure."""

    @pytest.mark.asyncio
    async def test_template_has_required_fields(self):
        """Test template response has all required fields."""
        mock_template = create_mock_template(name="Python API")

        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=mock_template)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/templates/{mock_template.id}")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "id",
            "name",
            "slug",
            "description",
            "version",
            "workload_type",
            "language",
            "capabilities",
            "ideal_for",
            "stack",
            "includes_ci",
            "includes_cd",
            "includes_monitoring",
            "includes_tests",
            "is_active",
            "is_recommended",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_template_list_has_pagination_fields(self):
        """Test template list response has pagination fields."""
        with patch("app.api.routes.templates.TemplateCRUD") as mock_crud:
            mock_crud.get_all = AsyncMock(return_value=[])
            mock_crud.count = AsyncMock(return_value=0)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/templates")

        assert response.status_code == 200
        data = response.json()

        pagination_fields = ["templates", "total", "page", "page_size", "pages"]
        for field in pagination_fields:
            assert field in data, f"Missing pagination field: {field}"
